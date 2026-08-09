from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from duels.models import DuelRoom, Submission
from .serializers import DuelRoomSerializer, SubmissionSerializer, MatchDetailSerializer
from duels.judge import judge_submissions
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from users.models import User
from achievements.models import Achievement
from notifications.services import send_notification, send_achievement_unlocked_email, send_duel_judged_email
from core.permissions import IsDuelParticipant
import random
import string
import time
import threading
import logging

logger = logging.getLogger(__name__)

_room_cache = {}
_CACHE_TTL = 5

def get_channel_layer_instance():
    return get_channel_layer()

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_cached_room(code):
    now = time.time()
    cached = _room_cache.get(code)
    if cached and now - cached['time'] < _CACHE_TTL:
        return cached['room']
    room = DuelRoom.objects.select_related('creator', 'opponent').get(code=code)
    _room_cache[code] = {'room': room, 'time': now}
    return room

def invalidate_room_cache(code):
    _room_cache.pop(code, None)

def award_achievements(user):
    conditions = []
    if user.wins >= 1:
        conditions.append('first_win')
    if user.wins >= 10:
        conditions.append('ten_wins')
    if user.total_duels >= 100:
        conditions.append('hundred_duels')

    achievements = Achievement.objects.filter(condition__in=conditions)
    for achievement in achievements:
        if not user.achievements.filter(pk=achievement.pk).exists():
            user.achievements.add(achievement)
            send_achievement_unlocked_email(user, achievement.name)

class CreateDuelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        language = request.data.get('language', 'python')
        difficulty = request.data.get('difficulty', 'easy')
        buggy_code = request.data.get('buggy_code', '')
        duration = request.data.get('duration', 180)

        if duration not in (60, 180, 300):
            return Response({'error': 'Duration must be 60, 180, or 300 seconds'}, status=status.HTTP_400_BAD_REQUEST)

        for _ in range(10):
            code = generate_room_code()
            try:
                room = DuelRoom.objects.create(
                    creator=request.user,
                    code=code,
                    language=language,
                    difficulty=difficulty,
                    buggy_code=buggy_code,
                    duration=duration,
                )
                return Response({'code': room.code}, status=status.HTTP_201_CREATED)
            except Exception:
                continue
        return Response({'error': 'Failed to generate unique room code'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JoinDuelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        try:
            room = DuelRoom.objects.select_related('creator').get(code=code, status='waiting')
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Room not found or already started'}, status=status.HTTP_404_NOT_FOUND)
        if room.creator == request.user:
            return Response({'error': 'You cannot join your own room'}, status=status.HTTP_400_BAD_REQUEST)
        room.opponent = request.user
        room.status = 'active'
        room.started_at = timezone.now()
        room.save()
        invalidate_room_cache(code)
        send_notification(
            user=room.creator,
            notification_type='opponent_joined',
            message=f'{request.user.username} joined your duel room {code}'
        )
        channel_layer = get_channel_layer_instance()
        async_to_sync(channel_layer.group_send)(
            f'duel_{code}',
            {'type': 'room_update', 'status': 'active', 'code': code}
        )
        return Response({'ok': True})

class DuelDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, code):
        try:
            room = get_cached_room(code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DuelRoomSerializer(room).data)

def _run_judging(room_id, code):
    try:
        room = DuelRoom.objects.select_related('creator', 'opponent').get(pk=room_id)
        submissions = list(Submission.objects.filter(room=room).select_related('player'))
        if len(submissions) != 2:
            return

        creator_sub = next(s for s in submissions if s.player_id == room.creator_id)
        opponent_sub = next(s for s in submissions if s.player_id == room.opponent_id)

        result = judge_submissions(
            buggy_code=room.buggy_code,
            submission1=creator_sub.code,
            submission2=opponent_sub.code,
            language=room.language
        )
        winner = result['winner']
        p1 = result['player1']
        p2 = result['player2']

        Submission.objects.filter(pk=creator_sub.pk).update(
            correctness=p1['correctness'],
            cleanliness=p1['cleanliness'],
            efficiency=p1['efficiency'],
            security=p1['security'],
            score=p1['score'],
            ai_feedback=p1['feedback'],
            is_winner=winner == 'player1',
        )
        Submission.objects.filter(pk=opponent_sub.pk).update(
            correctness=p2['correctness'],
            cleanliness=p2['cleanliness'],
            efficiency=p2['efficiency'],
            security=p2['security'],
            score=p2['score'],
            ai_feedback=p2['feedback'],
            is_winner=winner == 'player2',
        )

        if winner == 'player1':
            room.creator.wins += 1
            room.creator.current_streak += 1
            room.creator.best_streak = max(room.creator.best_streak, room.creator.current_streak)
            room.creator.last_win_at = timezone.now()
            room.opponent.losses += 1
            room.opponent.current_streak = 0
        elif winner == 'player2':
            room.opponent.wins += 1
            room.opponent.current_streak += 1
            room.opponent.best_streak = max(room.opponent.best_streak, room.opponent.current_streak)
            room.opponent.last_win_at = timezone.now()
            room.creator.losses += 1
            room.creator.current_streak = 0
        room.creator.total_duels += 1
        room.opponent.total_duels += 1
        room.creator.save(update_fields=['wins', 'losses', 'total_duels', 'current_streak', 'best_streak', 'last_win_at'])
        room.opponent.save(update_fields=['wins', 'losses', 'total_duels', 'current_streak', 'best_streak', 'last_win_at'])

        room.status = 'finished'
        room.finished_at = timezone.now()
        room.save(update_fields=['status', 'finished_at'])
        invalidate_room_cache(code)

        channel_layer = get_channel_layer_instance()
        async_to_sync(channel_layer.group_send)(
            f'duel_{code}',
            {'type': 'duel_judged'}
        )
    except Exception as e:
        logger.exception("Judging failed for room %s", code)
        try:
            room = DuelRoom.objects.get(pk=room_id)
            room.status = 'finished'
            room.finished_at = timezone.now()
            room.save(update_fields=['status', 'finished_at'])
            invalidate_room_cache(code)
            channel_layer = get_channel_layer_instance()
            async_to_sync(channel_layer.group_send)(
                f'duel_{code}',
                {'type': 'duel_judged'}
            )
        except Exception:
            pass


class SubmitCodeView(APIView):
    permission_classes = [IsAuthenticated, IsDuelParticipant]

    def post(self, request, code):
        try:
            room = get_cached_room(code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Active room not found'}, status=status.HTTP_404_NOT_FOUND)
        if room.status != 'active':
            return Response({'error': 'Room is not active'}, status=status.HTTP_400_BAD_REQUEST)

        code_text = request.data.get('code', '').strip()
        if not code_text:
            return Response({'error': 'Code cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        existing = Submission.objects.filter(room=room, player=request.user).first()
        if existing:
            return Response({'error': 'You already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        Submission.objects.create(
            room=room,
            player=request.user,
            code=code_text
        )

        channel_layer = get_channel_layer_instance()
        async_to_sync(channel_layer.group_send)(
            f'duel_{code}',
            {'type': 'submitted', 'player': request.user.username}
        )

        submissions = Submission.objects.filter(room=room).select_related('player')
        if submissions.count() == 2:
            room.status = 'judging'
            room.save()
            invalidate_room_cache(code)
            subs = list(submissions)
            creator_sub = next(s for s in subs if s.player_id == room.creator_id)
            opponent_sub = next(s for s in subs if s.player_id == room.opponent_id)
            other_player = room.opponent if request.user == room.creator else room.creator
            send_notification(
                user=other_player,
                notification_type='opponent_submitted',
                message=f'{request.user.username} submitted their code in room {code}'
            )
            try:
                result = judge_submissions(
                    buggy_code=room.buggy_code,
                    submission1=creator_sub.code,
                    submission2=opponent_sub.code,
                    language=room.language
                )
                winner = result['winner']
                p1 = result['player1']
                p2 = result['player2']

                Submission.objects.filter(pk=creator_sub.pk).update(
                    correctness=p1['correctness'],
                    cleanliness=p1['cleanliness'],
                    efficiency=p1['efficiency'],
                    security=p1['security'],
                    score=p1['score'],
                    ai_feedback=p1['feedback'],
                    is_winner=winner == 'player1',
                )
                Submission.objects.filter(pk=opponent_sub.pk).update(
                    correctness=p2['correctness'],
                    cleanliness=p2['cleanliness'],
                    efficiency=p2['efficiency'],
                    security=p2['security'],
                    score=p2['score'],
                    ai_feedback=p2['feedback'],
                    is_winner=winner == 'player2',
                )

                if winner == 'player1':
                    room.creator.wins += 1
                    room.creator.current_streak += 1
                    room.creator.best_streak = max(room.creator.best_streak, room.creator.current_streak)
                    room.creator.last_win_at = timezone.now()
                    room.opponent.losses += 1
                    room.opponent.current_streak = 0
                elif winner == 'player2':
                    room.opponent.wins += 1
                    room.opponent.current_streak += 1
                    room.opponent.best_streak = max(room.opponent.best_streak, room.opponent.current_streak)
                    room.opponent.last_win_at = timezone.now()
                    room.creator.losses += 1
                    room.creator.current_streak = 0
                # tie: neither player gets a win/loss, streaks unchanged
                room.creator.total_duels += 1
                room.opponent.total_duels += 1
                room.creator.save(update_fields=['wins', 'losses', 'total_duels', 'current_streak', 'best_streak', 'last_win_at'])
                room.opponent.save(update_fields=['wins', 'losses', 'total_duels', 'current_streak', 'best_streak', 'last_win_at'])

                award_achievements(room.creator)
                award_achievements(room.opponent)

                room.status = 'finished'
                room.finished_at = timezone.now()
                room.save(update_fields=['status', 'finished_at'])
                invalidate_room_cache(code)

                send_notification(
                    user=room.creator,
                    notification_type='duel_judged',
                    message=f'Duel {code} has been judged'
                )
                send_duel_judged_email(room.creator, code, 'Your duel has been judged')
                send_notification(
                    user=room.opponent,
                    notification_type='duel_judged',
                    message=f'Duel {code} has been judged'
                )
                send_duel_judged_email(room.opponent, code, 'Your duel has been judged')

                async_to_sync(channel_layer.group_send)(
                    f'duel_{code}',
                    {'type': 'duel_judged'}
                )
            except Exception as e:
                room.status = 'finished'
                room.finished_at = timezone.now()
                room.save(update_fields=['status', 'finished_at'])
                invalidate_room_cache(code)
                return Response({'error': f'Judging failed: {str(e)}'}, status=500)
        return Response({'ok': True})

class RoomSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, code):
        try:
            room = get_cached_room(code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        submissions = Submission.objects.filter(room=room).select_related('player')
        return Response(SubmissionSerializer(submissions, many=True).data)


class RematchView(APIView):
    permission_classes = [IsAuthenticated, IsDuelParticipant]

    def post(self, request, code):
        try:
            old_room = DuelRoom.objects.get(code=code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Original room not found'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, old_room)

        for _ in range(10):
            new_code = generate_room_code()
            try:
                new_room = DuelRoom.objects.create(
                    creator=request.user,
                    code=new_code,
                    language=old_room.language,
                    difficulty=old_room.difficulty,
                    buggy_code=old_room.buggy_code,
                    duration=old_room.duration,
                )
                return Response({'code': new_room.code}, status=status.HTTP_201_CREATED)
            except Exception:
                continue
        return Response({'error': 'Failed to generate room code'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDuelParticipant]

    def get(self, request, code):
        try:
            room = DuelRoom.objects.select_related('creator', 'opponent').get(code=code)
        except DuelRoom.DoesNotExist:
            return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, room)

        return Response(MatchDetailSerializer(room).data)

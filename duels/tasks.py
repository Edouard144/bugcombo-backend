from core.celery import app

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from duels.models import DuelRoom
from duels.judge import judge_submissions
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()
logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def judge_duel_async(self, room_id):
    try:
        room = DuelRoom.objects.select_related('creator', 'opponent').get(pk=room_id)
    except DuelRoom.DoesNotExist:
        logger.error("Room %s not found for async judging", room_id)
        return

    submissions = list(Submission.objects.filter(room=room).select_related('player'))
    if len(submissions) != 2:
        logger.warning("Room %s does not have 2 submissions", room.code)
        return

    creator_sub = next(s for s in submissions if s.player_id == room.creator_id)
    opponent_sub = next(s for s in submissions if s.player_id == room.opponent_id)

    try:
        result = judge_submissions(
            buggy_code=room.buggy_code,
            submission1=creator_sub.code,
            submission2=opponent_sub.code,
            language=room.language,
        )
    except Exception as exc:
        logger.exception("Judging failed for room %s", room.code)
        _finish_room_as_error(room)
        return

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
        room.opponent.losses += 1
    elif winner == 'player2':
        room.opponent.wins += 1
        room.creator.losses += 1

    room.creator.total_duels += 1
    room.opponent.total_duels += 1
    room.creator.save(update_fields=['wins', 'losses', 'total_duels'])
    room.opponent.save(update_fields=['wins', 'losses', 'total_duels'])

    room.status = 'finished'
    room.finished_at = timezone.now()
    room.save(update_fields=['status', 'finished_at'])

    from notifications.tasks import send_duel_judged_notifications
    send_duel_judged_notifications.delay(room.code)

    _notify_room(room.code, 'duel_judged')


def _finish_room_as_error(room):
    room.status = 'finished'
    room.finished_at = timezone.now()
    room.save(update_fields=['status', 'finished_at'])


def _notify_room(code, event_type):
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            f'duel_{code}',
            {'type': event_type},
        )


@app.task
def cleanup_stale_rooms():
    cutoff = timezone.now() - timedelta(hours=24)
    stale_rooms = DuelRoom.objects.filter(status='waiting', created_at__lt=cutoff)
    count = stale_rooms.count()
    stale_rooms.delete()
    logger.info("Cleaned up %s stale duel rooms", count)

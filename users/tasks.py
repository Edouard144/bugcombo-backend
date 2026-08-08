from core.celery import app

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from duels.models import Submission

User = get_user_model()
logger = logging.getLogger(__name__)


@app.task
def recalculate_user_stats(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("User %s not found for stats recalculation", user_id)
        return

    wins = Submission.objects.filter(player=user, is_winner=True).count()
    losses = Submission.objects.filter(player=user, is_winner=False).exclude(room__status='waiting').count()
    total = Submission.objects.filter(player=user).exclude(room__status='waiting').count()

    user.wins = wins
    user.losses = losses
    user.total_duels = total
    user.save(update_fields=['wins', 'losses', 'total_duels'])
    logger.info("Recalculated stats for user %s: %s wins, %s losses", user_id, wins, losses)


@app.task
def cleanup_inactive_users():
    cutoff = timezone.now() - timedelta(days=365)
    inactive_users = User.objects.filter(last_login__lt=cutoff, is_active=True)
    count = inactive_users.count()
    inactive_users.update(is_active=False)
    logger.info("Deactivated %s inactive users", count)


@app.task
def batch_recalculate_leaderboard():
    users = User.objects.annotate(
        submission_count=Count('submissions', filter=Q(submissions__room__status='finished'))
    ).filter(submission_count__gt=0)

    for user in users:
        recalculate_user_stats.delay(user.pk)

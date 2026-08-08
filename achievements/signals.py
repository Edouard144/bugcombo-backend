from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from duels.models import DuelRoom
from achievements.models import Achievement

User = get_user_model()

@receiver(post_save, sender=DuelRoom)
def check_achievements_on_duel_finish(sender, instance, created, **kwargs):
    if not created and instance.status == 'finished':
        check_achievements_for_user(instance.creator)
        if instance.opponent:
            check_achievements_for_user(instance.opponent)

def check_achievements_for_user(user):
    if not user:
        return
    achievements = Achievement.objects.all()
    for achievement in achievements:
        if not user.achievements.filter(id=achievement.id).exists():
            if achievement.condition_type == 'wins' and user.wins >= achievement.condition_value:
                user.achievements.add(achievement)
            elif achievement.condition_type == 'total_duels' and user.total_duels >= achievement.condition_value:
                user.achievements.add(achievement)
            elif achievement.condition_type == 'streak' and user.best_streak >= achievement.condition_value:
                user.achievements.add(achievement)
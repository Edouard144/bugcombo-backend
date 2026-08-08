import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('debugduel')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from duels.tasks import cleanup_stale_rooms
    from users.tasks import cleanup_inactive_users

    sender.add_periodic_task(3600, cleanup_stale_rooms.s(), name='cleanup stale rooms every hour')
    sender.add_periodic_task(86400, cleanup_inactive_users.s(), name='cleanup inactive users daily')


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

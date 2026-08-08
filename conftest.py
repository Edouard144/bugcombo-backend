import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from duels.models import DuelRoom, Submission
from bugs.models import Bug
from notifications.models import Notification
from achievements.models import Achievement
from chat.models import ChatMessage

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='otheruser',
        email='other@test.com',
        password='otherpass123',
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='adminpass123',
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def other_client(api_client, other_user):
    api_client.force_authenticate(user=other_user)
    return api_client


@pytest.fixture
def waiting_room(db, user):
    return DuelRoom.objects.create(
        creator=user,
        code='WAIT01',
        language='python',
        difficulty='easy',
        status='waiting',
    )


@pytest.fixture
def active_room(db, user, other_user):
    return DuelRoom.objects.create(
        creator=user,
        opponent=other_user,
        code='ACT001',
        language='python',
        difficulty='easy',
        status='active',
    )


@pytest.fixture
def finished_room(db, user, other_user):
    return DuelRoom.objects.create(
        creator=user,
        opponent=other_user,
        code='FIN001',
        language='python',
        difficulty='easy',
        status='finished',
    )


@pytest.fixture
def bug(db, user):
    return Bug.objects.create(
        title='Test Bug',
        description='A test bug for unit tests',
        language='python',
        difficulty='easy',
        starter_code='def fix_this(): pass',
        test_cases=[{'input': '1', 'expected': '2'}],
        created_by=user,
    )


@pytest.fixture
def other_bug(db, other_user):
    return Bug.objects.create(
        title='Other Bug',
        description='Created by another user',
        language='javascript',
        difficulty='medium',
        created_by=other_user,
    )


@pytest.fixture
def notification(db, user):
    return Notification.objects.create(
        user=user,
        type='opponent_joined',
        message='Test notification',
    )


@pytest.fixture
def achievement(db):
    return Achievement.objects.create(
        name='First Win',
        description='Win your first duel',
        icon='trophy',
        condition='first_win',
    )


@pytest.fixture
def ten_win_achievement(db):
    return Achievement.objects.create(
        name='Ten Wins',
        description='Win 10 duels',
        icon='star',
        condition='ten_wins',
    )


@pytest.fixture
def chat_message(db, user, active_room):
    return ChatMessage.objects.create(
        room_code=active_room.code,
        sender=user,
        message='Hello!',
    )

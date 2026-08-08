from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from bugs.models import Bug

User = get_user_model()


class BugListCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.admin = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='adminpass123'
        )
        self.bug = Bug.objects.create(
            title='Test Bug', description='A test bug',
            language='python', difficulty='easy',
            created_by=self.user,
        )

    def test_list_bugs_returns_paginated_results(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_bugs_requires_authentication(self):
        response = self.client.get('/api/bugs/')
        self.assertEqual(response.status_code, 401)

    def test_create_bug_requires_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/bugs/', {
            'title': 'New Bug', 'description': 'A new bug',
        })
        self.assertEqual(response.status_code, 403)

    def test_create_bug_as_admin_succeeds(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/bugs/', {
            'title': 'Admin Bug', 'description': 'Created by admin',
            'language': 'python', 'difficulty': 'easy',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'Admin Bug')

    def test_filter_by_language(self):
        Bug.objects.create(
            title='JS Bug', description='JavaScript bug',
            language='javascript', difficulty='medium', created_by=self.user,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/?language=python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_difficulty(self):
        Bug.objects.create(
            title='Hard Bug', description='Hard bug',
            language='python', difficulty='hard', created_by=self.user,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/?difficulty=easy')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_search_by_title(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_ordering(self):
        Bug.objects.create(
            title='Another Bug', description='Another',
            language='python', difficulty='easy', created_by=self.user,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/?ordering=created_at')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

    def test_pagination(self):
        for i in range(25):
            Bug.objects.create(
                title=f'Bug {i}', description=f'Description {i}',
                language='python', difficulty='easy', created_by=self.user,
            )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/?limit=10&page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 10)


class BugDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.other = User.objects.create_user(
            username='other', email='other@test.com', password='otherpass123'
        )
        self.bug = Bug.objects.create(
            title='Test Bug', description='A test bug',
            language='python', difficulty='easy', created_by=self.user,
        )
        self.other_bug = Bug.objects.create(
            title='Other Bug', description='Other bug',
            language='python', difficulty='easy', created_by=self.other,
        )

    def test_get_bug(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/bugs/{self.bug.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Test Bug')

    def test_get_nonexistent_bug(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/bugs/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(response.status_code, 404)

    def test_update_own_bug(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(f'/api/bugs/{self.bug.id}/', {
            'title': 'Updated Bug', 'description': 'Updated',
            'language': 'python', 'difficulty': 'medium',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Updated Bug')

    def test_update_other_users_bug_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(f'/api/bugs/{self.other_bug.id}/', {
            'title': 'Hacked',
        })
        self.assertEqual(response.status_code, 403)

    def test_delete_own_bug(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/bugs/{self.bug.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Bug.objects.filter(pk=self.bug.id).exists())

    def test_delete_other_users_bug_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/bugs/{self.other_bug.id}/')
        self.assertEqual(response.status_code, 403)


class FeaturedBugsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.bug = Bug.objects.create(
            title='Test Bug', description='A test bug',
            language='python', difficulty='easy', created_by=self.user,
        )

    def test_featured_bugs(self):
        response = self.client.get('/api/bugs/featured/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_featured_bugs_no_auth_required(self):
        response = self.client.get('/api/bugs/featured/')
        self.assertEqual(response.status_code, 200)


class RandomBugTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@test.com', password='testpass123'
        )
        self.bug = Bug.objects.create(
            title='Test Bug', description='A test bug',
            language='python', difficulty='easy', created_by=self.user,
        )

    def test_random_bug(self):
        response = self.client.get('/api/bugs/random/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Test Bug')

    def test_random_bug_with_filters(self):
        response = self.client.get('/api/bugs/random/?language=python&difficulty=easy')
        self.assertEqual(response.status_code, 200)

    def test_random_bug_no_results(self):
        response = self.client.get('/api/bugs/random/?language=go')
        self.assertEqual(response.status_code, 404)

    def test_random_bug_no_auth_required(self):
        response = self.client.get('/api/bugs/random/')
        self.assertEqual(response.status_code, 200)

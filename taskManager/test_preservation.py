from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings

from taskManager.models import Project


class FakeRedis:
    def exists(self, key):
        return False

    def get(self, key):
        return 0

    def delete(self, key):
        return None

    def incr(self, key):
        return 1

    def expire(self, key, timeout):
        return None


class VulnerabilityPreservationTests(TestCase):
    """
    Regression checks for intentionally vulnerable training surfaces.

    These tests document current behavior so modernization work does not
    accidentally remove the vulnerable routes or harden them as a side effect.
    """

    fixtures = [
        'users',
        'usersProfiles',
        'groups',
        'auth_group_permissions',
        'taskManagerProjects',
        'taskManagerNotes',
        'taskManagerTasks',
    ]

    def setUp(self):
        self.client = Client()

    @override_settings(REDIS=FakeRedis())
    def test_login_sets_jwt_cookies_with_insecure_flags(self):
        response = self.client.post(
            '/taskManager/login/',
            {'username': 'chris', 'password': 'test123'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertEqual(response.cookies['access_token']['httponly'], '')
        self.assertEqual(response.cookies['access_token']['secure'], '')
        self.assertEqual(response.cookies['refresh_token']['httponly'], '')
        self.assertEqual(response.cookies['refresh_token']['secure'], '')

    def test_search_preserves_raw_sql_query_path(self):
        self.client.login(username='chris', password='test123')

        with patch('taskManager.views.Task.objects.raw', return_value=[]) as raw:
            with patch('taskManager.views.render', return_value=HttpResponse('ok')):
                response = self.client.get('/taskManager/search/', {'q': "needle' OR '1'='1"})

        self.assertEqual(response.status_code, 200)
        raw.assert_called_once()
        sql = raw.call_args.args[0]
        self.assertIn('select * from taskManager_task', sql)
        self.assertIn("needle' OR '1'='1", sql)
        self.assertNotIn('%s', sql)

    def test_forgot_password_preserves_raw_sql_email_lookup(self):
        with patch('taskManager.views.User.objects.raw', return_value=[]) as raw:
            with patch('taskManager.views.render', return_value=HttpResponse('ok')):
                response = self.client.post(
                    '/taskManager/forgot_password/',
                    {'email': "person@example.com' OR '1'='1"},
                )

        self.assertEqual(response.status_code, 200)
        raw.assert_called_once()
        sql = raw.call_args.args[0]
        self.assertEqual(
            sql,
            "SELECT * FROM auth_user where email = 'person@example.com' OR '1'='1'",
        )

    def test_ping_preserves_subprocess_execution_of_request_controlled_text(self):
        with patch('taskManager.views.subprocess.getoutput', return_value='pong') as getoutput:
            with patch('taskManager.views.render', return_value=HttpResponse('ok')):
                response = self.client.post(
                    '/taskManager/ping/',
                    {'ip': '127.0.0.1; id'},
                )

        self.assertEqual(response.status_code, 200)
        getoutput.assert_called_once_with('ping -c 5 127.0.0.1; id')

    def test_upload_url_preserves_server_side_fetch_of_supplied_url(self):
        self.client.login(username='chris', password='test123')
        project = Project.objects.get(pk=6)
        self.assertTrue(project.users_assigned.filter(username='chris').exists())
        remote_url = 'http://169.254.169.254/latest/meta-data/avatar.png'
        mocked_response = Mock(
            content=b'fake image bytes',
            headers={'Content-Type': 'image/png'},
        )

        with patch('taskManager.views.requests.get', return_value=mocked_response) as get:
            with patch('taskManager.views.store_url_data', return_value='/tmp/avatar.png'):
                response = self.client.post(
                    f'/taskManager/{project.pk}/upload/',
                    {'name': 'avatar', 'url': remote_url},
                )

        self.assertEqual(response.status_code, 302)
        get.assert_called_once_with(remote_url, timeout=15)

    def test_profile_by_id_preserves_cross_user_edit_behavior(self):
        self.client.login(username='chris', password='test123')
        target = User.objects.get(username='seth')

        with patch('taskManager.views.render', return_value=HttpResponse('ok')):
            response = self.client.post(
                f'/taskManager/profile/{target.pk}',
                {
                    'first_name': target.first_name,
                    'last_name': 'EditedByChris',
                    'email': target.email,
                    'dob': target.userprofile.dob,
                    'ssn': target.userprofile.ssn,
                    'groups': 'project_managers',
                },
            )

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertEqual(target.last_name, 'EditedByChris')

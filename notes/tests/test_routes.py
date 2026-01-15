from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )

    def test_home_page_availability(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю
        доступны страницы notes/, done/, add/.
        """
        self.client.force_login(self.author)
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Страницы отдельной заметки, удаления
        и редактирования доступны только автору.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user.username, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Анонимный пользователь перенаправляется на страницу логина."""
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_auth_pages_availability(self):
        """Страницы регистрации, входа и выхода доступны всем."""
        urls = (
            ('users:signup', None),
            ('users:login', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_page(self):
        """Страница выхода из аккаунта должна быть доступна."""
        url = reverse('users:logout')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn(response.status_code,
                      [HTTPStatus.OK, HTTPStatus.METHOD_NOT_ALLOWED,
                       HTTPStatus.FOUND])

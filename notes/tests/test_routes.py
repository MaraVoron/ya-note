from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты доступности страниц."""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных."""
        cls.author = User.objects.create_user(
            username='author_user',
            password='author_password'
        )
        cls.reader = User.objects.create_user(
            username='reader_user',
            password='reader_password'
        )
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст тестовой заметки',
            slug='test-note',
            author=cls.author
        )

    def setUp(self):
        """Настройка клиентов для тестов."""
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.reader_client = Client()
        self.reader_client.force_login(self.reader)
        self.anonymous_client = Client()

    def test_home_page_available_to_anonymous(self):
        """
        Главная страница доступна анонимному пользователю.
        """
        url = reverse('notes:home')
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_pages_availability(self):
        """
        Аутентифицированному пользователю доступны:
        страница со списком заметок notes/
        траница успешного добавления заметки done/
        страница добавления новой заметки add/
        """
        urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_note_pages_availability_for_author_only(self):
        """
        Страницы: заметка, удаление и редактирование заметки
        доступны только автору заметки.
        """
        note_pages = [
            ('notes:detail', {'slug': self.note.slug}),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
        ]

        for page_name, kwargs in note_pages:
            with self.subTest(page_name=page_name, user='author'):
                url = reverse(page_name, kwargs=kwargs)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_note_pages_not_available_for_other_users(self):
        """
        Если на страницы заметки попытается зайти другой пользователь -
        ошибка 404.
        """
        note_pages = [
            ('notes:detail', {'slug': self.note.slug}),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
        ]

        for page_name, kwargs in note_pages:
            with self.subTest(page_name=page_name, user='reader'):
                url = reverse(page_name, kwargs=kwargs)
                response = self.reader_client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_anonymous_user_redirected_to_login(self):
        """
        Анонимный пользователь не может попасть на защищённые страницы
        """
        protected_urls = [
            reverse('notes:list'),
            reverse('notes:success'),
            reverse('notes:add'),
            reverse('notes:detail', kwargs={'slug': self.note.slug}),
            reverse('notes:edit', kwargs={'slug': self.note.slug}),
            reverse('notes:delete', kwargs={'slug': self.note.slug}),
        ]

        login_url = reverse('users:login')

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.anonymous_client.get(url)
                self.assertRedirects(
                    response,
                    f'{login_url}?next={url}'
                )

    def test_auth_pages_available_to_all(self):
        """
        Страницы: регистрация пользователей, вход
        и выход доступны всем пользователям.
        """
        auth_urls = [
            ('users:signup', 200),
            ('users:login', 200),
            ('users:logout', 405),]

        for url_name, expected_status in auth_urls:
            with self.subTest(url_name=url_name):
                url = reverse(url_name)

            response = self.anonymous_client.get(url)
            self.assertEqual(response.status_code, expected_status)

            response = self.author_client.get(url)
            self.assertEqual(response.status_code, expected_status)

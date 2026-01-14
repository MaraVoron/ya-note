from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import pytils.translit

from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):
    """Тесты бизнес-логики приложения."""

    @classmethod
    def setUpTestData(cls):
        """Создание тестовых данных."""
        cls.author = User.objects.create_user(
            username='author_user',
            password='author_password'
        )
        cls.other_user = User.objects.create_user(
            username='other_user',
            password='other_password'
        )

        cls.note_data = {
            'title': 'Тестовая заметка',
            'text': 'Текст тестовой заметки',
            'slug': 'test-note',
        }

        cls.existing_note = Note.objects.create(
            **cls.note_data,
            author=cls.author
        )

    def setUp(self):
        """Настройка клиентов для тестов."""
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.other_client = Client()
        self.other_client.force_login(self.other_user)
        self.anonymous_client = Client()

    def test_authenticated_user_can_create_note(self):
        """
        Залогиненный пользователь может создать заметку.
        """
        notes_count_before = Note.objects.count()

        new_note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note',
        }

        url = reverse('notes:add')
        response = self.author_client.post(url, data=new_note_data)

        self.assertRedirects(response, reverse('notes:success'))

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)

        self.assertTrue(
            Note.objects.filter(slug='new-note').exists()
        )

    def test_anonymous_user_cannot_create_note(self):
        """
        Анонимный пользователь не может создать заметку.
        """
        notes_count_before = Note.objects.count()

        new_note_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
            'slug': 'new-note',
        }

        url = reverse('notes:add')
        response = self.anonymous_client.post(url, data=new_note_data)

        login_url = reverse('users:login')
        self.assertRedirects(
            response,
            f'{login_url}?next={url}'
        )

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_cannot_create_duplicate_slug(self):
        """
        Невозможно создать две заметки с одинаковым slug.
        """
        notes_count_before = Note.objects.count()

        duplicate_note_data = {
            'title': 'Другая заметка',
            'text': 'Текст другой заметки',
            'slug': 'test-note',
        }

        url = reverse('notes:add')

        response = self.author_client.post(url, data=duplicate_note_data)

        self.assertEqual(response.status_code, 200)

        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_auto_generate_slug_if_empty(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически.
        """
        note_without_slug = {
            'title': 'Заметка без slug',
            'text': 'Текст заметки без slug',
        }

        url = reverse('notes:add')
        response = self.author_client.post(url, data=note_without_slug)

        self.assertRedirects(response, reverse('notes:success'))

        created_note = Note.objects.filter(
            title='Заметка без slug',
            author=self.author
        ).first()

        self.assertIsNotNone(created_note)
        self.assertIsNotNone(created_note.slug)
        self.assertNotEqual(created_note.slug, '')

        expected_slug = pytils.translit.slugify('Заметка без slug')
        self.assertEqual(created_note.slug, expected_slug)

    def test_user_can_edit_own_note(self):
        """
        Пользователь может редактировать свои заметки.
        """
        updated_data = {
            'title': 'Обновленный заголовок',
            'text': 'Обновленный текст',
            'slug': 'test-note',
        }

        url = reverse('notes:edit', kwargs={'slug': self.existing_note.slug})
        response = self.author_client.post(url, data=updated_data)

        self.assertRedirects(response, reverse('notes:success'))

        self.existing_note.refresh_from_db()

        self.assertEqual(self.existing_note.title, 'Обновленный заголовок')
        self.assertEqual(self.existing_note.text, 'Обновленный текст')

    def test_user_cannot_edit_other_users_note(self):
        """
        Пользователь не может редактировать чужие заметки.
        """
        updated_data = {
            'title': 'Попытка изменить чужую',
            'text': 'Текст чужой заметки',
            'slug': 'test-note',
        }

        url = reverse('notes:edit', kwargs={'slug': self.existing_note.slug})
        response = self.other_client.post(url, data=updated_data)

        self.assertEqual(response.status_code, 404)

        self.existing_note.refresh_from_db()
        self.assertEqual(self.existing_note.title, 'Тестовая заметка')
        self.assertEqual(self.existing_note.text, 'Текст тестовой заметки')

    def test_user_can_delete_own_note(self):
        """
        Пользователь может удалять свои заметки.
        """
        notes_count_before = Note.objects.count()

        url = reverse('notes:delete', kwargs={'slug': self.existing_note.slug})
        response = self.author_client.post(url)

        self.assertRedirects(response, reverse('notes:success'))

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

        with self.assertRaises(Note.DoesNotExist):
            Note.objects.get(slug='test-note', author=self.author)

    def test_user_cannot_delete_other_users_note(self):
        """
        Пользователь не может удалять чужие заметки.
        """
        notes_count_before = Note.objects.count()

        url = reverse('notes:delete', kwargs={'slug': self.existing_note.slug})
        response = self.other_client.post(url)

        self.assertEqual(response.status_code, 404)

        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

        self.assertTrue(
            Note.objects.filter(slug='test-note').exists()
        )

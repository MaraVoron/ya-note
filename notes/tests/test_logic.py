from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
import pytils.translit

from notes.models import Note

User = get_user_model()


class TestCommentCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

    def test_author_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        notes_count = Note.objects.count()
        form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), notes_count + 1)
        new_note = Note.objects.get(slug='new-slug')
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.text, form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count = Note.objects.count()
        form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
        }
        response = self.client.post(self.add_url, data=form_data)
        login_url = reverse('users:login')
        redirect_url = f'{login_url}?next={self.add_url}'
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Note.objects.count(), notes_count)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        notes_count = Note.objects.count()
        form_data = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
            'slug': self.note.slug,
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Note.objects.count(), notes_count)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('slug', form.errors)
        error_message = form.errors['slug'][0]
        self.assertIn(self.note.slug, error_message)

    def test_empty_slug(self):
        """Если slug не заполнен, он формируется автоматически."""
        notes_count = Note.objects.count()
        form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': '',
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), notes_count + 1)
        new_note = Note.objects.get(title='Новый заголовок')
        expected_slug = pytils.translit.slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.form_data = {
            'title': 'Обновленный заголовок',
            'text': 'Обновленный текст',
            'slug': 'updated-slug',
        }

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Пользователь не может редактировать чужие заметки."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'Заголовок')
        self.assertEqual(self.note.text, 'Текст заметки')
        self.assertEqual(self.note.slug, 'note-slug')

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        notes_count = Note.objects.count()
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), notes_count - 1)

    def test_other_user_cant_delete_note(self):
        """Пользователь не может удалять чужие заметки."""
        notes_count = Note.objects.count()
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), notes_count)

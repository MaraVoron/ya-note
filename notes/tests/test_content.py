from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметок')
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        Note.objects.create(
            title='Заголовок другого',
            text='Текст другой заметки',
            slug='other-note',
            author=cls.reader
        )

    def test_note_in_list(self):
        """Отдельная заметка передаётся на страницу со списком заметок."""
        self.client.force_login(self.author)
        url = reverse('notes:list')
        response = self.client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_notes_list_for_different_users(self):
        """В список заметок одного пользователя не попадают заметки другого."""
        users_notes_count = (
            (self.author, 1),
            (self.reader, 1),
        )
        for user, notes_count in users_notes_count:
            self.client.force_login(user)
            url = reverse('notes:list')
            response = self.client.get(url)
            object_list = response.context['object_list']
            self.assertEqual(object_list.count(), notes_count)
            for note in object_list:
                self.assertEqual(note.author, user)

    def test_pages_contain_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.force_login(self.author)
        urls_with_forms = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls_with_forms:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

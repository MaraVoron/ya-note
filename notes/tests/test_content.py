from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.another_user = User.objects.create(username='Другой автор')
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )

        Note.objects.create(
            title='Заголовок другого',
            text='Текст другой заметки',
            slug='another-note',
            author=cls.another_user
        )

    def test_notes_list_for_different_users(self):
        """В список заметок попадают только заметки текущего пользователя."""
        url = reverse('notes:list')

        response = self.author_client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)
        self.assertEqual(object_list.count(), 1)

        response = self.another_client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)
        self.assertEqual(object_list.count(), 1)

    def test_pages_contain_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

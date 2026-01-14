from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):
    """Тесты контекста и передаваемых данных."""

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

        cls.note1 = Note.objects.create(
            title='Заметка 1 автора',
            text='Текст заметки 1',
            slug='note-1',
            author=cls.author
        )
        cls.note2 = Note.objects.create(
            title='Заметка 2 автора',
            text='Текст заметки 2',
            slug='note-2',
            author=cls.author
        )

        cls.other_note = Note.objects.create(
            title='Заметка другого пользователя',
            text='Текст чужой заметки',
            slug='other-note',
            author=cls.other_user
        )

    def setUp(self):
        """Настройка клиента для тестов."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_note_in_list_context(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок
        в списке object_list в словаре context.
        """
        url = reverse('notes:list')
        response = self.author_client.get(url)

        self.assertIn('object_list', response.context)

        notes_in_context = response.context['object_list']
        self.assertIn(self.note1, notes_in_context)
        self.assertIn(self.note2, notes_in_context)

    def test_user_sees_only_own_notes(self):
        """
        В список заметок одного пользователя не попадают заметки
        другого пользователя.
        """
        url = reverse('notes:list')
        response = self.author_client.get(url)

        notes_in_context = response.context['object_list']

        self.assertIn(self.note1, notes_in_context)
        self.assertIn(self.note2, notes_in_context)

        self.assertNotIn(self.other_note, notes_in_context)

        self.assertEqual(notes_in_context.count(), 2)

    def test_form_passed_to_add_page(self):
        """
        На страницу создания заметки передается форма.
        """
        url = reverse('notes:add')
        response = self.author_client.get(url)

        self.assertIn('form', response.context)

        from notes.forms import NoteForm
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_form_passed_to_edit_page(self):
        """
        На страницу редактирования заметки передается форма.
        """
        url = reverse('notes:edit', kwargs={'slug': self.note1.slug})
        response = self.author_client.get(url)

        self.assertIn('form', response.context)

        form = response.context['form']
        self.assertEqual(form.instance, self.note1)

        self.assertIsInstance(form, NoteForm)

from http import HTTPStatus

from django.test import Client, TestCase
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.core import (
    CoreTestCase,
    FIELD_DATA,
    FIELD_NAMES,
    FIELD_NEW_DATA,
    AUTHOR,
    URL,
    SLUG,
    USER_MODEL,
)


class CheckData(TestCase):
    def check_data(self, field_data):
        """Сравнение данных заметки в БД с данными отправленными в форме."""
        note = Note.objects.get()
        db_data = (note.title, note.text, note.slug, note.author)
        for name, sent_value, db_value in zip(
            FIELD_NAMES, field_data, db_data
        ):
            with self.subTest(sent_value=sent_value, db_value=db_value):
                self.assertEqual(
                    sent_value,
                    db_value,
                    msg=(
                        f'В базу данных, в поле {name} было записано: '
                        f'{db_value}. Убедитесь что передаете верные данные '
                        f'- {sent_value}.'
                    ),
                )

    def equal(self, expected_count):
        """Сравнение кол-ва заметок в БД."""
        notes_count = Note.objects.count()
        self.assertEqual(
            expected_count,
            notes_count,
            msg=(
                f'Кол-во заметок в БД {notes_count} не соответствует '
                f'ожидаемому {expected_count}.'
            ),
        )


class TestCreateNote(CheckData):
    @classmethod
    def setUpTestData(cls):
        cls.author = USER_MODEL.objects.create(username=AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = dict(zip(FIELD_NAMES, FIELD_DATA))
        cls.field_data = (*FIELD_DATA, cls.author)

    def test_user_can_create_note(self):
        """Проверка создания заметки авторизованным пользователем."""
        expected_count = Note.objects.count() + 1
        self.assertRedirects(
            self.author_client.post(URL.add, data=self.form_data),
            URL.success,
            msg_prefix=(
                f'После создания заметки, не выполнен редирект на '
                f'страницу {URL.success}.'
            ),
        )
        super().equal(expected_count)
        super().check_data(self.field_data)

    def test_anonymous_user_cant_create_note(self):
        """Проверка создания заметки анонимным пользователем."""
        expected_count = Note.objects.count()
        expected_url = f'{URL.login}?next={URL.add}'
        self.assertRedirects(
            self.client.post(URL.add, data=self.form_data),
            expected_url,
            msg_prefix=(
                f'При попытке создать заметку, анонимный пользователь '
                f'должен быть перенаправлен на страницу входа '
                f'{expected_url}.'
            ),
        )
        super().equal(expected_count)

    def test_not_unique_slug(self):
        """Проверка дублирования slug."""
        expected_count = Note.objects.count() + 1
        Note.objects.create(**dict(zip(FIELD_NAMES, self.field_data)))
        self.assertFormError(
            self.author_client.post(URL.add, data=self.form_data),
            form='form',
            field='slug',
            errors=(SLUG + WARNING),
            msg_prefix=(
                f'Убедитесь, что форма создания заметки, возвращает '
                f'ошибку "{WARNING}" при попытке создать заметку с '
                f'существующим slug.'
            ),
        )
        super().equal(expected_count)

    def test_empty_slug(self):
        """Проверка автоматического создания slug."""
        expected_count = Note.objects.count() + 1
        self.form_data.pop('slug')
        self.assertRedirects(
            self.author_client.post(URL.add, data=self.form_data),
            URL.success,
            msg_prefix=(
                'Убедитесь что при отсутствии данных в поле slug, '
                'форма формирует данные автоматически на основе'
                'заголовка заметки. После добавления заметки пользователь '
                'должен быть перенаправлен на страницу успешного '
                'создания заметки.'
            ),
        )
        super().equal(expected_count)
        note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(
            note.slug,
            expected_slug,
            msg=(
                f'Автоматически сформированные данные {note.slug} для поля '
                f'slug, не соответствуют ожидаемым - {expected_slug}.'
            ),
        )


class TestNoteEditDelete(CoreTestCase, CheckData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.new_data = dict(zip(FIELD_NAMES, FIELD_NEW_DATA))

    def test_author_can_delete_note(self):
        """Проверка удаления заметки автором."""
        expected_count = Note.objects.count() - 1
        self.assertRedirects(
            self.author_client.delete(URL.delete),
            URL.success,
            msg_prefix=(
                f'После удаления заметки, не выполнен редирект на '
                f'страницу {URL.success}.'
            ),
        )
        super().equal(expected_count)

    def test_other_user_cant_delete_note(self):
        """Проверка удаления заметки не автором."""
        expected_count = Note.objects.count()
        self.assertEqual(
            self.user_client.delete(URL.delete).status_code,
            HTTPStatus.NOT_FOUND,
            msg=(
                'При попытке удалить чужую заметку, пользователь '
                'должен быть перенаправлен на страницу 404.'
            ),
        )
        super().equal(expected_count)

    def test_author_can_edit_note(self):
        """Проверка редактирования заметки автором."""
        self.assertRedirects(
            self.author_client.post(URL.edit, data=self.new_data),
            URL.success,
            msg_prefix=(
                f'После редактирования заметки, не выполнен редирект на '
                f'страницу {URL.success}.'
            ),
        )
        super().check_data((*FIELD_NEW_DATA, self.author))

    def test_other_user_cant_edit_note(self):
        """Проверка редактирования заметки не автором."""
        self.assertEqual(
            self.user_client.post(URL.edit, data=self.new_data).status_code,
            HTTPStatus.NOT_FOUND,
            msg=(
                'При попытке отредактировать чужую заметку, пользователь '
                'должен быть перенаправлен на страницу 404.'
            ),
        )
        super().check_data((*FIELD_DATA, self.author))

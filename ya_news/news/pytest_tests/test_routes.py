from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects

from conftest import URL, ADMIN, AUTHOR, CLIENT

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'url, parametrized_client, expected_status',
    (
        (URL.home, CLIENT, HTTPStatus.OK),
        (URL.detail, CLIENT, HTTPStatus.OK),
        (URL.login, CLIENT, HTTPStatus.OK),
        (URL.logout, CLIENT, HTTPStatus.OK),
        (URL.signup, CLIENT, HTTPStatus.OK),
        (URL.edit, AUTHOR, HTTPStatus.OK),
        (URL.delete, AUTHOR, HTTPStatus.OK),
        (URL.edit, ADMIN, HTTPStatus.NOT_FOUND),
        (URL.delete, ADMIN, HTTPStatus.NOT_FOUND),
    ),
)
def test_pages_availability_for_anonymous_user(
    url, parametrized_client, expected_status, comment
):
    """Проверка доступа к страницам."""
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'url',
    (URL.edit, URL.delete),
)
def test_redirect_for_anonymous_client(client, url, comment):
    """Проверка редиректа для анонимного пользователя."""
    expected_url = f'{URL.login}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)

import datetime
import pytest
from api.models import Habit
from rest_framework import status
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_list_own_and_public_habits(api_client, user, habit):
    """
    Пользователь видит только свои ЛЮБЫЕ привычки + чужие ПУБЛИЧНЫЕ.
    """
    # Создаём чужую приватную привычку
    other_user = get_user_model().objects.create_user(email='other@example.com', password='pass')
    Habit.objects.create(
        owner=other_user,
        place='Улица',
        time=datetime.time(7, 30),
        action='Сходить в магазин',
        is_pleasant=False,
        periodicity=1,
        execution_time=60,
        reward='Купить мороженое',
        is_public=False,  # приватная — не должна быть видна
    )

    # Авторизуемся
    api_client.force_authenticate(user=user)

    response = api_client.get('/api/v1/auth/habits/')

    assert response.status_code == status.HTTP_200_OK
    # Должна быть видна своя привычка и публичные чужие (их нет), но НЕ чужая приватная
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == habit.id


@pytest.mark.django_db
def test_delete_not_own_habit(api_client, user):
    """
    Нельзя удалять чужую привычку.
    """
    other_user = get_user_model().objects.create_user(email='other@example.com', password='pass')
    other_habit = Habit.objects.create(
        owner=other_user,
        action="Чужая",
        place="Улица",
        time="18:00",
        is_pleasant=True,
        periodicity=7,
        execution_time=90
    )

    api_client.force_authenticate(user=user)
    response = api_client.delete(f'/api/v1/auth/habits/{other_habit.id}/')

    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
def test_register_user(api_client):
    # Регистрация пользователя через API
    data = {
        'email': 'newuser@example.com',
        'password': 'StrongPass123!',
        'first_name': 'New'
    }
    response = api_client.post('/api/v1/auth/register/', data)
    assert response.status_code == 201
    user = get_user_model().objects.get(email='newuser@example.com')
    assert hasattr(user.auth_token, 'key') is True


@pytest.mark.django_db
def test_login_user(api_client):
    # Авторизация
    get_user_model().objects.create_user(
        email='testlogin@example.com',
        password='TestLoginPass1!'
    )

    login_data = {'email': 'testlogin@example.com', 'password': 'TestLoginPass1!'}
    response = api_client.post('/api/v1/auth/login/', login_data)
    assert response.status_code == 200
    assert 'token' in response.data


@pytest.mark.parametrize('page_size,expected_count', [(4, 4), (6, 5)])
@pytest.mark.django_db
def test_habits_pagination(api_client, user, page_size, expected_count):
    # Пагинация (PAGE_SIZE в settings = 5)
    for i in range(page_size):
        Habit.objects.create(
            owner=user,
            action=f"Действие {i}",
            place="Дом",
            time=datetime.time(8, 0),
            is_pleasant=False,
            periodicity=1,
            execution_time=60,
            reward=f"Награда за действие {i}",
        )

    api_client.force_authenticate(user=user)
    response = api_client.get('/api/v1/auth/habits/')

    assert response.status_code == 200
    assert len(response.data['results']) == expected_count

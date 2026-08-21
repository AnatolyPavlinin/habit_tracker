import os
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Обеспечиваем доступ к базе данных."""
    with django_db_blocker.unblock():
        pass


@pytest.fixture()
def user():
    UserModel = get_user_model()
    return UserModel.objects.create_user(
        email='user@example.com',
        password='TestPass1!',
        first_name='User'
    )


@pytest.fixture()
def habit(user):
    from api.models import Habit
    return Habit.objects.create(
        owner=user,
        place='Кухня',
        time='07:00',
        action='Выпить стакан воды',
        is_pleasant=False,
        periodicity=1,
        execution_time=60,
        reward='Съесть конфету',
        is_public=True
    )

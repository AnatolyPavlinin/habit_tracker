from django.core.exceptions import ValidationError
from api.models import Habit
import pytest


@pytest.mark.django_db
def test_habit_clean(user):
    """
    Проверяет бизнес-правила на уровне модели.
    Приятная привычка не может иметь вознаграждение или связанную привычку.
    """
    pleasant_habit = Habit(owner=user, is_pleasant=True, reward='Отдых')

    # Ожидается ошибка
    with pytest.raises(ValidationError) as excinfo:
        pleasant_habit.full_clean()

    assert 'reward' in str(excinfo.value)

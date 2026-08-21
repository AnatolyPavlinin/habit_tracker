import pytest
from api.models import Habit
from rest_framework.exceptions import ValidationError
from api.serializers import HabitCreateUpdateSerializer


@pytest.mark.django_db
def test_create_illegal_habit():
    """
    Проверка сериализатора: нельзя одновременно указать
    награду и связанную приятную привычку.
    """
    data = {
        "action": "Прогулка",
        "place": "Парк",
        "time": "19:00",
        "is_pleasant": False,
        "related_habit": 1,  # ID приятной привычки
        "reward": "Конфета"
    }

    serializer = HabitCreateUpdateSerializer(data=data)

    # Ожидается ошибка
    with pytest.raises(ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)

        error_keys = list(excinfo.value.detail.keys())
        assert any(key in ['non_field_errors', 'reward', 'related_habit'] for key in error_keys)


@pytest.mark.django_db
def test_serializer_validation(api_client, habit):
    """
    Проверка бизнес-логики сериализатора.
    """
    # Создадим приятную привычку, чтобы она могла быть связанной
    pleasant_habit = Habit.objects.create(
        owner=habit.owner,
        action='Приятная привычка',
        place='Кафе',
        time='17:00',
        is_pleasant=True
    )

    # Данные для новой полезной привычки
    data = {
        "action": "Прогулка",
        "place": "Парк",
        "time": "19:00",
        "is_pleasant": False,
        "related_habit": pleasant_habit.id,   # Связанная приятная
        "reward": "Конфета"                 # И текстовое вознаграждение
    }

    serializer = HabitCreateUpdateSerializer(data=data)

    with pytest.raises(ValidationError) as excinfo:
        serializer.is_valid(raise_exception=True)

    # Ошибка должна быть либо в поле non_field_errors, либо в reward/related_habit
    error_keys = list(excinfo.value.detail.keys())
    assert any(key in ['non_field_errors', 'reward', 'related_habit'] for key in error_keys)

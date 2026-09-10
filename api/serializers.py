from rest_framework import serializers
from .models import CustomUser, Habit
from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "first_name", "last_name")
        read_only_fields = ("id",)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
        )
        Token.objects.create(user=user)  # Создаем токен сразу при регистрации
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для отображения в публичных привычках"""

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")


class HabitCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор с полной бизнес-логикой.
    Используется при POST/PUT/PATCH.
    """

    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ("owner",)

    def validate(self, attrs):
        is_pleasant = attrs.get("is_pleasant")
        reward = attrs.get("reward")
        related_habit = attrs.get("related_habit")  # В DRF это уже объект Habit (или None)
        execution_time = attrs.get("execution_time")
        periodicity = attrs.get("periodicity")

        # Нельзя одновременно награду и связанную привычку
        if related_habit is not None and reward:
            raise serializers.ValidationError("Нельзя одновременно указывать награду и связанную привычку.")

        # У приятной привычки не должно быть ни награды, ни связи
        if is_pleasant and (reward or related_habit is not None):
            raise serializers.ValidationError("У приятной привычки не должно быть награды или связи.")

        # Проверка execution_time
        if execution_time is not None and execution_time > 120:
            raise serializers.ValidationError({"execution_time": "Максимум 120 секунд."})

        # Проверка periodicity
        if periodicity is not None and not (1 <= periodicity <= 7):
            raise serializers.ValidationError({"periodicity": "Допустимо от 1 до 7 дней."})

        return attrs


class HabitListRetrieveSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)

    class Meta:
        model = Habit
        fields = "__all__"  # Выведем все поля модели + связанные данные

    def get_related_habit_data(self, obj):
        if obj.related_habit:
            return {
                "id": obj.related_habit.id,
                "action": obj.related_habit.action,
                "is_pleasant": obj.related_habit.is_pleasant,
            }
        return None

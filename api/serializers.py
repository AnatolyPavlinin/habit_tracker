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

    def validate(self, attrs):
        # Получаем текущий экземпляр (если это обновление)
        instance = self.instance

        # Берём данные либо из запроса, либо из текущего объекта,
        # либо используем дефолтное значение из модели
        is_pleasant = attrs.get(
            "is_pleasant",
            getattr(instance, "is_pleasant", False),
        )
        reward = attrs.get("reward", getattr(instance, "reward", ""))
        related_habit_id = attrs.get(
            "related_habit",
            getattr(instance, "related_habit", None),
        )
        execution_time = attrs.get(
            "execution_time",
            getattr(instance, "execution_time", 120),
        )
        periodicity = attrs.get(
            "periodicity",
            getattr(instance, "periodicity", 1),
        )

        # Проверка связанной привычки
        if related_habit_id:
            try:
                # Мы проверяем именно связанную привычку!
                related_habit = Habit.objects.get(pk=related_habit_id)
                if not related_habit.is_pleasant:
                    raise serializers.ValidationError({"related_habit": "Связанная привычка должна быть приятной."})
            except Habit.DoesNotExist:
                raise serializers.ValidationError({"related_habit": "Привычки с таким ID не существует."})

        # Остальные проверки
        if reward and related_habit_id:
            raise serializers.ValidationError("Нельзя одновременно указывать награду и связанную привычку.")
        if is_pleasant and (reward or related_habit_id):
            raise serializers.ValidationError("У приятной привычки не должно быть награды или связи.")
        if execution_time > 120:
            raise serializers.ValidationError({"execution_time": "Максимум 120 секунд."})
        if not 1 <= periodicity <= 7:
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

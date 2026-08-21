from rest_framework import serializers
from .models import CustomUser, Habit
from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        Token.objects.create(user=user)  # Создаем токен сразу при регистрации
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для отображения в публичных привычках"""

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name')


class HabitCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления.
    related_habit принимает ID приятной привычки."""

    class Meta:
        model = Habit
        fields = (
            'place', 'time', 'action', 'is_pleasant', 'related_habit',
            'periodicity', 'reward', 'execution_time', 'is_public'
        )

    def validate(self, attrs):
        # Дублируем серверную валидацию на уровне API для понятных ошибок фронтенду
        is_pleasant = attrs.get('is_pleasant', False)
        reward = attrs.get('reward')
        related_habit = attrs.get('related_habit')

        if is_pleasant and (reward or related_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки."
            )

        if not is_pleasant and reward and related_habit:
            raise serializers.ValidationError(
                "Нельзя одновременно указывать вознаграждение и связанную приятную привычку."
            )

        if attrs.get('execution_time') > 120:
            raise serializers.ValidationError({'execution_time': 'Время выполнения не может превышать 120 секунд.'})

        if attrs.get('periodicity') > 7:
            raise serializers.ValidationError({'periodicity': 'Периодичность не может быть больше 7 дней.'})

        return attrs


class HabitListRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода списка и деталей.
    Поля:
    - place: Место выполнения
    - time: Время выполнения (HH:MM)
    - action: Действие (что именно нужно сделать)
    - is_pleasant: Является ли эта привычка "приятной" (вознаграждение)
    - related_habit_data: Связанная приятная привычка (если выбрано)
    - periodicity: Периодичность напоминания в днях
    - reward: Текст вознаграждения
    - execution_time: Максимальное время выполнения (в секундах; <= 120)
    - is_public: Публичность привычки
    """
    owner = UserPublicSerializer(read_only=True)
    related_habit_data = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = '__all__'  # Выведем все поля модели + связанные данные

    def get_related_habit_data(self, obj):
        if obj.related_habit:
            return {
                'id': obj.related_habit.id,
                'action': obj.related_habit.action,
                'is_pleasant': obj.related_habit.is_pleasant
            }
        return None
    
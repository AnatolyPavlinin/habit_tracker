from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager


class Habit(models.Model):
    # Типы привычек
    USEFUL = 'useful'
    PLEASANT = 'pleasant'
    HABIT_TYPE_CHOICES = [
        (USEFUL, 'Полезная'),
        (PLEASANT, 'Приятная'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
        verbose_name='Пользователь'
    )
    place = models.CharField(max_length=255, verbose_name='Место')
    time = models.TimeField(verbose_name='Время выполнения')
    action = models.CharField(max_length=255, verbose_name='Действие')
    is_pleasant = models.BooleanField(default=False, verbose_name='Признак приятной привычки')

    # Связанная привычка (только если текущая - полезная, а связанная - приятная)
    related_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_to',
        limit_choices_to={'is_pleasant': True},
        verbose_name='Связанная привычка'
    )

    periodicity = models.PositiveIntegerField(
        default=1,
        verbose_name='Периодичность (в днях)',
        help_text='Через сколько дней повторять. Минимум 1.'
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Вознаграждение'
    )
    execution_time = models.PositiveSmallIntegerField(
        default=120,
        verbose_name='Время на выполнение (сек)'
    )
    is_public = models.BooleanField(default=False, verbose_name='Публичная привычка')

    class Meta:
        ordering = ['-time']
        constraints = [
            # Валидатор: нельзя одновременно указать связанную привычку и вознаграждение
            models.CheckConstraint(
                condition=~(
                        Q(related_habit__isnull=False) &
                        (
                                Q(reward__isnull=False) |
                                ~Q(reward='')
                        )
                ),
                name='no_reward_and_related_habit'
            ),
            # Время выполнения не больше 120 секунд
            models.CheckConstraint(
                condition=models.Q(execution_time__lte=120),
                name='execution_time_lte_120'
            ),
            # Нельзя выполнять реже раза в неделю (periodicity <= 7)
            models.CheckConstraint(
                condition=models.Q(periodicity__lte=7),
                name='periodicity_lte_7'
            )
        ]
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'

    def __str__(self):
        return f'{self.action} в {self.time} в {self.place}'

    def clean(self):
        super().clean()

        # Серверный валидатор: у приятной привычки нет вознаграждения и связанных привычек
        if self.is_pleasant:
            if self.reward:
                raise ValidationError({'reward': 'У приятной привычки не может быть вознаграждения.'})
            if self.related_habit:
                raise ValidationError({'related_habit': 'У приятной привычки не может быть связанной привычки.'})

        # У полезной привычки должна быть либо связь, либо вознаграждение (или ничего, если это просто действие)
        if not self.is_pleasant:
            if not self.related_habit and not self.reward:
                # По ТЗ допускается отсутствие обоих полей, так как наградой может быть что-то внешнее
                pass

    def save(self, *args, **kwargs):
        self.full_clean()  # Автоматический вызов clean при сохранении
        super().save(*args, **kwargs)


class CustomUserManager(BaseUserManager):
    """
    Менеджер для нашей модели пользователя.
    Здесь мы переписываем методы create_user и create_superuser,
    чтобы они работали с email вместо username.
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')

        # Приводим почту к нижнему регистру (стандарт безопасности)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # Удаляем стандартное поле username
    email = models.EmailField(unique=True, verbose_name='Email')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

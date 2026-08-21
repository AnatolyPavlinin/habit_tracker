from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from api.models import Habit


@receiver(post_save, sender=Habit)
def create_or_update_habit_schedule(sender, instance, created, **kwargs):
    """
    При создании или обновлении привычки пересоздаем её напоминание в Celery Beat.
    """
    # Генерируем уникальное имя задачи, привязанное к ID привычки
    task_name = f"habit_reminder_{instance.id}"

    # Удаляем старую задачу с таким же именем, если она была (при редактировании привычки)
    PeriodicTask.objects.filter(name=task_name).delete()

    # Если привычка удалена или помечена как неактивная (если добавите такое поле), выходим
    if not instance.is_public and instance.owner != instance.owner:  # заглушка для логики удаления
        return

    # Определяем интервал из поля periodicity (в днях)
    schedule, _ = IntervalSchedule.objects.get_or_create(every=instance.periodicity, period=IntervalSchedule.DAYS)

    # Создаем новую периодическую задачу
    PeriodicTask.objects.create(
        interval=schedule,
        name=task_name,
        task="api.tasks.send_telegram_notification",  # Путь к нашей задаче
        args=[str(instance.id)],  # Передаем ID привычки в аргументы функции
        start_time=timezone.now(),  # Начинаем прямо сейчас
        enabled=True,
    )

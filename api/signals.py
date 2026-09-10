import json

from config import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from api.models import Habit


@receiver(post_save, sender=Habit)
def create_or_update_habit_schedule(sender, instance, created, **kwargs):
    """Создаёт задачу напоминания."""

    task_name = f"habit_reminder_{instance.pk}"

    # Удаляем старую задачу, чтобы избежать дублирования
    PeriodicTask.objects.filter(name=task_name).delete()

    # Если привычка удалена или скрыта, ничего не создаем
    if not instance.is_public and instance.owner != instance.owner:
        return

    # Привязываем уведомление строго ко времени привычки через crontab
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(instance.time.minute),
        hour=str(instance.time.hour),
        day_of_week="*",  # Каждый день недели
        timezone=settings.TIME_ZONE,
    )

    args_json = json.dumps([str(instance.id)])

    # Создаём новую периодическую задачу
    PeriodicTask.objects.create(
        name=task_name,
        crontab=schedule,
        interval=None,
        task="api.tasks.send_telegram_notification",
        args=args_json,
        enabled=True,
    )


@receiver(post_delete, sender=Habit)
def delete_habit_task(sender, instance, **kwargs):
    """Удаляет задачу при удалении привычки."""
    task_name = f"habit_reminder_{instance.pk}"
    PeriodicTask.objects.filter(name=task_name).delete()

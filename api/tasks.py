import os
import requests
from celery import shared_task
from api.models import Habit


@shared_task(name='send_telegram_notification')
def send_telegram_notification(habit_id):
    """
    Задача Celery для отправки уведомления пользователю в Telegram 
    через прямой запрос к Bot API.
    """
    try:
        habit = Habit.objects.get(id=habit_id)

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

        # Проверяем наличие токена бота и ID чата пользователя
        if not bot_token or not getattr(habit.owner, 'telegram_chat_id', None):
            return

        message_text = (
            f"⏰ Время привычки!\n\n"
            f"Я буду {habit.action} в {habit.place}.\n"
            f"Время: {habit.time.strftime('%H:%M')}"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            'chat_id': habit.owner.telegram_chat_id,
            'text': message_text,
            'parse_mode': 'HTML'  # Позволяет использовать жирный шрифт и теги, если захотите
        }

        # Отправляем синхронный POST-запрос
        response = requests.post(url, json=payload, timeout=10)

        # Если сервер вернул ошибку (например, бот заблокирован), выведем её в лог
        response.raise_for_status()

    except Habit.DoesNotExist:
        pass
    except Exception as e:
        print(f"[Celery Task Error] Не удалось отправить уведомление для привычки #{habit_id}: {e}")

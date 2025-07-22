import requests

from gosconnect import settings


class Telegram:
    def send_captcha_to_telegram(self, img_url: str, solving_id: str):
        """
        Скачивает изображение по URL и отправляет его в Telegram через бота.
        """
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not bot_token or not chat_id:
            raise Exception(
                "TELEGRAM_BOT_TOKEN и/или TELEGRAM_CHAT_ID не заданы в .env или переменных окружения"
            )

        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        # Скачиваем изображение.
        response_img = requests.get(img_url)
        response_img.raise_for_status()
        files = {"photo": ("captcha.jpg", response_img.content)}
        caption = (
            f"[CaptchaRequest #{solving_id}]\nПожалуйста, введите текст с картинки."
        )
        data = {"chat_id": chat_id, "caption": caption}
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()

    def send_2fa_petition(self, request_id: str):
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not bot_token or not chat_id:
            raise Exception(
                "TELEGRAM_BOT_TOKEN и/или TELEGRAM_CHAT_ID не заданы в .env или переменных окружения"
            )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        text = (
            f"[TwoFactorRequest #{request_id}]\n"
            "Пожалуйста, введите код из СМС для входа."
        )
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, data=data)
        response.raise_for_status()

    def poll_and_process_updates(self, offset=None):
        """
        Периодически опрашивает Telegram Bot API на новые сообщения, ищет ответы на сообщения бота,
        определяет тип сущности по заголовку и обновляет соответствующую запись.
        """
        from etk_retriever.models import CaptchaSolving, SecondFactorRequest

        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            raise Exception(
                "TELEGRAM_BOT_TOKEN не заданы в .env или переменных окружения"
            )

        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            return
        for update in data.get("result", []):
            message = update.get("message")
            if not message:
                continue
            reply_to = message.get("reply_to_message")
            if not reply_to:
                continue
            # Определяем тип запроса по заголовку исходного сообщения бота
            text = reply_to.get("text") or reply_to.get("caption")
            if not text:
                continue
            if text.startswith("[CaptchaRequest #"):
                # Извлекаем ID
                import re

                m = re.match(r"\[CaptchaRequest #(\d+)]", text)
                if m:
                    solving_id = m.group(1)
                    try:
                        captcha = CaptchaSolving.objects.get(id=solving_id)
                        captcha.solved_text = message.get("text", "")
                        captcha.is_solved = True
                        captcha.save(update_fields=["solved_text", "is_solved"])
                    except CaptchaSolving.DoesNotExist:
                        pass
            elif text.startswith("[TwoFactorRequest #"):
                import re

                m = re.match(r"\[TwoFactorRequest #(\d+)]", text)
                if m:
                    request_id = m.group(1)
                    try:
                        req = SecondFactorRequest.objects.get(id=request_id)
                        req.second_factor = message.get("text", "")
                        req.is_captured = True
                        req.save(update_fields=["second_factor", "is_captured"])
                    except SecondFactorRequest.DoesNotExist:
                        pass
        # Возвращаем последний offset для продолжения
        if data.get("result"):
            return data["result"][-1]["update_id"] + 1
        return offset

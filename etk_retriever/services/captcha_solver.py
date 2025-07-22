import time

from etk_retriever import tasks
from etk_retriever.models import CaptchaSolving, Credentials


class CaptchaSolvingTimeout(Exception):
    """Исключение для таймаута решения капчи"""

    pass


class CaptchaSolver:
    # Секунды.
    POLL_INTERVAL = 2
    # Секунды.
    TIMEOUT = 60

    def set_captcha_to_solve(self, img_url: str, creds: Credentials, session_id: str):
        record = CaptchaSolving.objects.create(
            session_id=session_id,
            credentials=creds,
            img_url=img_url,
        )
        tasks.send_captcha.apply_async(args=[record.id], queue="send_to_telegram")
        return record.id

    def is_captcha_solved(self, captcha_id: int) -> bool:
        try:
            captcha = CaptchaSolving.objects.get(id=captcha_id)
            return captcha.is_solved
        except CaptchaSolving.DoesNotExist:
            return False

    def wait_for_captcha_solution(
        self,
        captcha_id: int,
    ):
        waited = 0
        while waited < self.TIMEOUT:
            if self.is_captcha_solved(captcha_id):
                return
            time.sleep(self.POLL_INTERVAL)
            waited += self.POLL_INTERVAL
        raise CaptchaSolvingTimeout("Капча не была решена за 60 секунд")

    def get_captcha_text(self, captcha_id: int) -> str:
        """Возвращает текст решённой капчи по её ID. Бросает исключение, если не решена."""
        captcha = CaptchaSolving.objects.get(id=captcha_id)
        if not captcha.is_solved:
            raise CaptchaSolvingTimeout("Капча ещё не решена")
        return captcha.solved_text

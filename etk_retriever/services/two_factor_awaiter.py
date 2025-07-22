import time

from etk_retriever import tasks
from etk_retriever.models import Credentials, SecondFactorRequest


class TwoFactorAwaitTimeout(Exception):
    pass


class TwoFactorAwaiter:
    POLL_INTERVAL = 2  # seconds
    TIMEOUT = 60  # seconds

    def set_second_factor_to_capture(self, creds: Credentials, session_id: str):
        record = SecondFactorRequest.objects.create(
            session_id=session_id,
            credentials=creds,
        )
        tasks.send_second_factor_request.apply_async(
            args=[record.id], queue="send_to_telegram"
        )
        return record.id

    def is_second_factor_captured(self, factor_request_id: int) -> bool:
        try:
            request = SecondFactorRequest.objects.get(id=factor_request_id)
            return request.is_captured
        except SecondFactorRequest.DoesNotExist:
            return False

    def get_second_factor(self, factor_request_id: int) -> str:
        """Возвращает текст второго фактора по его ID. Бросает исключение, если не введён."""
        factor = SecondFactorRequest.objects.get(id=factor_request_id)
        if not factor.is_captured:
            raise TwoFactorAwaitTimeout("Второй фактор ещё не введён")
        return factor.second_factor

    def wait_for_second_factor_capture(
        self,
        captcha_id: int,
    ):
        waited = 0
        while waited < self.TIMEOUT:
            if self.is_second_factor_captured(captcha_id):
                return
            time.sleep(self.POLL_INTERVAL)
            waited += self.POLL_INTERVAL
        raise TwoFactorAwaitTimeout("Капча не была решена за 60 секунд")

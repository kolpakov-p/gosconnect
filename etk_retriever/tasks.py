from celery import shared_task

from etk_retriever.models import CaptchaSolving, SecondFactorRequest
from etk_retriever.services.etk_retriever import EtkRetriever
from etk_retriever.services.telegram import Telegram


@shared_task(queue="request_etk_statement")
def async_request_etk_statement():
    retriever = EtkRetriever()
    retriever.request_etk_statement()


@shared_task(queue="send_to_telegram")
def send_captcha(captcha_id: str):
    captcha = CaptchaSolving.objects.get(id=captcha_id)
    Telegram().send_captcha_to_telegram(captcha.img_url, captcha_id)


@shared_task(queue="send_to_telegram")
def send_second_factor_request(factor_request_id: str):
    request = SecondFactorRequest.objects.get(id=factor_request_id)
    Telegram().send_2fa_petition(factor_request_id)


@shared_task
def poll_telegram_updates():
    telegram = Telegram()
    telegram.poll_and_process_updates()

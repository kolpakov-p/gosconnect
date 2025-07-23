from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

from etk_retriever.tasks import async_request_etk_statement
from gosconnect import settings


def retrieve_etk(request):
    try:
        async_request_etk_statement.apply_async()
        return JsonResponse({"status": "ok", "message": "Задача поставлена в очередь"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)


def db_healthcheck(request):
    try:
        connections["default"].cursor()
        return JsonResponse({"status": "ok"})
    except OperationalError:
        return JsonResponse(
            {"status": "error", "config": settings.DATABASES["default"]}, status=500
        )

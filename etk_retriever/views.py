from django.http import JsonResponse

from etk_retriever.tasks import async_request_etk_statement


def retrieve_etk(request):
    try:
        async_request_etk_statement.apply_async()
        return JsonResponse({"status": "ok", "message": "Задача поставлена в очередь"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

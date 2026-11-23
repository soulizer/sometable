import logging

from django.http import JsonResponse
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

MAX_DETAIL_LENGTH = 2000


def baserow_exception_handler(exc, context):
    """
    Return a JSON error body for every API failure, including exceptions that
    DRF does not know about.

    DRF's default handler returns ``None`` for unhandled server errors, which
    makes Django fall back to an HTML 500 page. The frontend then has no error
    code or detail to show and users only see "unknown error". Log the full
    traceback server-side and return the exception type and message so the
    client can display actionable diagnostics.
    """

    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    request = context.get('request')
    logger.exception('Unhandled exception while processing API request')

    body = {
        'error': 'ERROR_INTERNAL_SERVER_ERROR',
        'detail': f'{type(exc).__name__}: {exc}'[:MAX_DETAIL_LENGTH],
    }
    if request is not None:
        body['path'] = request.path

    return JsonResponse(body, status=500)

import json

from rest_framework.exceptions import APIException
from rest_framework.test import APIRequestFactory

from baserow.api.handler import baserow_exception_handler


def test_unhandled_exception_returns_json_with_diagnostic_detail():
    request = APIRequestFactory().get('/api/settings/backups/')

    response = baserow_exception_handler(
        RuntimeError('disk is full'), {'request': request}
    )

    assert response.status_code == 500
    assert response['Content-Type'].startswith('application/json')
    body = json.loads(response.content)
    assert body['error'] == 'ERROR_INTERNAL_SERVER_ERROR'
    assert body['detail'] == 'RuntimeError: disk is full'
    assert body['path'] == '/api/settings/backups/'


def test_known_api_exception_is_handled_by_drf():
    request = APIRequestFactory().get('/api/settings/backups/')
    exception = APIException('nope')

    response = baserow_exception_handler(exception, {'request': request})

    assert response.status_code == 500
    assert response.data['detail'] == 'nope'

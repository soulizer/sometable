from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.api_rows
def test_deduplicate_preview_and_delete(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, name="Key")
    model = table.get_model()
    field_name = f"field_{field.id}"
    rows = [
        model.objects.create(**{field_name: "A"}),
        model.objects.create(**{field_name: "A"}),
        model.objects.create(**{field_name: "A"}),
        model.objects.create(**{field_name: "B"}),
    ]

    preview_url = reverse(
        "api:database:rows:deduplicate-preview",
        kwargs={"table_id": table.id},
    )
    response = api_client.post(
        preview_url,
        {"field_ids": [field.id]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["total_groups"] == 1
    assert data["groups"][0]["row_count"] == 3
    assert data["groups"][0]["keep_id"] == rows[0].id

    url = reverse(
        "api:database:rows:deduplicate", kwargs={"table_id": table.id}
    )
    response = api_client.post(
        url,
        {"field_ids": [field.id], "rule": "oldest"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["deleted_count"] == 2

    for row in rows:
        row.refresh_from_db()
    assert rows[0].trashed is False
    assert rows[1].trashed is True
    assert rows[2].trashed is True
    assert rows[3].trashed is False


@pytest.mark.django_db
@pytest.mark.api_rows
def test_deduplicate_manual_requires_a_keep_row(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, name="Key")
    model = table.get_model()
    field_name = f"field_{field.id}"
    model.objects.create(**{field_name: "A"})
    model.objects.create(**{field_name: "A"})

    url = reverse(
        "api:database:rows:deduplicate", kwargs={"table_id": table.id}
    )
    response = api_client.post(
        url,
        {"field_ids": [field.id], "rule": "manual", "keep_row_ids": {}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_DEDUPE_MANUAL_KEEP_MISSING"

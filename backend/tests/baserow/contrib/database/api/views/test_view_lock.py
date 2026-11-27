from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED


@pytest.mark.django_db(transaction=True)
def test_locked_view_is_read_only_for_non_owners(api_client, data_fixture):
    owner, owner_token = data_fixture.create_user_and_token()
    other_user, other_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=owner)
    data_fixture.create_user_workspace(
        workspace=table.database.workspace, user=other_user, permissions="MEMBER"
    )
    view = data_fixture.create_grid_view(
        table=table, user=owner, owned_by=owner, locked=True
    )

    url = reverse("api:database:views:item", kwargs={"view_id": view.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {other_token}")
    assert response.status_code == HTTP_200_OK
    assert response.json()["locked"] is True

    response = api_client.patch(
        url,
        {"name": "Should not change"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    view.refresh_from_db()
    assert view.name != "Should not change"

    rows_url = reverse("api:database:rows:list", kwargs={"table_id": table.id})
    response = api_client.post(
        f"{rows_url}?view={view.id}",
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED

    response = api_client.post(
        f"{rows_url}?view={view.id}",
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {owner_token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db(transaction=True)
def test_locked_view_can_be_unlocked_by_owner_and_staff(api_client, data_fixture):
    owner, owner_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    table = data_fixture.create_database_table(user=owner)
    data_fixture.create_user_workspace(
        workspace=table.database.workspace, user=staff_user, permissions="MEMBER"
    )
    view = data_fixture.create_grid_view(
        table=table, user=owner, owned_by=owner, locked=True
    )
    url = reverse("api:database:views:item", kwargs={"view_id": view.id})

    response = api_client.patch(
        url,
        {"locked": False},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {owner_token}",
    )
    assert response.status_code == HTTP_200_OK
    view.refresh_from_db()
    assert view.locked is False

    view.locked = True
    view.save(update_fields=["locked"])
    response = api_client.patch(
        url,
        {"locked": False},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_200_OK
    view.refresh_from_db()
    assert view.locked is False

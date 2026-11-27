from django.shortcuts import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)


@pytest.mark.workspace_search
@pytest.mark.django_db
def test_global_search_requires_authentication(api_client):
    response = api_client.get(reverse("api:search:global_search"), {"query": "test"})

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.workspace_search
@pytest.mark.django_db
def test_global_search_rejects_missing_or_empty_query(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token()
    url = reverse("api:search:global_search")

    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"

    response = api_client.get(
        url, {"query": ""}, HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"


@pytest.mark.workspace_search
@pytest.mark.django_db(transaction=True)
def test_global_search_only_searches_permitted_workspaces(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    allowed_workspace = data_fixture.create_workspace(
        name="Allowed workspace", user=user
    )
    denied_workspace = data_fixture.create_workspace(name="Denied workspace")
    data_fixture.create_database_application(
        workspace=allowed_workspace, name="Needle allowed database"
    )
    data_fixture.create_database_application(
        workspace=denied_workspace, name="Needle denied database"
    )

    # A client supplied workspace id must not grant access to another workspace.
    response = api_client.get(
        reverse("api:search:global_search"),
        {"query": "Needle", "workspace_id": denied_workspace.id},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Needle allowed database"
    assert results[0]["metadata"]["workspace_id"] == allowed_workspace.id


@pytest.mark.workspace_search
@pytest.mark.django_db
def test_global_search_merges_results_caps_limit_and_adds_workspace_id(
    api_client, data_fixture, mocker
):
    user, token = data_fixture.create_user_and_token()
    first_workspace = data_fixture.create_workspace(user=user)
    second_workspace = data_fixture.create_workspace(user=user)

    def fake_search_workspace(
        self, user, workspace, query, limit, offset=0, types=None
    ):
        if workspace.id == first_workspace.id:
            results = [
                {"type": "database", "id": index + 1, "title": f"first-{index}"}
                for index in range(3)
            ]
        else:
            results = [
                {
                    "type": "database",
                    "id": 10,
                    "title": "second",
                    "metadata": {"workspace_name": second_workspace.name},
                }
            ]
        return {"results": results, "has_more": False}

    mocker.patch(
        "baserow.api.search.views.WorkspaceSearchHandler.search_workspace",
        new=fake_search_workspace,
    )

    url = reverse("api:search:global_search")
    response = api_client.get(
        url, {"query": "needle", "limit": 4}, HTTP_AUTHORIZATION=f"JWT {token}"
    )

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["count"] == 4
    assert [result["title"] for result in data["results"]] == [
        "first-0",
        "first-1",
        "first-2",
        "second",
    ]
    assert all(
        result["metadata"]["workspace_id"] == first_workspace.id
        for result in data["results"][:3]
    )
    assert data["results"][3]["metadata"] == {
        "workspace_name": second_workspace.name,
        "workspace_id": second_workspace.id,
    }

    response = api_client.get(
        url, {"query": "needle", "limit": 2}, HTTP_AUTHORIZATION=f"JWT {token}"
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 2
    assert len(response.json()["results"]) == 2

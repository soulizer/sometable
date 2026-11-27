from datetime import datetime, timezone

from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.core.handler import CoreHandler
from baserow.core.job_types import ExportApplicationsJobType
from baserow.core.models import ExportApplicationsJob, Workspace, WorkspaceUser


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_admin_workspaces(api_client, data_fixture, django_assert_num_queries):
    """
    This endpoint doesn't need to be tested extensively because it uses the same base
    class as the list users endpoint which already has extensive tests. We only need to
    test if the functionality works in a basic form.
    """

    created = datetime(2020, 4, 10, 0, 0, 0).replace(tzinfo=timezone.utc)
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    normal_user, normal_token = data_fixture.create_user_and_token()
    workspace_1 = data_fixture.create_workspace(name="A")
    workspace_1.created_on = created
    workspace_1.save()
    workspace_2 = data_fixture.create_workspace(name="B", created_on=created)
    workspace_2.created_on = created
    workspace_2.save()
    template_workspace = data_fixture.create_workspace(
        name="Template", created_on=created
    )
    data_fixture.create_template(workspace=template_workspace)
    data_fixture.create_user_workspace(
        workspace=workspace_1, user=normal_user, permissions="MEMBER"
    )
    data_fixture.create_user_workspace(
        workspace=workspace_2, user=normal_user, permissions="ADMIN"
    )
    data_fixture.create_database_application(workspace=workspace_1)
    data_fixture.create_database_application(workspace=workspace_1)

    response = api_client.get(
        reverse("api:admin:workspaces:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {normal_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    with django_assert_num_queries(4):
        response = api_client.get(
            reverse("api:admin:workspaces:list"),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {staff_token}",
        )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": workspace_2.id,
                "name": workspace_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 0,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f"{reverse('api:admin:workspaces:list')}?search={workspace_1.name}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f"{reverse('api:admin:workspaces:list')}?sorts=-name",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_2.id,
                "name": workspace_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 0,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }


@pytest.mark.django_db
def test_admin_workspace_users_and_free_seats_exclude_identities(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace(user=user, seats_taken=1)
    data_fixture.create_identity(workspace=workspace, role_uid="ADMIN")

    response = api_client.get(
        reverse("api:admin:workspaces:list"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    result = response.json()["results"][0]
    assert result["id"] == workspace.id
    assert result["free_users"] == 0
    assert result["users"] == [
        {"id": user.id, "email": user.email, "permissions": "ADMIN"}
    ]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_delete_workspace(api_client, data_fixture):
    normal_user, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace()

    url = reverse("api:admin:workspaces:edit", kwargs={"workspace_id": 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    url = reverse("api:admin:workspaces:edit", kwargs={"workspace_id": workspace.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {normal_token}")
    assert response.status_code == HTTP_403_FORBIDDEN

    url = reverse("api:admin:workspaces:edit", kwargs={"workspace_id": workspace.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == 204
    assert Workspace.objects.all().count() == 0


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_delete_template_workspace(api_client, data_fixture):
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace()
    data_fixture.create_template(workspace=workspace)

    url = reverse("api:admin:workspaces:edit", kwargs={"workspace_id": workspace.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP"
    assert Workspace.objects.all().count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_list_workspaces_as_options(api_client, data_fixture):
    (
        admin_user,
        admin_token,
    ) = data_fixture.create_user_and_token()

    # no search query should return all workspaces
    response = api_client.get(
        reverse("api:admin:workspaces:options"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_list_workspaces_as_options(api_client, data_fixture):
    (
        admin_user,
        admin_token,
    ) = data_fixture.create_user_and_token(is_staff=True)
    workspace_1 = data_fixture.create_workspace(name="workspace 1", user=admin_user)
    workspace_2 = data_fixture.create_workspace(name="workspace 2", user=admin_user)

    # no search query should return all workspaces
    response = api_client.get(
        reverse("api:admin:workspaces:options"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {"id": workspace_1.id, "value": workspace_1.name},
            {"id": workspace_2.id, "value": workspace_2.name},
        ],
    }

    # searching by name should return only the correct workspace
    response = api_client.get(
        reverse("api:admin:workspaces:options") + "?search=workspace 1",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": workspace_1.id, "value": workspace_1.name}],
    }

    response = api_client.get(
        reverse("api:admin:workspaces:options") + f"?search={workspace_2.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["results"] == [
        {"id": workspace_2.id, "value": workspace_2.name}
    ]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_list_workspaces_as_options_filter_by_ids(api_client, data_fixture):
    (
        admin_user,
        admin_token,
    ) = data_fixture.create_user_and_token(is_staff=True)
    workspace_1 = data_fixture.create_workspace(name="workspace 1", user=admin_user)
    workspace_2 = data_fixture.create_workspace(name="workspace 2", user=admin_user)
    data_fixture.create_workspace(name="workspace 3", user=admin_user)

    # filtering by a single id should return only that workspace
    response = api_client.get(
        reverse("api:admin:workspaces:options") + f"?ids={workspace_1.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"id": workspace_1.id, "value": workspace_1.name}],
    }

    # filtering by multiple ids should return all matching workspaces
    response = api_client.get(
        reverse("api:admin:workspaces:options")
        + f"?ids={workspace_1.id},{workspace_2.id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {"id": workspace_1.id, "value": workspace_1.name},
            {"id": workspace_2.id, "value": workspace_2.name},
        ],
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_list_workspaces_as_options_filter_by_invalid_ids(
    api_client, data_fixture
):
    _, admin_token = data_fixture.create_user_and_token(is_staff=True)

    # Negative IDs should be rejected.
    response = api_client.get(
        reverse("api:admin:workspaces:options") + "?ids=-1",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert response.json()["detail"]["ids"] == [
        {
            "code": "invalid",
            "error": "'-1' is not a valid ID. Only positive integers are accepted.",
        }
    ]

    # Non-numeric values should be rejected.
    response = api_client.get(
        reverse("api:admin:workspaces:options") + "?ids=abc",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert response.json()["detail"]["ids"] == [
        {
            "code": "invalid",
            "error": "'abc' is not a valid ID. Only positive integers are accepted.",
        }
    ]

    # A mix of valid and invalid values should still be rejected.
    response = api_client.get(
        reverse("api:admin:workspaces:options") + "?ids=1,-2,3",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert response.json()["detail"]["ids"] == [
        {
            "code": "invalid",
            "error": "'-2' is not a valid ID. Only positive integers are accepted.",
        }
    ]

    # Newline in ids should return 400, not 500.
    response = api_client.get(
        reverse("api:admin:workspaces:options") + "?ids=1%0A2",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"


@pytest.mark.django_db
def test_workspace_options_use_the_estimated_count(api_client, data_fixture, mocker):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    workspaces = [
        data_fixture.create_workspace(name=f"workspace {i:03}") for i in range(101)
    ]
    template_workspace = data_fixture.create_workspace(name="workspace 000 template")
    data_fixture.create_template(workspace=template_workspace)
    data_fixture.create_workspace(name="workspace 000 trashed", trashed=True)
    estimate = mocker.patch(
        "baserow.api.pagination.get_approximate_row_count", return_value=100_000
    )
    response = api_client.get(
        reverse("api:admin:workspaces:options"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 100_000
    assert response.json()["next"] is not None
    assert response.json()["previous"] is None
    assert response.json()["results"] == [
        {"id": workspace.id, "value": workspace.name} for workspace in workspaces[:100]
    ]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_list_workspace_members_is_staff_only(api_client, data_fixture):
    _, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    member = data_fixture.create_user(email="member@example.com")
    workspace = data_fixture.create_workspace()
    membership = data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )

    url = reverse(
        "api:admin:workspaces:members", kwargs={"workspace_id": workspace.id}
    )
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {normal_token}")
    assert response.status_code == HTTP_403_FORBIDDEN

    # The staff user does not need to be a workspace member.
    response = api_client.get(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 1
    result = response.json()["results"][0]
    assert result["id"] == membership.id
    assert result["user_id"] == member.id
    assert result["email"] == member.email
    assert result["permissions"] == "MEMBER"
    assert result["role_uid"] == CoreHandler().get_workspace_user_role_uid(membership)
    assert result["created_on"] is not None

    response = api_client.get(
        reverse("api:admin:workspaces:members", kwargs={"workspace_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_update_workspace_member_role_and_guards(api_client, data_fixture):
    _, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    member = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    membership = data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )
    url = reverse(
        "api:admin:workspaces:edit-member",
        kwargs={"workspace_id": workspace.id, "member_id": membership.id},
    )

    response = api_client.patch(
        url,
        {"permissions": "ADMIN"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {normal_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.patch(
        url,
        {"permissions": "ADMIN"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["permissions"] == "ADMIN"
    assert response.json()["role_uid"] == "ADMIN"
    membership.refresh_from_db()
    assert membership.permissions == "ADMIN"

    response = api_client.patch(
        url,
        {"permissions": "INVALID"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_WORKSPACE_ROLE"

    # The last admin of a workspace cannot be demoted.
    admin = data_fixture.create_user()
    last_admin_workspace = data_fixture.create_workspace(user=admin)
    last_admin_membership = WorkspaceUser.objects.get(
        workspace=last_admin_workspace, user=admin
    )
    response = api_client.patch(
        reverse(
            "api:admin:workspaces:edit-member",
            kwargs={
                "workspace_id": last_admin_workspace.id,
                "member_id": last_admin_membership.id,
            },
        ),
        {"permissions": "MEMBER"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_GROUP_USER_IS_LAST_ADMIN"

    # Staff cannot change their own role, even from the admin area.
    own_workspace = data_fixture.create_workspace(user=staff_user)
    own_membership = WorkspaceUser.objects.get(
        workspace=own_workspace, user=staff_user
    )
    response = api_client.patch(
        reverse(
            "api:admin:workspaces:edit-member",
            kwargs={
                "workspace_id": own_workspace.id,
                "member_id": own_membership.id,
            },
        ),
        {"permissions": "MEMBER"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_CHANGE_YOUR_OWN_ROLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_delete_workspace_member_and_guards(api_client, data_fixture):
    _, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    member = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    membership = data_fixture.create_user_workspace(
        workspace=workspace, user=member, permissions="MEMBER"
    )
    url = reverse(
        "api:admin:workspaces:edit-member",
        kwargs={"workspace_id": workspace.id, "member_id": membership.id},
    )

    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {normal_token}")
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_204_NO_CONTENT
    assert not WorkspaceUser.objects.filter(id=membership.id).exists()

    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_USER_DOES_NOT_EXIST"

    # The last admin cannot be removed.
    admin = data_fixture.create_user()
    last_admin_workspace = data_fixture.create_workspace(user=admin)
    last_admin_membership = WorkspaceUser.objects.get(
        workspace=last_admin_workspace, user=admin
    )
    response = api_client.delete(
        reverse(
            "api:admin:workspaces:edit-member",
            kwargs={
                "workspace_id": last_admin_workspace.id,
                "member_id": last_admin_membership.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_GROUP_USER_IS_LAST_ADMIN"

    # Staff cannot remove themselves from a workspace.
    own_workspace = data_fixture.create_workspace(user=staff_user)
    own_membership = WorkspaceUser.objects.get(
        workspace=own_workspace, user=staff_user
    )
    response = api_client.delete(
        reverse(
            "api:admin:workspaces:edit-member",
            kwargs={
                "workspace_id": own_workspace.id,
                "member_id": own_membership.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_YOURSELF_FROM_GROUP"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_export_workspace_async_is_staff_only(api_client, data_fixture):
    _, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    workspace = data_fixture.create_workspace()
    application = data_fixture.create_database_application(workspace=workspace)
    url = reverse(
        "api:admin:workspaces:export-async", kwargs={"workspace_id": workspace.id}
    )

    response = api_client.post(
        url, {}, format="json", HTTP_AUTHORIZATION=f"JWT {normal_token}"
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.post(
        url,
        {"application_ids": [application.id], "only_structure": True},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_202_ACCEPTED
    assert response.json()["type"] == ExportApplicationsJobType.type
    job = ExportApplicationsJob.objects.get(id=response.json()["id"])
    assert job.user_id == staff_user.id
    assert job.workspace_id == workspace.id
    assert job.application_ids == [application.id]
    assert job.only_structure is True

    # A staff user who is not a workspace member can still fetch the applications.
    applications = ExportApplicationsJobType().fetch_applications(
        staff_user, workspace, [application.id]
    )
    assert [app.id for app in applications] == [application.id]

    response = api_client.post(
        reverse("api:admin:workspaces:export-async", kwargs={"workspace_id": 99999}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

from django.contrib.auth import get_user_model

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace, WorkspaceUser

User = get_user_model()


class AdminWorkspaceMemberSerializer(ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    role_uid = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceUser
        fields = ("id", "user_id", "email", "permissions", "role_uid", "created_on")

    @extend_schema_field(OpenApiTypes.STR)
    def get_role_uid(self, instance):
        return CoreHandler().get_workspace_user_role_uid(instance)


class AdminWorkspaceMemberUpdateSerializer(serializers.Serializer):
    permissions = serializers.CharField(max_length=32)


class WorkspaceAdminUsersSerializer(ModelSerializer):
    id = serializers.IntegerField(source="user.id")
    email = serializers.CharField(source="user.email")

    class Meta:
        model = WorkspaceUser

        fields = ("id", "email", "permissions")


class WorkspacesAdminResponseSerializer(ModelSerializer):
    users = WorkspaceAdminUsersSerializer(source="workspaceuser_set", many=True)
    application_count = serializers.IntegerField()
    row_count = serializers.SerializerMethodField()
    free_users = serializers.SerializerMethodField()
    seats_taken = serializers.IntegerField()

    ROW_COUNT_ANNOTATION_NAME = "row_count"

    @extend_schema_field(OpenApiTypes.INT)
    def get_free_users(self, instance):
        if instance.seats_taken:
            return instance.workspaceuser_set.count() - instance.seats_taken
        else:
            return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_row_count(self, instance):
        return getattr(instance, self.ROW_COUNT_ANNOTATION_NAME, None)

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "users",
            "application_count",
            "row_count",
            "storage_usage",
            "seats_taken",
            "free_users",
            "created_on",
        )


class AdminWorkspaceUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)


class AdminWorkspaceOptionsSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="name")

    class Meta:
        model = Workspace
        fields = ("id", "value")

from django.urls import path

from baserow.api.search.views import GlobalSearchView, WorkspaceSearchView

app_name = "baserow.api.search"

urlpatterns = [
    path(
        "",
        GlobalSearchView.as_view(),
        name="global_search",
    ),
    path(
        "workspace/<int:workspace_id>/",
        WorkspaceSearchView.as_view(),
        name="workspace_search",
    ),
]

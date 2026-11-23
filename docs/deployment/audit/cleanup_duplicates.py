from django.contrib.auth import get_user_model
from django.db import transaction

from baserow.contrib.database.models import Database, Table
from baserow.core.models import Application, Workspace
from baserow.core.trash.handler import TrashHandler

User = get_user_model()


def main():
    admin = User.objects.filter(is_staff=True).first()
    with transaction.atomic():
        demo = Workspace.objects.get(name="演示-销售管理")
        for app in Application.objects_and_trash.filter(workspace=demo, trashed=True):
            model = app.content_type.model
            if model == "database":
                continue
            if model == "dashboard" and app.id == 288:
                continue
            if model == "automation" and app.id == 291:
                continue
            print("delete app", app.id, app.name)
            TrashHandler.permanently_delete(app.specific)

    with transaction.atomic():
        audit = Workspace.objects.get(name="审计-工作区")
        db = Database.objects.get(name="审计-数据库", workspace=audit)
        tables = list(Table.objects_and_trash.filter(database=db).order_by("id"))
        keep = next((t for t in tables if not t.trashed), None)
        for table in tables:
            if table is keep:
                continue
            print("delete table", table.id, table.name, table.trashed)
            TrashHandler.permanently_delete(table)

    print("CLEANUP2_DONE")


main()

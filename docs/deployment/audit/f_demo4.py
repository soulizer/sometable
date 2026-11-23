# 批次 F4：新增证件字段示例数据
from django.contrib.auth import get_user_model

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.models import Database
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.models import Workspace

User = get_user_model()


def main():
    admin = User.objects.filter(is_staff=True).first()
    workspace = Workspace.objects.get(name="演示-销售管理")
    db = Database.objects.get(name="销售数据", workspace=workspace)

    table = db.table_set.filter(name="客户资质").first()
    if table is None:
        table, _ = TableHandler().create_table(
            admin,
            db,
            name="客户资质",
            data=[
                ["客户名称", "联系人"],
                ["北京示例科技有限公司", "张三"],
                ["上海演示贸易有限公司", "李四"],
                ["深圳样例服务有限公司", "王五"],
            ],
            first_row_header=True,
        )

    id_field = table.field_set.filter(name="身份证号").first()
    if id_field is None:
        id_field = FieldHandler().create_field(
            admin, table, "id_card", name="身份证号"
        )
    uscc_field = table.field_set.filter(name="统一社会信用代码").first()
    if uscc_field is None:
        uscc_field = FieldHandler().create_field(
            admin, table, "unified_social_credit_code", name="统一社会信用代码"
        )

    ids = ["110101199001010015", "11010119900101004X", "110101199001010023"]
    codes = ["91350100M000100Y43", "91110108MA01ABCDEN", "91310000MA1K1234XB"]
    model = table.get_model()
    for index, row in enumerate(model.objects.all()):
        RowHandler().update_row(
            admin,
            table,
            row,
            {
                f"field_{id_field.id}": ids[index % len(ids)],
                f"field_{uscc_field.id}": codes[index % len(codes)],
            },
        )

    print("F4_DEMO_DONE", table.id, model.objects.count())


main()

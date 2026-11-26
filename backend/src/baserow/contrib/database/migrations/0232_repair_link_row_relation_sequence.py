from django.db import migrations


def repair_relation_sequence(apps, schema_editor):
    """
    Moves the link row relation id sequence past every existing through table.

    The relation id sequence is independent of transactions. When a schema change
    fails after the through table has been created, the sequence keeps its value
    while the field row is rolled back. Restores and imports can also bring tables
    whose ids were never written to this sequence. In both cases the next field
    creation can try to reuse an existing ``database_relation_<id>`` table and
    fail with ``relation ... already exists``.
    """

    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    sequence_name = "database_linkrowfield_link_row_relation_id_seq"
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s)", [sequence_name])
        if cursor.fetchone()[0] is None:
            return

        cursor.execute(
            """
            SELECT GREATEST(
                COALESCE(
                    (SELECT MAX(link_row_relation_id) FROM database_linkrowfield),
                    0
                ),
                COALESCE(
                    (
                        SELECT MAX(
                            substring(tablename FROM 'database_relation_([0-9]+)')::bigint
                        )
                        FROM pg_tables
                        WHERE tablename ~ '^database_relation_[0-9]+$'
                    ),
                    0
                )
            )
            """
        )
        max_relation_id = cursor.fetchone()[0] or 0
        # `false` makes the next nextval() return the provided value.
        cursor.execute(
            "SELECT setval(%s, %s, false)",
            [sequence_name, max_relation_id + 1],
        )


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0231_chinese_identity_fields"),
    ]

    operations = [
        migrations.RunPython(repair_relation_sequence, migrations.RunPython.noop),
    ]

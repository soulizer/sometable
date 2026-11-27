from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0232_repair_link_row_relation_sequence"),
    ]

    operations = [
        migrations.AddField(
            model_name="view",
            name="locked",
            field=models.BooleanField(
                default=False,
                db_default=False,
                help_text="When locked, only the view owner or an instance staff "
                "member can change the view configuration or its rows.",
            ),
        ),
    ]

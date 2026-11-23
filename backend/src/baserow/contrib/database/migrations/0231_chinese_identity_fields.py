import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0230_multiplecollaboratorsfield_include_identities"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdCardField",
            fields=[
                (
                    "field_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.Field",
                    ),
                ),
            ],
            options={"abstract": False},
            bases=("database.field",),
        ),
        migrations.CreateModel(
            name="UnifiedSocialCreditCodeField",
            fields=[
                (
                    "field_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.Field",
                    ),
                ),
            ],
            options={"abstract": False},
            bases=("database.field",),
        ),
    ]

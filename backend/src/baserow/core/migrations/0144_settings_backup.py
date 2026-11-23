from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0143_settings_favicon"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="backup_scope",
            field=models.CharField(
                choices=[
                    ("all", "all"),
                    ("database", "database"),
                    ("object_storage", "object_storage"),
                ],
                default="all",
                db_default="all",
                help_text="What the scheduled backups include.",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="backup_frequency",
            field=models.CharField(
                choices=[
                    ("disabled", "disabled"),
                    ("daily", "daily"),
                    ("weekly", "weekly"),
                    ("monthly", "monthly"),
                ],
                default="daily",
                db_default="daily",
                help_text="How often scheduled backups run.",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="backup_hour",
            field=models.PositiveSmallIntegerField(
                default=3, db_default=3, help_text="Hour of day for scheduled backups."
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="backup_dow",
            field=models.PositiveSmallIntegerField(
                default=0, db_default=0, help_text="Day of week for weekly backups."
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="backup_dom",
            field=models.PositiveSmallIntegerField(
                default=1, db_default=1, help_text="Day of month for monthly backups."
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="backup_keep",
            field=models.PositiveSmallIntegerField(
                default=7, db_default=7, help_text="Number of backups to keep."
            ),
        ),
    ]

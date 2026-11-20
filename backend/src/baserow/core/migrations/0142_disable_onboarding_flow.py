from django.db import migrations, models


def complete_onboarding_for_everyone(apps, schema_editor):
    """This instance has no onboarding flow, so no profile should be pending it."""

    UserProfile = apps.get_model("core", "UserProfile")
    UserProfile.objects.filter(
        models.Q(completed_onboarding=False) | models.Q(completed_onboarding__isnull=True)
    ).update(completed_onboarding=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0141_ai_provider_excluded_workspaces"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="show_baserow_help_request",
            field=models.BooleanField(
                db_default=False,
                default=False,
                help_text=(
                    "Deprecated: the help request banner has been removed from the "
                    "UI. Kept for backwards compatibility of existing API clients."
                ),
            ),
        ),
        migrations.RunPython(
            complete_onboarding_for_everyone, migrations.RunPython.noop
        ),
    ]

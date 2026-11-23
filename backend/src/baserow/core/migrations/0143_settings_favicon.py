import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0142_disable_onboarding_flow"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="favicon",
            field=models.ForeignKey(
                blank=True,
                help_text="Favicon of the instance. When empty, the default icon is "
                "used.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.userfile",
            ),
        ),
    ]

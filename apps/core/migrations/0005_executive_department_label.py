from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_remove_executive_gender_executive_avatar_icon"),
    ]

    operations = [
        migrations.AddField(
            model_name="executive",
            name="department_label",
            field=models.CharField(
                blank=True,
                help_text="Preserves the executive's department when it has not yet been added to the department directory.",
                max_length=140,
                verbose_name="department as supplied",
            ),
        ),
    ]

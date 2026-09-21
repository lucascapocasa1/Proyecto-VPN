from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("players", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="position",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ARQ", "Arquero"),
                    ("DEF", "Defensor"),
                    ("MED", "Mediocampista"),
                    ("DEL", "Delantero"),
                ],
                max_length=3,
                null=True,
            ),
        ),
    ]

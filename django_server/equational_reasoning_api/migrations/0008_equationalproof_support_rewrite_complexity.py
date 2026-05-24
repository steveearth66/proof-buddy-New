from django.db import migrations, models


def add_column_if_not_exists(apps, schema_editor):
    """Only add the column if it does not already exist (handles dev DBs where it was added manually)."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'equational_reasoning_api_equationalproof'
              AND COLUMN_NAME = 'support_rewrite_complexity'
            """
        )
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute(
                "ALTER TABLE equational_reasoning_api_equationalproof "
                "ADD COLUMN support_rewrite_complexity TINYINT(1) NOT NULL DEFAULT 1"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('equational_reasoning_api', '0007_alter_equationalproof_visible_rules'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='equationalproof',
                    name='support_rewrite_complexity',
                    field=models.BooleanField(default=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_column_if_not_exists, migrations.RunPython.noop),
            ],
        ),
    ]

# Merge migration: brings 0006_add_comment_fields (orphaned branch) into the main chain.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equational_reasoning_api', '0006_add_comment_fields'),
        ('equational_reasoning_api', '0009_merge_20260523_1250'),
    ]

    operations = [
    ]

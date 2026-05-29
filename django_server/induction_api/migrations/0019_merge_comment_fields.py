# Merge migration: brings 0014_add_comment_fields (orphaned branch) into the main chain.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('induction_api', '0014_add_comment_fields'),
        ('induction_api', '0018_merge_20260523_1250'),
    ]

    operations = [
    ]

# Generated migration for adding comment fields to EquationalProofLine
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equational_reasoning_api', '0005_equationalproof_support_current_lhs_rhs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='equationalproofline',
            name='instructor_comment',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='equationalproofline',
            name='student_comment',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='equationalproofline',
            name='comment_correct',
            field=models.BooleanField(default=None, null=True),
        ),
    ]

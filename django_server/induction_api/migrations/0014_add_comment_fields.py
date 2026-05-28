# Generated migration for adding comment fields to InductionProofLine
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('induction_api', '0013_inductionproof_support_current_lhs_rhs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inductionproofline',
            name='instructor_comment',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='inductionproofline',
            name='student_comment',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='inductionproofline',
            name='comment_correct',
            field=models.BooleanField(default=None, null=True),
        ),
    ]

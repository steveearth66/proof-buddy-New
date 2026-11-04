from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('induction_api', '0019_alter_inductionprooflinecomment_proof'),
    ]

    operations = [
        migrations.AddField(
            model_name='inductionprooflinecomment',
            name='case',
            field=models.CharField(default='base', max_length=10),
        ),
    ]

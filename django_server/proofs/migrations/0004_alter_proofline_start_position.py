# Generated by Django 5.0.5 on 2024-05-07 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proofs', '0003_alter_proof_lsh_alter_proof_rsh'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proofline',
            name='start_position',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
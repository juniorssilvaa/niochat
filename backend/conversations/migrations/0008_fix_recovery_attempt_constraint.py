# Generated manually to fix constraint issue

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conversations', '0007_alter_contact_options_alter_conversation_options_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='recoveryattempt',
            unique_together={('conversation', 'attempt_number')},
        ),
    ]
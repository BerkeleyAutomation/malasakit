from __future__ import unicode_literals

from django.db import migrations, models


def forwards_qualitative_question(apps, schema_editor):
    Text = apps.get_model('pcari', 'Text')
    QualitativeQuestion = apps.get_model('pcari', 'QualitativeQuestion')
    prompt = Text()
    question = QualitativeQuestion(prompt=prompt)


def backwards_qualitative_question(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunPython(forwards_qualitative_question, 
                             backwards_qualitative_question),
    ]

from decimal import Decimal

from django.db import migrations


def add_custom_diagnosis_service(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    Service.objects.using(schema_editor.connection.alias).get_or_create(
        service_name='Custom Problem & Diagnosis',
        defaults={
            'description': 'Mechanic inspects the reported issue and submits an estimate before repair work begins.',
            'price_type': 'ESTIMATE',
            'vehicle_type': 'ALL',
            'base_price': Decimal('0.00'),
            'estimated_hours': Decimal('1.5'),
            'icon': 'bi-search',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0002_service_price_type_alter_service_base_price'),
    ]

    operations = [
        migrations.RunPython(add_custom_diagnosis_service, migrations.RunPython.noop),
    ]

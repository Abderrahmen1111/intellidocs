# Generated manually for PostgreSQL/Supabase with pgvector support

from django.db import migrations, models
import django.db.models.deletion
try:
    from pgvector.django import VectorExtension, VectorField
except ImportError:
    # Safe fallback for environments without pgvector (e.g. local SQLite development / IDE analysis)
    class VectorExtension(migrations.operations.base.Operation):
        def state_forwards(self, app_label, state): pass
        def database_forwards(self, app_label, schema_editor, from_state, to_state): pass
        def database_backwards(self, app_label, schema_editor, from_state, to_state): pass
        def describe(self): return "Dummy VectorExtension"

    class VectorField(models.BinaryField):
        def __init__(self, *args, **kwargs):
            kwargs.pop('dimensions', None)
            super().__init__(*args, **kwargs)

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_now_add=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('file_path', models.CharField(blank=True, max_length=512, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.BigAutoField(auto_now_add=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('chunk_index', models.PositiveIntegerField()),
                ('embedding', VectorField(dimensions=384)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='core.document')),
            ],
            options={
                'ordering': ['document', 'chunk_index'],
            },
        ),
    ]

# backend/core/models.py
from django.db import models

try:
    from pgvector.django import VectorField
    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback pour les environnements sans PostgreSQL/pgvector (ex: CI, dev local SQLite)
    VectorField = None
    PGVECTOR_AVAILABLE = False


class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    file_path = models.CharField(max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


if PGVECTOR_AVAILABLE:
    class DocumentChunk(models.Model):
        document = models.ForeignKey(
            Document, on_delete=models.CASCADE, related_name='chunks'
        )
        content = models.TextField()
        chunk_index = models.PositiveIntegerField()
        # Dimension 384 pour all-MiniLM-L6-v2
        embedding = VectorField(dimensions=384)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.document.title} — chunk {self.chunk_index}"

        class Meta:
            ordering = ['document', 'chunk_index']
else:
    # Modèle de substitution sans embeddings (SQLite / dev local)
    class DocumentChunk(models.Model):
        document = models.ForeignKey(
            Document, on_delete=models.CASCADE, related_name='chunks'
        )
        content = models.TextField()
        chunk_index = models.PositiveIntegerField()
        # embedding stocké en JSON quand pgvector n'est pas disponible
        embedding_json = models.JSONField(null=True, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{self.document.title} — chunk {self.chunk_index}"

        class Meta:
            ordering = ['document', 'chunk_index']
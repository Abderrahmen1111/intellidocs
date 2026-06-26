# backend/core/serializers.py
from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_index', 'content', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'file_path', 'created_at', 'updated_at', 'chunks']
        read_only_fields = ['id', 'created_at', 'updated_at']

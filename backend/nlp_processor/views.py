# backend/nlp_processor/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import generate_answer, semantic_search


class SearchView(APIView):
    """
    POST /api/nlp/search/
    Body: { "query": "...", "top_k": 5 }
    Retourne les chunks les plus similaires sans génération LLM.
    """
    def post(self, request):
        query = request.data.get('query', '').strip()
        top_k = int(request.data.get('top_k', 5))

        if not query:
            return Response(
                {"error": "Le champ 'query' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        chunks = semantic_search(query, top_k=top_k)
        results = [
            {
                "id": c.id,
                "document_title": c.document.title,
                "chunk_index": c.chunk_index,
                "content": c.content,
            }
            for c in chunks
        ]
        return Response({"query": query, "results": results}, status=status.HTTP_200_OK)


class AnswerView(APIView):
    """
    POST /api/nlp/answer/
    Body: { "query": "...", "top_k": 5 }
    Pipeline RAG complet : recherche sémantique + génération LLM.
    """
    def post(self, request):
        query = request.data.get('query', '').strip()
        top_k = int(request.data.get('top_k', 5))

        if not query:
            return Response(
                {"error": "Le champ 'query' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = generate_answer(query, top_k=top_k)
        return Response({"query": query, **result}, status=status.HTTP_200_OK)

# backend/nlp_processor/services.py
import os
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

try:
    from pgvector.django import CosineDistance
    PGVECTOR_AVAILABLE = True
except ImportError:
    CosineDistance = None
    PGVECTOR_AVAILABLE = False

# Charger le modèle une seule fois au démarrage du module (mis en cache)
_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def generate_embedding(text: str) -> list[float]:
    """Génère un vecteur d'embeddings pour un texte donné."""
    model = _get_model()
    return model.encode(text).tolist()


def process_document(content: str, title: str, document_id: int | None = None) -> list:
    """
    Découpe le contenu en chunks, génère les embeddings et les persiste en base de données.
    Retourne la liste des chunks créés.
    """
    from core.models import DocumentChunk, Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.create_documents([content])

    created_chunks = []

    if document_id:
        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            return []

        # Supprimer les anciens chunks en cas de re-traitement
        document.chunks.all().delete()

        for i, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk.page_content)

            if PGVECTOR_AVAILABLE:
                doc_chunk = DocumentChunk.objects.create(
                    document=document,
                    content=chunk.page_content,
                    chunk_index=i,
                    embedding=embedding,
                )
            else:
                # Fallback SQLite : stockage JSON
                doc_chunk = DocumentChunk.objects.create(
                    document=document,
                    content=chunk.page_content,
                    chunk_index=i,
                    embedding_json=embedding,
                )

            created_chunks.append(doc_chunk)
            print(f"[NLP] Chunk {i+1}/{len(chunks)} traité pour '{title}'.")

    return created_chunks


def semantic_search(query: str, top_k: int = 5) -> list:
    """
    Recherche sémantique :
    - Avec pgvector : similarité cosinus native via PostgreSQL.
    - Sans pgvector  : fallback par similarité cosinus en mémoire (dev local).
    """
    from core.models import DocumentChunk

    query_embedding = generate_embedding(query)

    if PGVECTOR_AVAILABLE:
        results = (
            DocumentChunk.objects
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .order_by('distance')[:top_k]
            .select_related('document')
        )
        return list(results)
    else:
        # Fallback : calcul cosinus en mémoire (dev/test sans PostgreSQL)
        import numpy as np
        all_chunks = list(DocumentChunk.objects.select_related('document').all())
        if not all_chunks:
            return []

        q = np.array(query_embedding)
        scored = []
        for chunk in all_chunks:
            emb = chunk.embedding_json
            if emb:
                v = np.array(emb)
                cos_sim = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9))
                scored.append((cos_sim, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]


def generate_answer(query: str, top_k: int = 5) -> dict:
    """
    Pipeline RAG complet :
    1. Recherche sémantique des chunks les plus pertinents.
    2. Construction du contexte.
    3. Génération de la réponse via Groq (Llama 3.1).

    Retourne un dict avec 'answer' et 'sources'.
    """
    api_key = os.getenv('GROQ_API_KEY')

    chunks = semantic_search(query, top_k=top_k)
    context = "\n\n".join(c.content for c in chunks)
    sources = list({c.document.title for c in chunks})

    if not api_key:
        return {
            'answer': (
                f"[MODE DÉMO — GROQ_API_KEY non configurée]\n\n"
                f"Contexte trouvé ({len(chunks)} chunks) :\n{context[:500]}..."
            ),
            'sources': sources,
        }

    prompt = ChatPromptTemplate.from_template(
        "Tu es un assistant documentaire expert. Réponds uniquement à partir du contexte fourni.\n\n"
        "Contexte :\n{context}\n\n"
        "Question : {question}\n\n"
        "Réponds de manière précise et cite les sources pertinentes."
    )

    llm = ChatGroq(
        model=os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile'),
        temperature=0,
        api_key=api_key,
    )

    chain = prompt | llm
    response = chain.invoke({'context': context, 'question': query})

    return {
        'answer': response.content,
        'sources': sources,
    }
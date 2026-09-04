import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from app.config import CHROMA_DIR, EMBEDDING_MODEL_NAME


def get_collection_name_for_paper(paper_id: str | None = None) -> str:
    """Map a paper_id (UUID) to a valid ChromaDB collection name."""
    if not paper_id:
        return "papers"
    clean_id = paper_id.replace("-", "_")
    return f"paper_{clean_id}"


def get_collection(collection_name: str = "papers"):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    embedding_function = OllamaEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME,
        url="http://localhost:11434/api/embeddings",
    )

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def add_chunks(chunks: list[dict], collection_name: str = "papers"):
    collection = get_collection(collection_name)
    collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "page": chunk["page"],
                "section": chunk["section"],
                "chunk_id": chunk["chunk_id"],
            }
            for chunk in chunks
        ],
    )


def search(query: str, k: int = 5, collection_name: str = "papers") -> dict:
    collection = get_collection(collection_name)
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    return results


def reset_collection(collection_name: str = "papers"):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(collection_name)
        print(f"Collection '{collection_name}' deleted.")
    except Exception:
        print(f"Collection '{collection_name}' does not exist.")
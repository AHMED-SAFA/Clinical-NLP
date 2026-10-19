import chromadb
from sentence_transformers import SentenceTransformer
from .config import CARDS_PATH, INDEX_DIR, COLLECTION, EMBED_MODEL
from .schema import Card


def load_cards(path=CARDS_PATH) -> list[Card]:
    return [
        Card.model_validate_json(l)
        for l in path.read_text("utf-8").splitlines()
        if l.strip()
    ]


def build_index():
    cards = load_cards()
    if not cards:
        raise SystemExit(
            "No cards in data/cards/cards.jsonl - review drafts and add cards first."
        )
    texts = [c.index_text() for c in cards]
    embs = SentenceTransformer(EMBED_MODEL).encode(
        texts, normalize_embeddings=True, show_progress_bar=True
    )
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[c.card_id for c in cards],
        embeddings=embs.tolist(),
        documents=texts,
        metadatas=[{"disease": c.disease, "category": c.category} for c in cards],
    )
    return len(cards)

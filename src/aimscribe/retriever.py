import re
from dataclasses import dataclass
from typing import Optional
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from .config import INDEX_DIR, COLLECTION, EMBED_MODEL
from .indexer import load_cards
from .schema import Card

QPREFIX = (
    "Represent this sentence for searching relevant passages: "  # BGE query instruction
)


def _tok(s):
    return re.findall(r"[a-z0-9]+", s.lower())


@dataclass
class Hit:
    card: Card
    rrf: float
    dense_rank: Optional[int]
    bm25_rank: Optional[int]


class HybridRetriever:
    def __init__(self):
        self.cards = load_cards()
        self.by_id = {c.card_id: c for c in self.cards}
        self.model = SentenceTransformer(EMBED_MODEL)
        self.col = chromadb.PersistentClient(path=str(INDEX_DIR)).get_collection(
            COLLECTION
        )
        self.bm25 = BM25Okapi([_tok(c.index_text()) for c in self.cards])

    def retrieve(
        self, query, k=12, disease=None, category=None, pool=40, rrf_k=60
    ) -> list[Hit]:
        allowed = [
            i
            for i, c in enumerate(self.cards)
            if (not disease or c.disease == disease)
            and (not category or c.category == category)
        ]
        if not allowed:
            return []
        conds = [{"disease": disease}] if disease else []
        conds += [{"category": category}] if category else []
        where = None if not conds else conds[0] if len(conds) == 1 else {"$and": conds}
        q = self.model.encode(QPREFIX + query, normalize_embeddings=True).tolist()
        dense = self.col.query(
            query_embeddings=[q], n_results=min(pool, len(allowed)), where=where
        )["ids"][0]
        sc = self.bm25.get_scores(_tok(query))
        bm = [
            self.cards[i].card_id
            for i in sorted(allowed, key=lambda i: -sc[i])[:pool]
            if sc[i] > 0
        ]
        score, dr, br = {}, {}, {}
        for r, cid in enumerate(dense, 1):
            dr[cid] = r
            score[cid] = score.get(cid, 0) + 1 / (rrf_k + r)
        for r, cid in enumerate(bm, 1):
            br[cid] = r
            score[cid] = score.get(cid, 0) + 1 / (rrf_k + r)
        top = sorted(score, key=score.get, reverse=True)[:k]
        return [Hit(self.by_id[c], score[c], dr.get(c), br.get(c)) for c in top]

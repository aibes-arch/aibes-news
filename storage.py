"""
storage.py
SQLite + 向量库存储
- SQLite：保存元数据、分类、摘要、时间
- Chroma：保存文本向量，支持语义检索
"""
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "news.db")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma")

# 轻量级中文/多语言 embedding 模型
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


class Storage:
    def __init__(self):
        _ensure_dir()
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_sqlite()
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection("news")
        self._embedding_model: Optional[SentenceTransformer] = None

    def _init_sqlite(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                summary TEXT,
                clean_summary TEXT,
                content TEXT,
                published TEXT,
                source TEXT,
                source_category TEXT,
                category TEXT,
                confidence REAL,
                tags TEXT,
                summary_json TEXT,
                collected_at TEXT,
                vectorized INTEGER DEFAULT 0
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_published ON items(published)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)
        """)
        self.conn.commit()

    def _embedding(self) -> SentenceTransformer:
        if self._embedding_model is None:
            logger.info("[storage] 加载 embedding 模型: %s", EMBEDDING_MODEL)
            self._embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        return self._embedding_model

    def upsert(self, item: Dict[str, Any]) -> bool:
        """插入或更新 item；若已存在则跳过。"""
        try:
            existing = self.conn.execute(
                "SELECT id FROM items WHERE id=?", (item["id"],)
            ).fetchone()
            if existing:
                return False

            tags = item.get("tags", [])
            summary_json = item.get("summary", {})
            if isinstance(summary_json, dict):
                summary_json = json.dumps(summary_json, ensure_ascii=False)

            self.conn.execute(
                """
                INSERT INTO items
                (id, title, link, summary, clean_summary, content, published,
                 source, source_category, category, confidence, tags,
                 summary_json, collected_at, vectorized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["id"],
                    item.get("title", ""),
                    item.get("link", ""),
                    item.get("summary", ""),
                    item.get("clean_summary", ""),
                    item.get("content", ""),
                    item.get("published", datetime.utcnow()).isoformat()
                    if isinstance(item.get("published"), datetime)
                    else str(item.get("published", datetime.utcnow())),
                    item.get("source", ""),
                    item.get("source_category", ""),
                    item.get("category", "其他"),
                    item.get("confidence", 0.0),
                    json.dumps(tags, ensure_ascii=False),
                    summary_json,
                    datetime.utcnow().isoformat(),
                    0,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error("[storage] upsert 失败 %s: %s", item.get("id"), e)
            return False

    def vectorize_unvectorized(self):
        """为未向量化的记录生成 embedding 并写入 Chroma。"""
        rows = self.conn.execute(
            "SELECT id, title, clean_summary, content FROM items WHERE vectorized=0"
        ).fetchall()
        if not rows:
            return
        model = self._embedding()
        ids, docs, metadatas = [], [], []
        for row in rows:
            text = " ".join(filter(None, [row["title"], row["clean_summary"], row["content"]]))
            if not text.strip():
                continue
            ids.append(row["id"])
            docs.append(text[:2000])
            metadatas.append({"title": row["title"], "source": row.get("source", "")})

        if ids:
            embeddings = model.encode(docs, show_progress_bar=True).tolist()
            self.collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)
            self.conn.executemany(
                "UPDATE items SET vectorized=1 WHERE id=?", [(i,) for i in ids]
            )
            self.conn.commit()
            logger.info("[storage] 向量化 %d 条记录", len(ids))

    def get_recent(self, hours: int = 48, category: Optional[str] = None) -> List[Dict[str, Any]]:
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        sql = "SELECT * FROM items WHERE collected_at > ?"
        params = [since]
        if category:
            sql += " AND category=?"
            params.append(category)
        sql += " ORDER BY collected_at DESC"
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_by_date_range(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE published BETWEEN ? AND ? ORDER BY published DESC",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_categories(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT category FROM items ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """基于向量语义检索。"""
        if self.collection.count() == 0:
            return []
        model = self._embedding()
        emb = model.encode([query]).tolist()
        results = self.collection.query(query_embeddings=emb, n_results=top_k)
        ids = results["ids"][0]
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        rows = self.conn.execute(
            f"SELECT * FROM items WHERE id IN ({placeholders})", ids
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict[str, int]:
        total = self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        vec = self.conn.execute("SELECT COUNT(*) FROM items WHERE vectorized=1").fetchone()[0]
        return {"total": total, "vectorized": vec}

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    s = Storage()
    print(s.get_stats())

"""
ADR-001'in temel varsayimini (cok dilli embedding ile Turkce sorgu ->
Ingilizce dataset kayitlarinda dogru sonuc) 200 satirlik bir pilotla
dogrular. Tam 44.884 satirlik ingestion'a gecmeden once calistirilir.
"""
import csv
import os
import time

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from qdrant_client import QdrantClient, models

load_dotenv()

CSV_PATH = "bitext-retail-ecommerce-llm-chatbot-training-dataset.csv"
PILOT_SIZE = 100
EMBED_MODEL = "gemini-embedding-001"
OUTPUT_DIM = 768
COLLECTION = "support_qa_pilot"

TEST_QUERIES = [
    ("Verdiğim siparişi iptal etmek istiyorum.", "cancel_order"),
    ("Şifremi unuttum, nasıl sıfırlarım?", "recover_password"),
    ("Kargom nerede, takip edebilir miyim?", "track_order"),
    ("Bu ürün bitki bazlı mı, vegan mı?", None),  # off-domain, dataset'te yok
]


def normalize(vec):
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


MAX_BATCH = 100


def embed_batch(client, texts, task_type):
    vectors = []
    for start in range(0, len(texts), MAX_BATCH):
        chunk = texts[start : start + MAX_BATCH]
        for attempt in range(5):
            try:
                resp = client.models.embed_content(
                    model=EMBED_MODEL,
                    contents=chunk,
                    config=types.EmbedContentConfig(
                        output_dimensionality=OUTPUT_DIM, task_type=task_type
                    ),
                )
                break
            except errors.ClientError as e:
                if e.code == 429 and attempt < 4:
                    wait = 60
                    print(f"  rate limited, sleeping {wait}s (attempt {attempt + 1})...")
                    time.sleep(wait)
                else:
                    raise
        vectors.extend(normalize(v.values) for v in resp.embeddings)
    return vectors


def main():
    gemini = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    qdrant = QdrantClient(":memory:")
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=OUTPUT_DIM, distance=models.Distance.COSINE
        ),
    )

    # Dataset satirlari intent'e gore bloklar halinde siralanmis (ilk 100
    # satirin hepsi ayni intent). Rastgele bir dilim yerine, test
    # sorgularinin beklenen intent'lerinden + birkac alakasiz intent'ten
    # stratified sample aliyoruz ki pilot gercek bir sinyal versin.
    wanted_intents = {
        "cancel_order": 15,
        "recover_password": 15,
        "track_order": 15,
        "add_product": 15,
        "refund_status": 15,
        "delivery_time": 15,
    }
    per_intent = {k: 0 for k in wanted_intents}
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            intent = row["intent"]
            if intent in wanted_intents and per_intent[intent] < wanted_intents[intent]:
                rows.append(row)
                per_intent[intent] += 1
            if len(rows) >= PILOT_SIZE:
                break

    print(f"Embedding {len(rows)} pilot rows (task_type=RETRIEVAL_DOCUMENT)...")
    instructions = [r["instruction"] for r in rows]
    doc_vectors = embed_batch(gemini, instructions, "RETRIEVAL_DOCUMENT")

    points = [
        models.PointStruct(
            id=i,
            vector=vec,
            payload={
                "instruction": row["instruction"],
                "response": row["response"],
                "category": row["category"],
                "intent": row["intent"],
            },
        )
        for i, (row, vec) in enumerate(zip(rows, doc_vectors))
    ]
    qdrant.upsert(collection_name=COLLECTION, points=points, wait=True)
    print(f"Indexed {len(points)} points into in-memory Qdrant.\n")

    print("Embedding test queries (task_type=RETRIEVAL_QUERY)...\n")
    query_vectors = embed_batch(
        gemini, [q for q, _ in TEST_QUERIES], "RETRIEVAL_QUERY"
    )

    for (query_text, expected_intent), qvec in zip(TEST_QUERIES, query_vectors):
        hits = qdrant.query_points(
            collection_name=COLLECTION, query=qvec, limit=5
        ).points
        print(f"Query: {query_text!r}  (expected intent: {expected_intent})")
        for h in hits:
            print(
                f"  score={h.score:.4f}  intent={h.payload['intent']:<20} "
                f"instruction={h.payload['instruction'][:60]!r}"
            )
        print()


if __name__ == "__main__":
    main()

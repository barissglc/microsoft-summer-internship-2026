"""
44.884 satirlik Bitext e-ticaret dataset'ini Qdrant'a aktarir.

Embedding icin Voyage AI (voyage-4) kullanilir; ucretsiz kotasi
(hesap basi ilk 200M token) bu dataset icin fazlasiyla yeterli, bu
yuzden Gemini'deki gunluk kota sorunu burada yok. Yine de checkpoint
dosyasi ile resumable'dir (ADR-006) ve 429 hatalarinda retry yapar.
"""
import csv
import json
import os
import time
from pathlib import Path

import voyageai
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

CSV_PATH = "bitext-retail-ecommerce-llm-chatbot-training-dataset.csv"
CHECKPOINT_PATH = Path("ingestion_checkpoint.json")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = "support_qa"
EMBED_MODEL = "voyage-4-large"
OUTPUT_DIM = 1024
BATCH_SIZE = 500


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text())["last_index"]
    return -1


def save_checkpoint(last_index):
    CHECKPOINT_PATH.write_text(json.dumps({"last_index": last_index}))


def embed_with_retry(client, texts, input_type):
    for attempt in range(6):
        try:
            resp = client.embed(
                texts,
                model=EMBED_MODEL,
                input_type=input_type,
                output_dimension=OUTPUT_DIM,
            )
            return resp.embeddings
        except (voyageai.error.RateLimitError, voyageai.error.ServiceUnavailableError) as e:
            if attempt < 5:
                print(f"  rate limited/unavailable, sleeping 20s (attempt {attempt + 1}/5): {e}")
                time.sleep(20)
            else:
                raise
    raise RuntimeError("embed_with_retry: exhausted retries")


def ensure_collection(qdrant):
    if qdrant.collection_exists(COLLECTION):
        info = qdrant.get_collection(COLLECTION)
        existing_size = info.config.params.vectors.size
        if existing_size != OUTPUT_DIM:
            print(
                f"Collection '{COLLECTION}' has dim {existing_size}, "
                f"expected {OUTPUT_DIM} (embedding provider changed). Recreating."
            )
            qdrant.delete_collection(COLLECTION)
            if CHECKPOINT_PATH.exists():
                CHECKPOINT_PATH.unlink()
        else:
            print(f"Collection '{COLLECTION}' already exists, resuming.")
            return

    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(size=OUTPUT_DIM, distance=models.Distance.COSINE),
    )
    print(f"Created collection '{COLLECTION}'.")


def read_all_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    voyage = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant)

    rows = read_all_rows()
    total = len(rows)
    start_index = load_checkpoint() + 1
    print(f"Total rows: {total}. Resuming from index {start_index}.")

    idx = start_index
    while idx < total:
        batch_rows = rows[idx : idx + BATCH_SIZE]

        instructions = [r["instruction"] for r in batch_rows]
        vectors = embed_with_retry(voyage, instructions, "document")

        points = [
            models.PointStruct(
                id=idx + offset,
                vector=vec,
                payload={
                    "instruction": row["instruction"],
                    "response": row["response"],
                    "category": row["category"],
                    "intent": row["intent"],
                },
            )
            for offset, (row, vec) in enumerate(zip(batch_rows, vectors))
        ]
        qdrant.upsert(collection_name=COLLECTION, points=points, wait=True)

        last_index_in_batch = idx + len(batch_rows) - 1
        save_checkpoint(last_index_in_batch)

        done = last_index_in_batch + 1
        print(f"[{done}/{total}] indexed ({done * 100 // total}%)")

        idx += BATCH_SIZE

    print("Ingestion complete.")


if __name__ == "__main__":
    main()

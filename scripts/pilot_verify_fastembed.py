"""
Gemini API'nin gunluk kotasi (1000 embed/gun, free tier) 44.884 satirlik
tam ingestion'i pratiksiz hale getirdi. Alternatif olarak acik kaynak,
sunucuda (CPU, 1 vCPU / 2GB RAM) calisabilecek kucuk bir cok dilli model
deneniyor: intfloat/multilingual-e5-small (FastEmbed uzerinden, ONNX,
~0.4GB). Ayni stratified 90 satirlik pilot ve ayni Turkce test sorgulariyla
Gemini pilotuyla (scripts/pilot_verify.py) karsilastirilabilir sonuc
uretiyor.
"""
import csv
import time

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

COLLECTION = "support_qa_pilot_mpnet"
CSV_PATH = "bitext-retail-ecommerce-llm-chatbot-training-dataset.csv"

TEST_QUERIES = [
    ("Verdiğim siparişi iptal etmek istiyorum.", "cancel_order"),
    ("Şifremi unuttum, nasıl sıfırlarım?", "recover_password"),
    ("Kargom nerede, takip edebilir miyim?", "track_order"),
    ("Bu ürün bitki bazlı mı, vegan mı?", None),
]

wanted_intents = {
    "cancel_order": 15,
    "recover_password": 15,
    "track_order": 15,
    "add_product": 15,
    "refund_status": 15,
    "delivery_time": 15,
}


def main():
    t0 = time.time()
    model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    print(f"Model loaded in {time.time() - t0:.1f}s")

    per_intent = {k: 0 for k in wanted_intents}
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            intent = row["intent"]
            if intent in wanted_intents and per_intent[intent] < wanted_intents[intent]:
                rows.append(row)
                per_intent[intent] += 1
            if len(rows) >= 90:
                break

    t0 = time.time()
    doc_texts = [r["instruction"] for r in rows]
    doc_vectors = list(model.embed(doc_texts))
    print(f"Embedded {len(rows)} docs in {time.time() - t0:.2f}s")

    qdrant = QdrantClient(":memory:")
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    )
    points = [
        models.PointStruct(
            id=i,
            vector=vec.tolist(),
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

    query_texts = [q for q, _ in TEST_QUERIES]
    t0 = time.time()
    query_vectors = list(model.embed(query_texts))
    print(f"Embedded {len(TEST_QUERIES)} queries in {time.time() - t0:.2f}s\n")

    for (query_text, expected), qvec in zip(TEST_QUERIES, query_vectors):
        hits = qdrant.query_points(
            collection_name=COLLECTION, query=qvec.tolist(), limit=5
        ).points
        print(f"Query: {query_text!r}  (expected intent: {expected})")
        for h in hits:
            print(
                f"  score={h.score:.4f}  intent={h.payload['intent']:<20} "
                f"instruction={h.payload['instruction'][:60]!r}"
            )
        print()


if __name__ == "__main__":
    main()

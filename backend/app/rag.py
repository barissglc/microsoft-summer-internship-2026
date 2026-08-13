import os

import voyageai
from google import genai
from google.genai import types
from qdrant_client import QdrantClient

EMBED_MODEL = "voyage-4-large"
GEN_MODEL = "gemini-flash-lite-latest"
OUTPUT_DIM = 1024
COLLECTION = "support_qa"
TOP_K = 5

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

_gemini = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_voyage = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
_qdrant = QdrantClient(url=QDRANT_URL)

SYSTEM_INSTRUCTION = """\
Sen bir e-ticaret sitesinin müşteri destek asistanısın. Kısa ve net
cevap ver. Cevabını HER ZAMAN kullanıcının son mesajıyla aynı dilde yaz
(kullanıcı İngilizce sorduysa İngilizce, İspanyolca sorduysa İspanyolca,
Türkçe sorduysa Türkçe cevap ver) — kullanıcının dilini algıla ve ona
uy, varsayılan olarak Türkçe kullanma.

Sana her seferinde, geçmiş müşteri destek kayıtlarından bulunan en benzer
örnekler verilecek; her örneğin yanında bir benzerlik skoru (0-1 arası,
1 = tam örtüşen) olacak.

Kurallar:
- Sadece verilen örneklerdeki bilgiye dayanarak cevap ver. Örneklerde
  olmayan hiçbir politika, tarih, tutar veya kural uydurma.
- Örneklerin benzerlik skorlarına dikkat et. Skorlar genel olarak düşükse
  (örn. hepsi ~0.5 veya altı) ya da örnekler kullanıcının sorduğu konuyla
  gerçekten örtüşmüyorsa, bunu tahmin etmeye çalışma: kısaca emin
  olmadığını belirt ve kullanıcıyı canlı bir müşteri temsilcisine
  yönlendir.
- Örnekleri kelimesi kelimesine kopyalamak yerine, kullanıcının sorusuna
  göre tek, akıcı ve anlaşılır bir cevap halinde yeniden yaz.
- Skorları veya "örnek", "kayıt" gibi iç sistem terimlerini kullanıcıya
  gösterme; bunlar sadece senin karar vermen için.
- Düz metin yaz: yıldız (**), başlık (#) gibi markdown biçimlendirmesi
  kullanma. Madde listesi gerekiyorsa "1.", "2." gibi numaralandır veya
  "-" ile başlayan satırlar kullan, yıldızla vurgu yapma.
"""


def embed_query(text: str):
    resp = _voyage.embed(
        [text],
        model=EMBED_MODEL,
        input_type="query",
        output_dimension=OUTPUT_DIM,
    )
    return resp.embeddings[0]


def search_similar(vector):
    if not _qdrant.collection_exists(COLLECTION):
        return []
    return _qdrant.query_points(
        collection_name=COLLECTION, query=vector, limit=TOP_K
    ).points


def build_context_block(hits):
    if not hits:
        return "(No matching records found.)"
    lines = []
    for h in hits:
        p = h.payload
        lines.append(
            f"[benzerlik: {h.score:.2f}] [{p['category']}/{p['intent']}]\n"
            f"Soru: {p['instruction']}\n"
            f"Cevap: {p['response']}"
        )
    return "\n\n".join(lines)


def build_meta(hits):
    if not hits:
        return "no matching records"
    best = max(h.score for h in hits)
    return f"source: {len(hits)} similar records · top match: {best:.2f}"


ROLE_MAP = {"user": "user", "bot": "model"}


def build_contents(history, current_message, context_block):
    contents = []
    for turn in history[:-1]:
        role = ROLE_MAP.get(turn["role"])
        if role is None:
            continue
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=turn["text"])])
        )

    augmented = (
        f"Kullanıcının sorusu: {current_message}\n\n"
        f"Benzer geçmiş destek kayıtları:\n{context_block}"
    )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=augmented)])
    )
    return contents


def answer(message: str, history: list[dict]):
    vector = embed_query(message)
    hits = search_similar(vector)
    context_block = build_context_block(hits)
    contents = build_contents(history, message, context_block)

    resp = _gemini.models.generate_content(
        model=GEN_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
        ),
    )
    return resp.text, build_meta(hits)

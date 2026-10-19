import json
import os
import urllib.error
import urllib.request

EMBED_MODEL = "voyage-4-large"
GEN_MODEL = "gemini-flash-lite-latest"
OUTPUT_DIM = 1024
COLLECTION = "support_qa"
TOP_K = 5
TIMEOUT = 30

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEN_MODEL}:generateContent"
)

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


def _post_json(url, body, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def embed_query(text: str):
    resp = _post_json(
        VOYAGE_URL,
        {
            "input": [text],
            "model": EMBED_MODEL,
            "input_type": "query",
            "output_dimension": OUTPUT_DIM,
        },
        {"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}"},
    )
    return resp["data"][0]["embedding"]


def search_similar(vector):
    try:
        resp = _post_json(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/query",
            {"query": vector, "limit": TOP_K, "with_payload": True},
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise
    return resp["result"]["points"]


def build_context_block(hits):
    if not hits:
        return "(No matching records found.)"
    lines = []
    for h in hits:
        p = h["payload"]
        lines.append(
            f"[benzerlik: {h['score']:.2f}] [{p['category']}/{p['intent']}]\n"
            f"Soru: {p['instruction']}\n"
            f"Cevap: {p['response']}"
        )
    return "\n\n".join(lines)


def build_meta(hits):
    if not hits:
        return "no matching records"
    best = max(h["score"] for h in hits)
    return f"source: {len(hits)} similar records · top match: {best:.2f}"


ROLE_MAP = {"user": "user", "bot": "model"}


def build_contents(history, current_message, context_block):
    contents = []
    for turn in history[:-1]:
        role = ROLE_MAP.get(turn["role"])
        if role is None:
            continue
        contents.append({"role": role, "parts": [{"text": turn["text"]}]})

    augmented = (
        f"Kullanıcının sorusu: {current_message}\n\n"
        f"Benzer geçmiş destek kayıtları:\n{context_block}"
    )
    contents.append({"role": "user", "parts": [{"text": augmented}]})
    return contents


def answer(message: str, history: list[dict]):
    vector = embed_query(message)
    hits = search_similar(vector)
    context_block = build_context_block(hits)
    contents = build_contents(history, message, context_block)

    resp = _post_json(
        GEMINI_URL,
        {
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.3},
        },
        {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    parts = resp["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text:
        raise ValueError("Gemini boş yanıt döndü")
    return text, build_meta(hits)

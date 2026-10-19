"""Sohbet API'si. Statik arayüzü Nginx sunar; burada sadece /api uçları var.

Bellek için bilerek bağımlılıksız: standart kütüphanenin HTTP sunucusu,
Nginx'in arkasında 127.0.0.1'e bağlı çalışır.
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import rag

MAX_BODY = 64 * 1024

log = logging.getLogger("ecomm")


def _parse_chat(raw: bytes):
    """Geçerli istekte (mesaj, geçmiş), değilse None döner."""
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    message = data.get("message")
    history = data.get("history", [])
    if not isinstance(message, str) or not isinstance(history, list):
        return None
    turns = []
    for t in history:
        if not (
            isinstance(t, dict)
            and isinstance(t.get("role"), str)
            and isinstance(t.get("text"), str)
        ):
            return None
        turns.append({"role": t["role"], "text": t["text"]})
    return message.strip(), turns


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ecomm"
    sys_version = ""

    def _send(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"detail": "Not Found"})

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, {"detail": "Not Found"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(411, {"detail": "Content-Length gerekli"})
            return
        if not 0 < length <= MAX_BODY:
            self.close_connection = True
            self._send(413, {"detail": "İstek çok büyük"})
            return
        parsed = _parse_chat(self.rfile.read(length))
        if parsed is None:
            self._send(422, {"detail": "Geçersiz istek"})
            return
        message, history = parsed
        if not message:
            self._send(422, {"detail": "message boş olamaz"})
            return
        try:
            text, meta = rag.answer(message, history)
        except Exception:
            log.exception("yanıt oluşturulamadı")
            self._send(
                502, {"detail": "Yanıt oluşturulamadı, birazdan tekrar deneyin."}
            )
            return
        self._send(200, {"answer": text, "meta": meta})

    def log_message(self, fmt, *args):
        log.info("%s %s", self.address_string(), fmt % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    log.info("dinleniyor: %d", port)
    server.serve_forever()


if __name__ == "__main__":
    main()

import { useEffect, useRef, useState } from "react";

const SUGGESTIONS = [
  "Siparişimi nasıl iptal ederim?",
  "Kargom nerede, takip edebilir miyim?",
  "Şifremi unuttum, nasıl sıfırlarım?",
  "İade sürecim ne kadar sürer?",
  "Kargo ücreti ne kadar?",
  "Yanlış ürün geldi, ne yapmalıyım?",
  "How can I track my order?",
  "¿Cómo restablezco mi contraseña?",
];

function makeTrackingNumber() {
  const n = Math.floor(100000 + Math.random() * 899999);
  return `TR-${n}`;
}

function BarcodeStrip({ bars: fixedBars, className = "" }) {
  const bars = useRef(
    fixedBars || Array.from({ length: 28 }, () => 1 + Math.round(Math.random() * 3))
  ).current;
  return (
    <div className={`flex items-end gap-[2px] h-6 opacity-90 ${className}`} aria-hidden="true">
      {bars.map((w, i) => (
        <span
          key={i}
          className="bg-kraft-100"
          style={{ width: `${w}px`, height: i % 5 === 0 ? "100%" : "70%" }}
        />
      ))}
    </div>
  );
}

function TypingStamp() {
  return (
    <div
      className="relative overflow-hidden border-2 border-stamp/40 rounded-sm bg-kraft-50/60 dark:bg-kraft-900/40 px-4 py-3"
      role="status"
      aria-label="Yanıt hazırlanıyor"
    >
      <div className="relative overflow-hidden flex items-end gap-[2px] h-4 mb-1.5" aria-hidden="true">
        {Array.from({ length: 16 }, (_, i) => (1 + ((i * 7) % 4))).map((w, i) => (
          <span
            key={i}
            className="bg-stamp/50 dark:bg-stamp/60"
            style={{ width: `${w}px`, height: i % 4 === 0 ? "100%" : "60%" }}
          />
        ))}
        <span className="absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-transparent via-kraft-50/90 dark:via-kraft-900/80 to-transparent scan-sweep" />
      </div>
      <p className="font-mono text-[10px] uppercase tracking-wider text-stamp-dark dark:text-stamp">
        kayıt taranıyor…
      </p>
    </div>
  );
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = () => setReduced(mq.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return reduced;
}

function TypewriterText({ text, className }) {
  const reducedMotion = usePrefersReducedMotion();
  const [count, setCount] = useState(reducedMotion ? text.length : 0);

  useEffect(() => {
    if (reducedMotion) {
      setCount(text.length);
      return;
    }
    setCount(0);
    const duration = Math.min(1800, Math.max(400, text.length * 12));
    let start;
    let raf;
    function step(ts) {
      if (start === undefined) start = ts;
      const progress = Math.min(1, (ts - start) / duration);
      setCount(Math.round(progress * text.length));
      if (progress < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, reducedMotion]);

  const done = count >= text.length;
  return (
    <p className={className}>
      {text.slice(0, count)}
      {!done && <span className="inline-block w-[2px] h-[1em] align-text-bottom bg-stamp-dark dark:bg-stamp ml-0.5 dot-blink" />}
    </p>
  );
}

function BotMessage({ text, meta }) {
  return (
    <div className="flex justify-start animate-stamp-in">
      <div className="max-w-[85%] sm:max-w-[70%]">
        <div className="relative border-2 border-stamp/70 text-stamp-dark dark:text-stamp dark:border-stamp/50 rounded-sm px-4 py-3 bg-kraft-50/60 dark:bg-kraft-900/40">
          <TypewriterText
            text={text}
            className="font-body text-[15px] leading-relaxed whitespace-pre-wrap text-ink dark:text-kraft-100"
          />
        </div>
        {meta && (
          <p lang="en" className="mt-1 ml-1 font-mono text-[10px] uppercase tracking-wider text-ink-soft/80 dark:text-kraft-300/70">
            {meta}
          </p>
        )}
      </div>
    </div>
  );
}

function UserMessage({ text }) {
  return (
    <div className="flex justify-end animate-slide-in-label">
      <div className="max-w-[85%] sm:max-w-[70%] relative">
        <p className="font-body text-[15px] leading-relaxed whitespace-pre-wrap text-ink dark:text-kraft-50 px-4 py-2.5 border-b-[3px] border-tape">
          {text}
        </p>
      </div>
    </div>
  );
}

function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex justify-center animate-stamp-in">
      <div className="flex items-center gap-3 border-2 border-dashed border-alert/60 rounded-sm px-4 py-2.5 bg-alert/[0.06]">
        <p className="font-mono text-xs text-alert">{message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 font-mono text-[11px] uppercase tracking-wider text-alert underline decoration-dashed underline-offset-4 hover:text-ink dark:hover:text-kraft-50 transition-colors"
        >
          tekrar dene
        </button>
      </div>
    </div>
  );
}

function EmptyState({ tracking, onPick }) {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-7 px-4 py-6">
      <div className="relative animate-label-in">
        <div className="w-[19rem] sm:w-80 border-2 border-dashed border-kraft-300 dark:border-kraft-300/30 bg-kraft-100/50 dark:bg-kraft-800/40 px-5 py-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-ink-soft/80 dark:text-kraft-300/70">
            Gönderi No
          </p>
          <p className="font-display font-bold text-2xl tracking-wide text-ink dark:text-kraft-50 mt-0.5">
            {tracking}
          </p>
          <div className="flex items-center gap-1.5 mt-2.5 mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-stamp inline-block" />
            <p className="font-mono text-[10px] uppercase tracking-wider text-stamp-dark dark:text-stamp">
              durum: yanıt bekleniyor
            </p>
          </div>
          <BarcodeStrip
            className="[&>span]:bg-kraft-300 dark:[&>span]:bg-kraft-300/40"
            bars={[2, 1, 3, 1, 1, 2, 3, 1, 2, 1, 1, 3, 2, 1, 2, 3, 1, 1, 2, 1, 3, 1, 2, 2, 1, 3, 1, 2]}
          />
        </div>
      </div>

      <div className="text-center max-w-xs animate-label-in" style={{ animationDelay: "80ms" }}>
        <p className="font-display font-semibold uppercase tracking-wide text-ink dark:text-kraft-100 text-base leading-snug">
          Sorunu gönder, cevabın yolda
        </p>
      </div>

      <div className="w-full">
        <p className="font-mono text-[10px] uppercase tracking-[0.15em] text-ink-soft/60 dark:text-kraft-300/50 text-center mb-2.5">
          Sık sorulan gönderiler
        </p>
        <div className="flex flex-wrap gap-2 justify-center">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={s}
              onClick={() => onPick(s)}
              style={{ animationDelay: `${140 + i * 55}ms` }}
              className="animate-label-in font-mono text-xs px-3 py-1.5 border border-dashed border-kraft-300 text-ink-soft dark:text-kraft-200 dark:border-kraft-300/40 hover:border-tape hover:text-tape-dark dark:hover:text-tape hover:-translate-y-0.5 active:translate-y-0 active:scale-95 transition-all"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [tracking] = useState(makeTrackingNumber);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);
  const contentRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy, error]);

  // Keep the thread pinned to the bottom while a message's height grows
  // (typewriter reveal), as long as the reader hasn't scrolled up to look back.
  useEffect(() => {
    const container = scrollRef.current;
    const content = contentRef.current;
    if (!container || !content) return;
    const ro = new ResizeObserver(() => {
      const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
      if (distanceFromBottom < 120) {
        container.scrollTop = container.scrollHeight;
      }
    });
    ro.observe(content);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setError(null);
    const nextHistory = [...messages, { role: "user", text: trimmed }];
    setMessages(nextHistory);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          history: nextHistory.map((m) => ({ role: m.role, text: m.text })),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((cur) => [
        ...cur,
        { role: "bot", text: data.answer, meta: data.meta },
      ]);
    } catch (e) {
      setError({
        message: "Şu anda yanıt alınamadı. Bağlantını kontrol edip tekrar dene.",
        failedMessage: trimmed,
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-[100dvh] sm:min-h-screen bg-kraft-200 dark:bg-kraft-950 flex items-center justify-center p-0 sm:p-6 font-body">
      <div className="animate-app-in paper-grain w-full max-w-2xl h-[100dvh] sm:h-[85vh] bg-kraft-50 dark:bg-kraft-900 shadow-2xl shadow-black/20 flex flex-col overflow-hidden">
        <div className="bg-ink dark:bg-kraft-950 px-4 sm:px-5 pt-3.5 sm:pt-4 pb-3 shrink-0">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="font-display font-bold uppercase tracking-[0.08em] sm:tracking-[0.14em] text-kraft-50 text-base sm:text-lg leading-tight truncate">
                Sipariş Destek Hattı
              </p>
              <p className="font-mono text-[10px] sm:text-[11px] text-tape mt-1.5 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-stamp inline-block shrink-0" />
                <span className="truncate">çevrimiçi &nbsp;·&nbsp; kayıt no {tracking}</span>
              </p>
            </div>
            <BarcodeStrip className="hidden sm:flex shrink-0" />
          </div>
        </div>
        <div className="h-2 perforated-bottom bg-ink dark:bg-kraft-950 shrink-0" />

        <div
          ref={scrollRef}
          className="thread-scroll flex-1 overflow-y-auto px-4 sm:px-5 py-5"
          role="log"
          aria-live="polite"
          aria-label="Sohbet geçmişi"
        >
          {messages.length === 0 && <EmptyState tracking={tracking} onPick={send} />}

          <div ref={contentRef} className="space-y-4">
          {messages.map((m, i) =>
            m.role === "user" ? (
              <UserMessage key={i} text={m.text} />
            ) : (
              <BotMessage key={i} text={m.text} meta={m.meta} />
            )
          )}

          {busy && (
            <div className="flex justify-start">
              <TypingStamp />
            </div>
          )}

          {error && (
            <ErrorBanner message={error.message} onRetry={() => send(error.failedMessage)} />
          )}
          </div>
        </div>

        <div className="p-3 sm:p-4 bg-kraft-100 dark:bg-kraft-800 border-t border-dashed border-kraft-300 dark:border-kraft-300/20 shrink-0">
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder="Sorunuzu buraya yazın…"
              aria-label="Sorunuzu buraya yazın"
              className="no-scrollbar flex-1 resize-none bg-transparent border border-dashed border-kraft-300 dark:border-kraft-300/30 px-3 py-2.5 text-[15px] text-ink dark:text-kraft-50 placeholder:text-ink-soft/50 focus:outline-none focus-visible:border-tape focus-visible:outline-2 focus-visible:outline-tape-dark focus-visible:outline-offset-2 font-body max-h-[120px]"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              aria-label="Gönder"
              className="shrink-0 w-11 h-11 grid place-items-center bg-tape hover:bg-tape-dark disabled:opacity-40 disabled:hover:bg-tape transition-colors text-ink font-display font-bold text-lg rotate-1 hover:rotate-0 active:scale-90"
            >
              →
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { aiApi } from "../services/api.js";
import BookCard from "./BookCard.jsx";

const SUGGESTIONS = [
  "What should I read after Harry Potter?",
  "I want a beginner-friendly AI book.",
  "Give me books under 300 pages.",
];

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    aiApi
      .getChatHistory()
      .then((res) => {
        if (cancelled) return;
        setMessages(res.data.messages.map((m) => ({ role: m.role, message: m.message })));
      })
      .catch(() => {
        /* fail quiet — chat still works, just starts without prior history */
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  async function sendMessage(text) {
    if (!text.trim() || isSending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", message: text }]);
    setIsSending(true);
    try {
      const res = await aiApi.chat(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: res.data.reply, books: res.data.books },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: "Something went wrong — please try again.", books: [] },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex h-[70vh] flex-col overflow-hidden rounded-lg border border-parchment/10 bg-ink-panel">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-5">
        {isLoadingHistory && <p className="text-sm text-parchment/40">Loading conversation…</p>}

        {!isLoadingHistory && messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <Sparkles className="h-6 w-6 text-brass/60" strokeWidth={1.5} />
            <p className="max-w-xs text-sm text-parchment/50">
              Ask for recommendations grounded in Lexora's catalog — nothing invented.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="rounded-full border border-parchment/15 px-3 py-1.5 text-xs text-parchment/70 hover:bg-parchment/5"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user" ? "bg-brass text-ink" : "bg-ink text-parchment/90"
              }`}
            >
              <p>{m.message}</p>
              {m.books?.length > 0 && (
                <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
                  {m.books.map((book) => (
                    <div key={book.id} className="w-28 shrink-0">
                      <BookCard book={book} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isSending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-ink px-4 py-2.5 text-sm text-parchment/50">
              Thinking…
            </div>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="flex gap-2 border-t border-parchment/10 p-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Lexora for a recommendation…"
          className="flex-1 rounded-full border border-parchment/15 bg-ink px-4 py-2.5 text-sm text-parchment placeholder:text-parchment/35 focus:border-brass/50"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="brass-btn !px-4 disabled:opacity-50"
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}

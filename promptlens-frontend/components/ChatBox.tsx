"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const starterPrompts = [
  "What patterns do you see in failed prompts?",
  "How can I improve reliability for multilingual prompts?",
  "Suggest a better prompt for summarizing customer reviews.",
];

function parseAssistantMessage(payload: unknown): string {
  if (typeof payload === "string") {
    return payload;
  }

  if (!payload || typeof payload !== "object") {
    return "I could not understand the server response.";
  }

  const candidate = payload as Record<string, unknown>;

  if (typeof candidate.response === "string") return candidate.response;
  if (typeof candidate.answer === "string") return candidate.answer;
  if (typeof candidate.message === "string") return candidate.message;

  return JSON.stringify(payload, null, 2);
}

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to PromptLens Chat. Ask for diagnostics, rewrites, or strategy recommendations for your prompts.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messageContainerRef.current?.scrollTo({
      top: messageContainerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const submitQuery = async (query: string) => {
    if (!query || loading) {
      return;
    }

    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(query);
      const content = parseAssistantMessage(response);
      setMessages((prev) => [...prev, { role: "assistant", content }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to send message.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();

    const query = input.trim();
    await submitQuery(query);
  };

  const sendStarterPrompt = async (prompt: string) => {
    await submitQuery(prompt);
  };

  return (
    <div className="card-glow grid h-[75vh] grid-rows-[auto_1fr_auto] gap-4 rounded-3xl p-4 sm:p-6">
      <div className="flex flex-wrap gap-2">
        {starterPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => sendStarterPrompt(prompt)}
            className="rounded-full border border-cyan-300/25 bg-cyan-400/10 px-3 py-1.5 text-xs text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-400/15"
          >
            {prompt}
          </button>
        ))}
      </div>

      <div
        ref={messageContainerRef}
        className="space-y-3 overflow-y-auto rounded-2xl border border-slate-800/70 bg-slate-950/55 p-3 pr-2"
      >
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 shadow ${
              message.role === "user"
                ? "ml-auto border border-cyan-300/25 bg-cyan-400/15 text-cyan-50"
                : "mr-auto border border-emerald-300/20 bg-emerald-400/10 text-emerald-50"
            }`}
          >
            {message.content}
          </div>
        ))}

        {loading && (
          <div className="mr-auto inline-flex items-center gap-2 rounded-2xl border border-emerald-300/20 bg-emerald-400/15 px-4 py-3 text-sm text-emerald-100">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-200 border-t-transparent" />
            PromptLens is thinking...
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="space-y-2">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-950/90 px-3 py-2.5 text-slate-100 outline-none transition focus:border-cyan-300 focus:ring-4 focus:ring-cyan-400/15"
            placeholder="Ask about model trends, failures, or language behavior..."
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-linear-to-r from-cyan-300 to-emerald-300 px-4 py-2.5 font-semibold text-slate-900 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Send
          </button>
        </div>
        {error && <p className="text-sm text-rose-300">{error}</p>}
      </form>
    </div>
  );
}

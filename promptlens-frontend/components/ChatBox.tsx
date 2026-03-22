"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const starterPrompts = [
  "Which programming language has the lowest execution reliability?",
  "What is the average success rate for gpt-4 in the last 7 days?",
  "List the best performing models for creative tasks.",
];

function parseAssistantMessage(payload: unknown): string {
  if (typeof payload === "string") return payload;
  if (!payload || typeof payload !== "object") return "[ERROR] Unrecognized payload schema.";

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
        "[SYSTEM STATUS: ONLINE]\nEstablishing connection to Llama-3 Query Agent...\nConnection secure. Awaiting analytical directives.",
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
    if (!query || loading) return;

    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChatMessage(query);
      const content = parseAssistantMessage(response);
      setMessages((prev) => [...prev, { role: "assistant", content }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inference pipeline timeout.");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    await submitQuery(input.trim());
  };

  return (
    <div className="metric-card bg-slate-900 border-slate-700 flex flex-col h-[70vh] rounded-lg shadow-inner">
      <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-slate-800">
        {starterPrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => submitQuery(prompt)}
            className="rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-[10px] uppercase tracking-wider text-slate-400 transition hover:bg-slate-700 hover:text-purple-300"
          >
            {prompt.length > 40 ? prompt.substring(0, 40) + "..." : prompt}
          </button>
        ))}
      </div>

      <div
        ref={messageContainerRef}
        className="flex-1 overflow-y-auto space-y-4 pr-2 font-mono text-sm leading-relaxed"
      >
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[90%] rounded p-4 border ${
              message.role === "user"
                ? "ml-auto bg-slate-800 border-slate-700 text-slate-200"
                : "mr-auto bg-slate-950 border-purple-900/50 text-slate-300"
            }`}
          >
            <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2 font-sans font-bold">
               {message.role === "user" ? "User.Query" : "Llama-3.Response"}
            </div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}

        {loading && (
          <div className="mr-auto inline-flex items-center gap-3 rounded p-4 bg-slate-950 border border-purple-900/50 text-slate-400 text-sm font-mono">
            <span className="w-1.5 h-4 bg-purple-500 animate-pulse" />
            Agent evaluating schema...
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="mt-4 pt-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <span className="text-purple-500 font-mono font-bold">{">"}</span>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            className="w-full bg-transparent text-slate-200 font-mono text-sm outline-none placeholder:text-slate-600 focus:placeholder:text-slate-700"
            placeholder="Input natural language prompt..."
            autoComplete="off"
            spellCheck="false"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-purple-600 text-white font-bold text-[10px] uppercase tracking-widest rounded transition-colors hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Execute
          </button>
        </div>
        {error && <p className="text-[11px] text-red-500 font-mono mt-3 uppercase tracking-wider">{error}</p>}
      </form>
    </div>
  );
}

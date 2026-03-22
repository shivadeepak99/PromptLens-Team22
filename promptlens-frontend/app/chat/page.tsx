import ChatBox from "@/components/ChatBox";

export default function ChatPage() {
  return (
    <section className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8 sm:px-6">
      <header className="card-glow rounded-3xl p-6 sm:p-8">
        <span className="rounded-full border border-cyan-300/30 bg-cyan-400/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-cyan-100">
          Copilot Assistant
        </span>
        <h1 className="headline-gradient mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">AI Chat</h1>
        <p className="mt-2 text-slate-300">Discuss prompt quality, trends, and optimization ideas with PromptLens.</p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_290px]">
        <ChatBox />
        <aside className="card-glow rounded-3xl p-5">
          <h2 className="text-sm uppercase tracking-[0.18em] text-emerald-200">How to get better answers</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
            <li>Ask one specific objective per message.</li>
            <li>Include domain constraints and expected output format.</li>
            <li>Request alternatives to compare prompt strategies.</li>
            <li>Follow up with failure examples for targeted fixes.</li>
          </ul>
        </aside>
      </div>
    </section>
  );
}

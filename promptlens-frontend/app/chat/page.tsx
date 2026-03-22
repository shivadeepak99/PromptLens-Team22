import ChatBox from "@/components/ChatBox";

export default function ChatPage() {
  return (
    <section className="mx-auto w-full max-w-6xl space-y-6 px-4 py-8 xl:px-8">
      <header className="metric-card bg-slate-800/80 p-6 sm:p-8 rounded-lg">
        <span className="rounded border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-purple-400">
          Agent Workspace
        </span>
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-100">Natural Language Datamart Query</h1>
        <p className="mt-2 text-sm text-slate-400 max-w-3xl leading-relaxed">
          Direct secure conduit to the PromptLens Llama-3 Query Agent. Generate synthetic SQL, request analytical summaries, and parse datamart schemas dynamically without writing code.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <ChatBox />
        
        <div className="space-y-6">
           <aside className="metric-card bg-slate-900 border-slate-700 p-5 rounded-lg shadow-inner">
             <h2 className="text-[11px] font-bold uppercase tracking-widest text-slate-500 mb-4 border-b border-slate-700 pb-2">Execution Constraints</h2>
             <ul className="space-y-3 text-[13px] leading-relaxed text-slate-300">
               <li className="flex gap-2">
                 <span className="text-purple-400 font-mono">01</span>
                 <span>Limit queries to single atomic analytics operations.</span>
               </li>
               <li className="flex gap-2">
                 <span className="text-purple-400 font-mono">02</span>
                 <span>Define strict SQL table constraints (e.g. "from mv_top_prompt_templates").</span>
               </li>
               <li className="flex gap-2">
                 <span className="text-purple-400 font-mono">03</span>
                 <span>Outputs evaluate on historical state; direct mutations disabled.</span>
               </li>
               <li className="flex gap-2">
                 <span className="text-purple-400 font-mono">04</span>
                 <span>Latency bounded to 30s per model inference queue.</span>
               </li>
             </ul>
           </aside>
           
           <aside className="metric-card bg-slate-800/50 border-slate-700 p-5 rounded-lg">
              <h2 className="text-[11px] font-bold uppercase tracking-widest text-emerald-500 mb-4 border-b border-slate-700 pb-2">Datamart Tables Available</h2>
              <div className="flex flex-wrap gap-2">
                 <span className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[10px] font-mono text-slate-400">mv_daily_model_success</span>
                 <span className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[10px] font-mono text-slate-400">mv_model_performance_arena</span>
                 <span className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[10px] font-mono text-slate-400">mv_language_performance</span>
              </div>
           </aside>
        </div>
      </div>
    </section>
  );
}

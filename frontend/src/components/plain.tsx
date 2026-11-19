import type { ReactNode } from "react";
import { describe, term, type Level } from "../lib/plain";
import { COLOURS } from "../lib/data";

// One-line takeaway shown at the top of every tab.
export function Takeaway({ children }: { children: ReactNode }) {
  return (
    <div className="mb-6 rounded-lg border-l-8 border-slate-800 bg-slate-50 px-4 py-3" data-read>
      <div className="text-sm font-semibold uppercase tracking-wide text-slate-500">In one line</div>
      <p className="mt-1 font-serif text-2xl font-bold leading-snug text-slate-900">{children}</p>
    </div>
  );
}

export function HowToRead({ children }: { children: ReactNode }) {
  return (
    <p className="mb-2 text-base text-slate-700" data-read>
      <span className="font-semibold">How to read this: </span>{children}
    </p>
  );
}

export function Means({ children }: { children: ReactNode }) {
  return (
    <div className="mt-2 rounded-lg border border-slate-300 bg-white px-4 py-3" data-read>
      <div className="text-sm font-semibold uppercase tracking-wide text-slate-600">What this means</div>
      <p className="mt-1 text-base leading-relaxed text-slate-900">{children}</p>
    </div>
  );
}

// Small line that keeps the technical name next to the plain one.
export function Tech({ k, children }: { k?: string; children?: ReactNode }) {
  const t = k ? term(k) : null;
  return (
    <span className="mt-0.5 block text-xs text-slate-500" title={t?.define}>
      Technical term: {children ?? t?.tech}
    </span>
  );
}

// Plain label with an info tooltip (title + focusable for keyboard users).
export function Label({ k }: { k: string }) {
  const t = term(k);
  return (
    <span>
      {t.plain}{" "}
      <span tabIndex={0} role="img" aria-label={`${t.tech}: ${t.define}`} title={`${t.tech}: ${t.define}`}
        className="cursor-help rounded-full border border-slate-400 px-1.5 text-xs text-slate-600">i</span>
    </span>
  );
}

// Technical detail kept out of the main view.
export function Experts({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="mb-6 rounded-lg border border-slate-300 bg-slate-50">
      <summary className="cursor-pointer select-none px-4 py-2 font-semibold text-slate-700">For experts: {title}</summary>
      <div className="border-t border-slate-200 bg-white p-3">{children}</div>
    </details>
  );
}

const BADGE: Record<Level, { icon: string; text: string; cls: string }> = {
  good: { icon: "✔", text: "Good", cls: "border-emerald-700 bg-emerald-50 text-emerald-800" },
  caution: { icon: "!", text: "Caution", cls: "border-warn-500 bg-warn-100 text-warn-700" },
  poor: { icon: "✖", text: "Poor", cls: "border-violet-700 bg-violet-50 text-violet-800" },
};
export function Status({ level }: { level: Level }) {
  const b = BADGE[level];
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded border px-1.5 py-0.5 text-sm font-semibold ${b.cls}`}>
      <span aria-hidden>{b.icon}</span>{b.text}
    </span>
  );
}

export function ModelName({ m, short = false }: { m: string; short?: boolean }) {
  const d = describe(m);
  return (
    <span className="inline-flex items-start gap-2">
      <span className="mt-1.5 inline-block h-3 w-3 shrink-0 rounded-sm" style={{ background: COLOURS[m] }} aria-hidden />
      <span>
        <span className="font-semibold">{m}</span>
        <span className="block text-xs text-slate-600">{d.kind}{short ? "" : ` · ${d.detail}`}</span>
      </span>
    </span>
  );
}

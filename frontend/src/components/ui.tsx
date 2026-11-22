import type { ReactNode } from "react";
import { initials } from "../lib/store";

export function Loading({ what = "data" }: { what?: string }) {
  return <div className="card animate-pulse p-6 text-slate-500">Loading {what}…</div>;
}

export function ErrorBox({ error }: { error: string }) {
  return <div className="rounded-xl border border-warn-500 bg-warn-100 p-4 text-warn-700">Could not load data: {error}</div>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-slate-500">{children}</div>;
}

// White card with a coloured top rule for model family cards (GARCH red, ML blue, warning amber).
export function Card({ title, children, tone = "plain" }: {
  title: string; children: ReactNode; tone?: "plain" | "garch" | "ml" | "warn";
}) {
  const rule = { plain: "", garch: "border-t-4 border-t-garch-500", ml: "border-t-4 border-t-ml-500", warn: "border-t-4 border-t-warn-500" };
  return (
    <div className={`card p-5 ${rule[tone]}`}>
      <div className="text-[13px] font-semibold uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-2 text-base leading-snug text-slate-900">{children}</div>
    </div>
  );
}

export function Section({ title, children, note }: { title: string; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="mb-3 text-xl font-bold tracking-[-0.3px] text-navy-900">{title}</h2>
      {note && <p className="mb-4 max-w-4xl text-slate-600">{note}</p>}
      {children}
    </section>
  );
}

// KPI card: one big number with a small grey caption (numbers always come from the data files).
export function Kpi({ value, caption, sub, tone }: { value: ReactNode; caption: ReactNode; sub?: ReactNode; tone?: "garch" | "ml" | "warn" }) {
  const dot = tone === "garch" ? "bg-garch-500" : tone === "ml" ? "bg-ml-500" : tone === "warn" ? "bg-warn-500" : "bg-slate-300";
  return (
    <div className="card flex flex-col p-5" data-read>
      <div className="flex items-center gap-2 text-[13px] font-medium text-slate-500"><span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden />{caption}</div>
      <div className="kpi mt-3 text-navy-900">{value}</div>
      {sub && <div className="mt-2 text-[13px] text-slate-500">{sub}</div>}
    </div>
  );
}

// Outline pills; the selected pill is filled dark (navy). Used for time ranges and sector filters.
export function Pills<T extends string>({ options, value, onChange, label }: {
  options: { value: T; label: string }[]; value: T; onChange: (v: T) => void; label: string;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} onClick={() => onChange(o.value)} aria-pressed={value === o.value}
          className={`rounded-full border px-3 py-1 text-[13px] font-medium ${value === o.value ? "border-navy-900 bg-navy-900 text-white" : "border-slate-300 bg-white text-slate-700 hover:border-navy-900"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function StockBadge({ ticker }: { ticker: string }) {
  return (
    <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px] font-bold text-navy-900" aria-hidden>
      {initials(ticker)}
    </span>
  );
}

export function Select<T extends string>({ label, value, options, onChange }: {
  label: string; value: T; options: { value: T; label: string }[]; onChange: (v: T) => void;
}) {
  return (
    <label className="flex min-w-0 max-w-full flex-col text-[13px] font-medium text-slate-600">
      {label}
      <select
        className="mt-1 w-full max-w-full rounded-lg border border-line bg-white px-2 py-1.5 text-[15px] text-slate-900"
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

export function Table({ head, rows, rowClass }: {
  head: string[]; rows: (string | number)[][]; rowClass?: (i: number) => string;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-white">
      <table className="w-full text-sm">
        <thead className="text-left text-[13px] text-slate-500">
          <tr>{head.map((h) => <th key={h} className="whitespace-nowrap font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={`border-t border-line ${i % 2 ? "bg-slate-50" : ""} ${rowClass ? rowClass(i) : ""}`}>
              {r.map((c, j) => <td key={j} className={j === 0 ? "whitespace-nowrap font-medium" : "whitespace-nowrap"}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

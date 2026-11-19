import type { ReactNode } from "react";

export function Loading({ what = "data" }: { what?: string }) {
  return <div className="animate-pulse rounded border border-slate-200 bg-slate-50 p-6 text-slate-500">Loading {what}…</div>;
}

export function ErrorBox({ error }: { error: string }) {
  return <div className="rounded border border-warn-500 bg-warn-100 p-4 text-warn-700">Could not load data: {error}</div>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded border border-dashed border-slate-300 p-6 text-slate-500">{children}</div>;
}

export function Card({ title, children, tone = "plain" }: {
  title: string; children: ReactNode; tone?: "plain" | "garch" | "ml" | "warn";
}) {
  const tones = {
    plain: "border-slate-200 bg-white",
    garch: "border-garch-100 bg-garch-50",
    ml: "border-ml-100 bg-ml-50",
    warn: "border-warn-500 bg-warn-100",
  };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</div>
      <div className="mt-2 text-lg leading-snug">{children}</div>
    </div>
  );
}

export function Section({ title, children, note }: { title: string; children: ReactNode; note?: ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="mb-1 font-serif text-2xl font-bold">{title}</h2>
      {note && <p className="mb-4 max-w-4xl text-slate-600">{note}</p>}
      {children}
    </section>
  );
}

export function Select<T extends string>({ label, value, options, onChange }: {
  label: string; value: T; options: { value: T; label: string }[]; onChange: (v: T) => void;
}) {
  return (
    <label className="flex min-w-0 max-w-full flex-col text-sm font-medium text-slate-700">
      {label}
      <select
        className="mt-1 w-full max-w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-base"
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
    <div className="overflow-x-auto rounded border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>{head.map((h) => <th key={h} className="whitespace-nowrap font-semibold">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={`border-t border-slate-100 ${rowClass ? rowClass(i) : ""}`}>
              {r.map((c, j) => <td key={j} className={j === 0 ? "whitespace-nowrap font-medium" : "whitespace-nowrap"}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

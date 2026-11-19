import { Section } from "../components/ui";
import { Takeaway } from "../components/plain";
import { TERMS } from "../lib/plain";
import { useJson, type Meta } from "../lib/data";

export function Limits() {
  const meta = useJson<Meta>("meta.json");
  return (
    <div className="mb-8 rounded-lg border-2 border-warn-500 bg-warn-100 p-4" data-read>
      <h2 className="font-serif text-2xl font-bold">Limits of this study</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-lg">
        <li>We have only about 710 test days per stock. That is enough to see broad patterns. It is small for one stock alone.</li>
        <li>We used only {meta.data?.n_stocks ?? "the"} stocks: those with prices since 2015. Newer firms are left out.</li>
        <li>Past data does not promise the future. A new kind of crisis could change these results.</li>
        <li>The models do not yet use interest rates, price rises or factory output.</li>
        <li>Prices come from Yahoo Finance. It is free, but it is not an official source.</li>
        <li>These are draft results. Our project guide has not yet approved them.</li>
      </ul>
    </div>
  );
}

export default function Glossary() {
  return (
    <>
      <Takeaway>Every term on this site, in one plain sentence each.</Takeaway>
      <Section title="Glossary">
        <dl className="grid gap-3 md:grid-cols-2">
          {TERMS.map((t) => (
            <div key={t.key} className="rounded-lg border border-slate-200 p-3" data-read>
              <dt className="text-lg font-semibold">{t.plain}</dt>
              <dd className="mt-1 text-base">{t.define}</dd>
              <dd className="mt-1 text-xs text-slate-500">Technical term: {t.tech}</dd>
            </div>
          ))}
        </dl>
      </Section>
      <Limits />
    </>
  );
}

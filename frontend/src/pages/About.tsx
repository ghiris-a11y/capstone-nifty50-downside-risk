import { Section, Table } from "../components/ui";
import { Experts, Takeaway } from "../components/plain";
import { Limits } from "./Glossary";
import { pct, useJson, type Meta } from "../lib/data";

interface Excl { ticker: string; name: string; sector: string; reason: string }
interface Review { ticker: string; date: string; log_move: number; nifty_move: number; classification: string; note: string | null; triggered_exclusion: boolean }

export default function About() {
  const meta = useJson<Meta>("meta.json");
  const excl = useJson<Excl[]>("excluded.json");
  const rev = useJson<Review[]>("exclusion_review.json");
  const m = meta.data;
  return (
    <>
      <Takeaway>How we did the study, and what it cannot tell you.</Takeaway>
      <Section title="How the study was done">
        <ul className="max-w-3xl list-disc space-y-1 pl-6 text-lg" data-read>
          <li>We used {m?.n_stocks ?? "the"} Nifty 50 stocks that have daily prices from 2015 onwards. We left out {m?.n_excluded ?? "some"} others. They listed later, or their price data had errors.</li>
          <li>Each model forecast one day ahead. It used only what was known the evening before.</li>
          <li>The models learned from 2015 to 2021. We made our choices on 2022 and 2023. We tested on {m?.test_start?.slice(0, 4) ?? "2024"} to {m?.data_last?.slice(0, 4) ?? "2026"}.</li>
          <li>We say “closest to expected”, not “best”. We call a gap real only when a standard check says so.</li>
          <li>All report numbers come from one locked copy of the data, so anyone can repeat them.</li>
        </ul>
      </Section>
      <Limits />
      <Experts title="method in technical terms">
      <Section title="Method">
        <ul className="list-disc space-y-1 pl-6 text-slate-800">
          <li>Balanced panel of {m?.n_stocks ?? "…"} Nifty 50 stocks with full daily history from 2015 ({m?.n_excluded ?? "…"} candidates excluded; see below).</li>
          <li>Train to {m?.train_end}, validation to {m?.val_end}, test from {m?.test_start} to {m?.data_last}. One-day-ahead forecasts.</li>
          <li>Models: GARCH, EGARCH and GJR-GARCH with Normal and Student-t errors (refitted every 20 days); XGBoost quantile regression; Random Forest and MLP volatility models with filtered historical simulation; 250-day historical simulation as a benchmark.</li>
          <li>Features at day t use information up to t−1 only. Seeds fixed at 42. All report numbers come from a frozen snapshot with SHA-256 hashes ({m?.snapshot_utc}).</li>
          <li>Backtests: Kupiec and Christoffersen at 95% and 99%; Basel traffic-light zones at 99% only; pinball and Fissler-Ziegel (FZ0) losses; Diebold-Mariano tests on FZ0 and pinball loss.</li>
          <li>Wording: breach rates are described as closest to nominal, not as wins; forecast-quality differences are stated only where Diebold-Mariano tests find them.</li>
        </ul>
      </Section>
      <Section title="Limitations">
        <ul className="list-disc space-y-1 pl-6 text-slate-800">
          <li>{m?.approval_note}</li>
          <li>{m?.macro_note}</li>
          <li>About 710 test days per stock: a 99% backtest expects about 7 breaches per stock, so single-stock tests have low power.</li>
          <li>Survivorship: the balanced panel keeps only stocks listed since 2015 and in the index in December 2025.</li>
          <li>Yahoo Finance data are unofficial; corporate actions are not always adjusted (see the exclusion review).</li>
          <li>Only derived values (returns, VaR/ES, test results) are published here; no raw price series.</li>
        </ul>
      </Section>
      </Experts>
      <Experts title="excluded stocks and the review of large one-day moves">
      <Section title="Excluded stocks">
        {excl.data && <Table head={["Stock", "Name", "Sector", "Reason"]} rows={excl.data.map((e) => [e.ticker, e.name, e.sector, e.reason])} />}
      </Section>
      <Section title="Review of the moves that triggered exclusion"
        note="Event notes come from general knowledge and need a cited source before they are used in the report.">
        {rev.data && (
          <Table head={["Stock", "Date", "Move", "Nifty", "Triggered exclusion", "Assessment", "Note"]}
            rows={rev.data.map((r) => [r.ticker, r.date, pct(r.log_move, 1), pct(r.nifty_move, 1), r.triggered_exclusion ? "yes" : "no", r.classification, r.note ?? ""])} />
        )}
      </Section>
      </Experts>
    </>
  );
}

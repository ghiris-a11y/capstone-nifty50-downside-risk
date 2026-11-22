import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import Overview from "./pages/Overview";
import Start from "./pages/Start";
import Glossary from "./pages/Glossary";
import Models from "./pages/Models";
import Regimes from "./pages/Regimes";
import Stock from "./pages/Stock";
import Features from "./pages/Features";
import Live from "./pages/Live";
import About from "./pages/About";
import Icon from "./components/icons";
import { COLOURS, ORDER, useJson, type Meta } from "./lib/data";
import { useStore } from "./lib/store";

// Tab names and routes are unchanged; the last two are the secondary group.
const TABS = [
  ["/", "Start here", "start"],
  ["/overview", "Results at a glance", "overview"],
  ["/models", "Model comparison", "models"],
  ["/regimes", "Calm vs stressed days", "regimes"],
  ["/stock", "One stock up close", "stock"],
  ["/features", "What drives the forecasts", "features"],
  ["/glossary", "Glossary", "glossary"],
  ["/live", "Daily example", "live"],
  ["/about", "About & limits", "about"],
] as const;
const SECONDARY = new Set(["/live", "/about"]);
export const PROJECT_TITLE =
  "Comparative Predictive Analytics of Downside Risk in NSE Nifty 50 Stocks: Machine Learning vs. GARCH Models";
export const REPO_URL = "https://github.com/ghiris-a11y/capstone-nifty50-downside-risk";
interface StockInfo { ticker: string; name: string; sector: string }

// Mark: a loss limit (dashed line) with a few days that broke through it, drawn as a ledger stamp.
function Mark() {
  return (
    <svg viewBox="0 0 28 28" className="h-7 w-7 shrink-0" aria-hidden>
      <rect x="1" y="1" width="26" height="26" fill="#1d1b16" />
      <path d="M5 18h18" stroke="#d18f00" strokeWidth="1.5" strokeDasharray="2 2" />
      <path d="M6 13v3M10 11v5M14 14v2M18 9v7" stroke="#FFFDF8" strokeWidth="2" />
      <path d="M22 16v6" stroke="#cb181d" strokeWidth="2" />
    </svg>
  );
}

// Model ribbon: the ten models in their chart colours (GARCH reds, benchmark grey, ML blues), a signature strip
// that also teaches the colour code used in every chart.
function Ribbon() {
  return (
    <div className="flex h-[5px] w-full" aria-hidden>
      {ORDER.map((m) => <span key={m} className="flex-1" style={{ background: COLOURS[m] }} title={m} />)}
    </div>
  );
}

function Wordmark({ small = false }: { small?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <Mark />
      <span className="leading-none">
        <span className={`display block whitespace-nowrap font-bold text-navy-900 ${small ? "text-[14px]" : "text-[15px]"}`}>Nifty 50 Downside Risk</span>
        <span className="label mt-1 block whitespace-nowrap text-[10px] text-slate-500">Risk ledger</span>
      </span>
    </span>
  );
}

function Nav({ onPick }: { onPick?: () => void }) {
  // contents-page style: a running number, the label, and an ink bar on the open tab
  const item = (to: string, label: string, n: number) => (
    <NavLink key={to} to={to} end={to === "/"} onClick={onPick}
      className={({ isActive }) =>
        `group flex min-h-[40px] items-center gap-3 border-l-[3px] py-2 pl-3 pr-2 text-[15px] ${isActive ? "border-navy-900 bg-page font-semibold text-navy-900" : "border-transparent text-slate-600 hover:border-line hover:text-navy-900"}`}>
      <span className="label w-6 shrink-0 text-[11px] text-slate-400 group-hover:text-navy-900">{String(n).padStart(2, "0")}</span>{label}
    </NavLink>
  );
  const main = TABS.filter(([to]) => !SECONDARY.has(to)), more = TABS.filter(([to]) => SECONDARY.has(to));
  return (
    <nav className="flex flex-col gap-0.5">
      {main.map(([to, l], i) => item(to, l, i + 1))}
      <div className="label mt-5 border-t border-line px-3 pb-1 pt-3 text-[11px] text-slate-400">More</div>
      {more.map(([to, l], i) => item(to, l, main.length + i + 1))}
    </nav>
  );
}

function Search() {
  const { query, setQuery, setTicker } = useStore();
  const stocks = useJson<StockInfo[]>("stocks.json");
  const go = useNavigate();
  const pick = (v: string) => {
    setQuery(v);
    const q = v.trim().toUpperCase();
    const hit = stocks.data?.find((s) => s.ticker.replace(".NS", "") === q || s.name.toUpperCase() === q);
    if (hit) { setTicker(hit.ticker); go("/stock"); }
  };
  return (
    <label className="flex w-full max-w-sm items-center gap-2 rounded-lg bg-page px-3 py-2 text-slate-500">
      <Icon name="search" className="h-4 w-4 shrink-0" />
      <input list="stock-list" value={query} onChange={(e) => pick(e.target.value)} placeholder="Find a stock"
        aria-label="Find a stock (filters the stock list)" className="w-full min-w-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400" />
      <datalist id="stock-list">
        {stocks.data?.map((s) => <option key={s.ticker} value={s.ticker.replace(".NS", "")}>{s.name}</option>)}
      </datalist>
    </label>
  );
}

function FooterCols({ meta }: { meta?: Meta }) {
  const cols: [string, JSX.Element][] = [
    ["Data", <>
      <p>Locked data copy: {meta?.snapshot_utc ?? "not available"}</p>
      {meta?.results_generated_utc && <p>Results made: {meta.results_generated_utc}</p>}
      {meta?.live_as_of && <p>Daily example: prices up to {meta.live_as_of}</p>}
      <p>Yahoo Finance. Only returns and risk numbers are shown, no prices.</p>
    </>],
    ["Project", <>
      <p><a href={REPO_URL} className="underline underline-offset-2 hover:text-white">Code and data on GitHub</a></p>
      <p>Research project, not investment advice.</p>
      <p>Ghiri S · MBA Business Analytics · ITM Skills University</p>
    </>],
    ["Design", <>
      <p>Layout ideas from two Figma Community files (a trading dashboard kit and a report template). No assets copied.</p>
      <p>Details on the About &amp; limits tab.</p>
    </>],
  ];
  return (
    <>
      <div className="hidden gap-8 xs:grid xs:grid-cols-3">
        {cols.map(([t, body]) => (
          <div key={t}><div className="mb-2 font-semibold text-white">{t}</div><div className="space-y-1 text-slate-300">{body}</div></div>
        ))}
      </div>
      <div className="divide-y divide-navy-700 xs:hidden">
        {cols.map(([t, body]) => (
          <details key={t} className="py-2">
            <summary className="cursor-pointer font-semibold text-white">{t}</summary>
            <div className="mt-2 space-y-1 text-slate-300">{body}</div>
          </details>
        ))}
      </div>
    </>
  );
}

export default function App() {
  const meta = useJson<Meta>("meta.json");
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.pathname]);
  const tab = TABS.find(([to]) => to === loc.pathname)?.[1] ?? "";
  const isStart = loc.pathname === "/";
  return (
    <div className="flex min-h-screen bg-page">
      {/* desktop sidebar: full-height white column, menu stays in view while scrolling */}
      <aside className="hidden w-60 shrink-0 border-r border-line bg-paper lg:block">
        <div className="sticky top-0 px-4 py-5">
          <div className="mb-7 px-2"><Wordmark /></div>
          <Nav />
        </div>
      </aside>
      {/* phone and tablet drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-black/30" aria-label="Close menu" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85%] overflow-y-auto bg-paper px-4 py-5 shadow-xl">
            <div className="mb-6 flex items-center justify-between px-2">
              <Wordmark small />
              <button onClick={() => setOpen(false)} aria-label="Close menu" className="flex h-10 w-10 items-center justify-center rounded text-slate-600"><Icon name="close" /></button>
            </div>
            <Nav onPick={() => setOpen(false)} />
          </div>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <header className="border-b border-line bg-paper">
          <Ribbon />
          <div className="flex items-center gap-3 px-4 py-3 lg:px-8">
            <button className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-line text-navy-900 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
              <Icon name="menu" />
            </button>
            <span className="lg:hidden"><Wordmark small /></span>
            <div className="hidden flex-1 sm:block"><Search /></div>
            <span className="ml-auto whitespace-nowrap text-sm font-semibold text-navy-900">Ghiri S</span>
          </div>
          <div className="px-4 pb-3 sm:hidden"><Search /></div>
          <div className="border-t border-line px-4 pb-6 pt-4 lg:px-8">
            <div className="label flex flex-wrap gap-x-4 gap-y-1 border-b border-line pb-2 text-[11px] text-slate-500">
              <span>Research edition</span>
              {meta.data?.snapshot_utc && <span>Locked data {meta.data.snapshot_utc.slice(0, 10)}</span>}
              {meta.data?.live_as_of && <span>Daily example to {meta.data.live_as_of}</span>}
            </div>
            <div className="mt-3 text-xs leading-snug text-slate-500" title={PROJECT_TITLE}>
              {PROJECT_TITLE} · Ghiri S
            </div>
            <h1 className="mt-2 text-[30px] font-bold leading-[1.08] tracking-[-0.5px] text-navy-900 sm:text-[44px]">
              {isStart ? "How much could a big Indian stock lose tomorrow?" : tab}
            </h1>
            <p className="mt-1 text-[15px] text-slate-600">
              Classic models against machine learning, tested on {meta.data?.n_stocks ?? "…"} big stocks. A student project at ITM Skills University.
            </p>
          </div>
        </header>
        {meta.data && (
          <div className="border-b border-warn-500 bg-warn-100 text-sm text-warn-700">
            <div className="px-4 py-2 lg:px-8">
              {meta.data.approval_note}
            </div>
          </div>
        )}
        {meta.data?.macro_note && (
          <div className="border-b border-line bg-paper text-[13px] text-slate-600">
            <div className="px-4 py-2 lg:px-8">
              {meta.data.macro_note} <Link to="/about" className="font-medium text-navy-900 underline underline-offset-2">About &amp; limits</Link>
            </div>
          </div>
        )}
        <main className="mx-auto max-w-[1200px] px-4 py-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Start />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/glossary" element={<Glossary />} />
            <Route path="/models" element={<Models />} />
            <Route path="/regimes" element={<Regimes />} />
            <Route path="/stock" element={<Stock />} />
            <Route path="/features" element={<Features />} />
            <Route path="/live" element={<Live />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="bg-navy-900 px-4 py-8 text-sm lg:px-8">
          <FooterCols meta={meta.data} />
        </footer>
      </div>
    </div>
  );
}

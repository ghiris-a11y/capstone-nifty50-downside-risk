import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
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
import { useJson, type Meta } from "./lib/data";
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

function Mark() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6 shrink-0" aria-hidden>
      <rect width="24" height="24" rx="6" fill="#0f1b3d" />
      <path d="M5 8l5 6 3-3 6 7" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Nav({ onPick }: { onPick?: () => void }) {
  const item = (to: string, label: string, icon: string) => (
    <NavLink key={to} to={to} end={to === "/"} onClick={onPick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2 text-[15px] ${isActive ? "bg-slate-100 font-semibold text-navy-900" : "text-slate-600 hover:bg-slate-50 hover:text-navy-900"}`}>
      <Icon name={icon} />{label}
    </NavLink>
  );
  return (
    <nav className="flex flex-col gap-1">
      {TABS.filter(([to]) => !SECONDARY.has(to)).map(([to, l, i]) => item(to, l, i))}
      <div className="mt-5 px-3 pb-1 text-xs font-medium uppercase tracking-wide text-slate-400">More</div>
      {TABS.filter(([to]) => SECONDARY.has(to)).map(([to, l, i]) => item(to, l, i))}
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
      <aside className="hidden w-60 shrink-0 border-r border-line bg-white lg:block">
        <div className="sticky top-0 px-4 py-5">
          <div className="mb-6 flex items-center gap-2 px-2"><Mark /><span className="text-[15px] font-bold leading-tight text-navy-900">Nifty 50 Downside Risk</span></div>
          <Nav />
        </div>
      </aside>
      {/* phone and tablet drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-black/30" aria-label="Close menu" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85%] overflow-y-auto bg-white px-4 py-5 shadow-xl">
            <div className="mb-6 flex items-center justify-between px-2">
              <span className="flex items-center gap-2"><Mark /><span className="font-bold text-navy-900">Nifty 50 Downside Risk</span></span>
              <button onClick={() => setOpen(false)} aria-label="Close menu" className="rounded p-1 text-slate-600"><Icon name="close" /></button>
            </div>
            <Nav onPick={() => setOpen(false)} />
          </div>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <header className="border-b border-line bg-white">
          <div className="flex items-center gap-3 px-4 py-3 lg:px-8">
            <button className="rounded-lg border border-line p-2 text-navy-900 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
              <Icon name="menu" />
            </button>
            <span className="flex items-center gap-2 lg:hidden"><Mark /><span className="hidden text-sm font-bold text-navy-900 xs:inline">Nifty 50 Downside Risk</span></span>
            <div className="hidden flex-1 sm:block"><Search /></div>
            <span className="ml-auto whitespace-nowrap text-sm font-semibold text-navy-900">Ghiri S</span>
          </div>
          <div className="px-4 pb-3 sm:hidden"><Search /></div>
          <div className={`px-4 pb-6 pt-5 lg:px-8 ${isStart ? "bg-gradient-to-br from-stone-100 via-white to-white" : ""}`}>
            <div className="text-xs font-medium leading-snug text-slate-500" title={PROJECT_TITLE}>
              {PROJECT_TITLE} · Ghiri S
            </div>
            <h1 className="mt-2 text-[28px] font-bold leading-tight tracking-[-1px] text-navy-900 sm:text-[40px]">
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
              Draft results: our project guide has not yet approved them. The models do not yet use interest rates, price rises or
              factory output.
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

import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Overview from "./pages/Overview";
import Models from "./pages/Models";
import Regimes from "./pages/Regimes";
import Stock from "./pages/Stock";
import Features from "./pages/Features";
import Live from "./pages/Live";
import About from "./pages/About";
import { useJson, type Meta } from "./lib/data";

const TABS = [
  ["/", "Overview"],
  ["/models", "Model comparison"],
  ["/regimes", "Regimes & stress"],
  ["/stock", "Stock drill-down"],
  ["/features", "Feature importance"],
  ["/live", "Live risk"],
  ["/about", "About"],
] as const;

export default function App() {
  const meta = useJson<Meta>("meta.json");
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 pt-4">
          <h1 className="font-serif text-3xl font-bold">Nifty 50 Downside Risk: GARCH vs Machine Learning</h1>
          <p className="text-slate-600">
            One-day 95% and 99% Value-at-Risk and Expected Shortfall for {meta.data?.n_stocks ?? "…"} Nifty 50 stocks.
            MBA Business Analytics capstone, ITM Skills University.
          </p>
          <nav className="mt-3 flex flex-wrap gap-1">
            {TABS.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `rounded-t px-3 py-2 text-sm font-medium ${isActive ? "bg-slate-800 text-white" : "text-slate-700 hover:bg-slate-100"}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      {meta.data && (
        <div className="border-b border-warn-500 bg-warn-100 text-sm text-warn-700">
          <div className="mx-auto max-w-7xl px-4 py-2">
            Working results. {meta.data.approval_note} {meta.data.macro_note}
          </div>
        </div>
      )}
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/models" element={<Models />} />
          <Route path="/regimes" element={<Regimes />} />
          <Route path="/stock" element={<Stock />} />
          <Route path="/features" element={<Features />} />
          <Route path="/live" element={<Live />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Frozen research snapshot {meta.data?.snapshot_utc ?? ""} · results generated {meta.data?.results_generated_utc ?? ""}
        {meta.data?.live_as_of ? ` · live data as of ${meta.data.live_as_of}` : ""} · Data: Yahoo Finance (derived values only)
      </footer>
    </div>
  );
}

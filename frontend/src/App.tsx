import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Overview from "./pages/Overview";
import Start from "./pages/Start";
import Glossary from "./pages/Glossary";
import Models from "./pages/Models";
import Regimes from "./pages/Regimes";
import Stock from "./pages/Stock";
import Features from "./pages/Features";
import Live from "./pages/Live";
import About from "./pages/About";
import { useJson, type Meta } from "./lib/data";

const TABS = [
  ["/", "Start here"],
  ["/overview", "Results at a glance"],
  ["/models", "Model comparison"],
  ["/regimes", "Calm vs stressed days"],
  ["/stock", "One stock up close"],
  ["/features", "What drives the forecasts"],
  ["/live", "Daily example"],
  ["/glossary", "Glossary"],
  ["/about", "About & limits"],
] as const;

export default function App() {
  const meta = useJson<Meta>("meta.json");
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 pt-4">
          <h1 className="font-serif text-2xl font-bold sm:text-3xl">How much could a big Indian stock lose tomorrow?</h1>
          <p className="text-slate-600">
            Classic models against machine learning, tested on {meta.data?.n_stocks ?? "…"} big stocks. A student project at ITM Skills University.
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
            Draft results: our project guide has not yet approved them. The models do not yet use interest rates, price rises or
            factory output.
          </div>
        </div>
      )}
      <main className="mx-auto max-w-7xl px-4 py-6">
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
      <footer className="border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Locked data copy {meta.data?.snapshot_utc ?? ""} · results made {meta.data?.results_generated_utc ?? ""}
        {meta.data?.live_as_of ? ` · daily example up to ${meta.data.live_as_of}` : ""} · Data: Yahoo Finance (only returns and risk numbers are shown, no prices)
      </footer>
    </div>
  );
}

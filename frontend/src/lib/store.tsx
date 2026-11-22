import { createContext, useContext, useState, type ReactNode } from "react";

// Shared UI state: the top-bar search text filters the stock selector, and the chosen stock is kept across tabs.
interface Store { query: string; setQuery: (q: string) => void; ticker: string; setTicker: (t: string) => void }
const Ctx = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState("");
  const [ticker, setTicker] = useState("RELIANCE.NS");
  return <Ctx.Provider value={{ query, setQuery, ticker, setTicker }}>{children}</Ctx.Provider>;
}

export function useStore() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useStore outside StoreProvider");
  return s;
}

// Initials for a stock badge (no company logos): "RELIANCE.NS" -> "RE", "BAJAJ-AUTO.NS" -> "BA".
export const initials = (ticker: string) => ticker.replace(".NS", "").replace(/[^A-Z&]/g, "").slice(0, 2);

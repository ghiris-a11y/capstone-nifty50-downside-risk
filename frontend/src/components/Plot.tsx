import { lazy, Suspense, useCallback, useRef, useState } from "react";
import type { PlotParams } from "react-plotly.js";
import { Loading } from "./ui";

// Plotly is large: it is downloaded only when the first chart is shown.
const LazyPlot = lazy(async () => {
  const [{ default: Plotly }, { default: factory }] = await Promise.all([
    import("plotly.js-dist-min"),
    import("react-plotly.js/factory"),
  ]);
  return { default: factory(Plotly) };
});

// One hand-drawn-style note per chart: a thin curved arrow and an italic label pointing at a real data point.
// x and y are data values (dates allowed); y2 = use the right-hand axis. Without y the arrow points at the top of the plot.
export interface Annot { x: string | number; y?: number; y2?: boolean; text: string; short?: string }

interface Axis { _offset: number; _length: number; l2p: (v: number) => number; d2l: (v: unknown) => number }
interface Pos { px: number; py: number; lx: number; ly: number; anchor: "start" | "end"; w: number; h: number; text: string }

export default function Plot({ annotate, ...props }: PlotParams & { annotate?: Annot }) {
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<Pos | null>(null);
  const place = useCallback((_: unknown, gd: HTMLElement) => {
    if (!annotate || !box.current) return;
    const fl = (gd as unknown as { _fullLayout: Record<string, Axis> })._fullLayout;
    const xa = fl.xaxis, ya = fl[annotate.y2 ? "yaxis2" : "yaxis"];
    if (!xa || !ya) return;
    const px = xa._offset + xa.l2p(xa.d2l(annotate.x));
    const py = annotate.y == null ? ya._offset + 8 : ya._offset + ya.l2p(ya.d2l(annotate.y));
    if (!Number.isFinite(px) || !Number.isFinite(py)) return;
    const w = box.current.clientWidth, h = box.current.clientHeight;
    // label goes up and to whichever side has more room; the curve bends from the label to the point
    const text = w < 480 && annotate.short ? annotate.short : annotate.text;
    const tw = text.length * 6.6;  // italic 13 px, approximate width
    let anchor: "start" | "end" = px > w / 2 ? "end" : "start";
    let lx = anchor === "end" ? px - 60 : px + 60;
    if (anchor === "end" && lx - tw < 4) lx = Math.min(tw + 4, w - 4);
    if (anchor === "start" && lx + tw > w - 4) { anchor = "end"; lx = Math.min(Math.max(px - 60, tw + 4), w - 4); }
    const ly = Math.max(py - 56, 16);
    setPos({ px, py, lx, ly, anchor, w, h, text });
  }, [annotate]);
  return (
    <Suspense fallback={<Loading what="chart" />}>
      <div ref={box} className="relative">
        <LazyPlot
          useResizeHandler
          {...props}
          onInitialized={place}
          onUpdate={place}
          style={{ width: "100%", ...(props.style || {}) }}
          config={{ displaylogo: false, responsive: true, ...(props.config || {}) }}
        />
        {annotate && pos && (
          <svg className="pointer-events-none absolute left-0 top-0" width={pos.w} height={pos.h} aria-hidden>
            <defs>
              <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M0 1L9 5L0 9" fill="none" stroke="#334155" strokeWidth="1.4" />
              </marker>
            </defs>
            <path d={`M ${pos.lx + (pos.anchor === "end" ? 6 : -6)} ${pos.ly - 4} Q ${pos.px} ${pos.ly - 4} ${pos.px} ${pos.py - 6}`}
              fill="none" stroke="#334155" strokeWidth="1.2" markerEnd="url(#arrowhead)" />
            <text x={pos.lx} y={pos.ly} textAnchor={pos.anchor} fontSize="13" fontStyle="italic" fill="#1f2937"
              style={{ paintOrder: "stroke", stroke: "white", strokeWidth: 4 }}>
              {pos.text}
            </text>
          </svg>
        )}
        {annotate && <span className="sr-only">{annotate.text}</span>}
      </div>
    </Suspense>
  );
}

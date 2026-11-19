import { lazy, Suspense } from "react";
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

export default function Plot(props: PlotParams) {
  return (
    <Suspense fallback={<Loading what="chart" />}>
      <LazyPlot
        useResizeHandler
        {...props}
        style={{ width: "100%", ...(props.style || {}) }}
        config={{ displaylogo: false, responsive: true, ...(props.config || {}) }}
      />
    </Suspense>
  );
}

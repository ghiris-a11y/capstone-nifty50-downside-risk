"""How much does XGBoost's ES (mean of 5 tail quantiles at 0.1a..0.9a) understate true ES?

Even with perfectly estimated quantiles, a 5-point midpoint average of the quantile function
misses part of the deepest tail. This compares it with exact ES = (1/a) * integral_0^a q(u) du
for Normal and Student-t distributions and writes outputs/tables/xgb_es_approx_bias.csv.
"""
import os

import numpy as np
import pandas as pd
from scipy import integrate, stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = (0.1, 0.3, 0.5, 0.7, 0.9)  # same grid as xgb_quantile in the pipeline


def main():
    rows = []
    for name, d in [("normal", stats.norm), ("t(6)", stats.t(6)), ("t(5)", stats.t(5)),
                    ("t(4)", stats.t(4)), ("t(3)", stats.t(3))]:
        for a in (0.05, 0.01):
            approx = np.mean([d.ppf(a * u) for u in GRID])
            exact = integrate.quad(d.ppf, 0, a, limit=200)[0] / a
            rows.append(dict(distribution=name, alpha=a, es_5pt_over_true=approx / exact,
                             understatement_pct=100 * (1 - approx / exact)))
    out = pd.DataFrame(rows)
    path = os.path.join(ROOT, "outputs", "tables", "xgb_es_approx_bias.csv")
    out.to_csv(path, index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

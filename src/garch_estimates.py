"""GARCH parameter estimates at the start of the test window (for the report's statistical-analysis section).

The pipeline does not store fitted parameters. This script repeats exactly the first fit that
nifty50_var_pipeline.garch_forecasts makes for each stock: same frozen data, same returns (log close-to-close,
in %), same specification (constant mean, p=1, q=1, o=1 for EGARCH/GJR), estimated on all data before
TEST_START (2015-01-01 to 2023-12-31). Later refits (every 20 days) are not stored.

  python src/garch_estimates.py   ->  outputs/tables/garch_params_teststart.csv
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import nifty50_var_pipeline as p  # noqa: E402

OUT = os.path.join(ROOT, "outputs", "tables", "garch_params_teststart.csv")


def main():
    from arch import arch_model
    tickers = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))["ticker"].tolist()
    p.FROZEN_DIR = os.path.join(ROOT, "data", "frozen")
    rows = []
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)  # load_prices appends dropped-row notes to ./data/logs; keep the project log untouched
        try:
            for t in tickers:
                px = p.load_prices(t, "2015-01-01", "2026-11-18")
                r = np.log(px["Close"]).diff().dropna() * 100
                r = r[r.index < pd.Timestamp(p.TEST_START)]
                for kind in ("GARCH", "EGARCH", "GJR"):
                    for dist in ("normal", "t"):
                        spec = dict(mean="Constant", dist=dist, p=1, q=1)
                        spec.update({"GARCH": dict(vol="GARCH"), "EGARCH": dict(vol="EGARCH", o=1), "GJR": dict(vol="GARCH", o=1)}[kind])
                        res = arch_model(r, **spec).fit(disp="off", show_warning=False)
                        pr = res.params
                        a, b, g = pr.get("alpha[1]", np.nan), pr.get("beta[1]", np.nan), pr.get("gamma[1]", 0.0)
                        pers = b if kind == "EGARCH" else a + b + (g / 2 if kind == "GJR" else 0.0)
                        rows.append(dict(ticker=t, model=f"{kind}-{dist}", n_obs=len(r), mu=pr["mu"], omega=pr["omega"],
                                         alpha=a, gamma=pr.get("gamma[1]", np.nan), beta=b, nu=pr.get("nu", np.nan),
                                         persistence=pers, loglik=res.loglikelihood, aic=res.aic, bic=res.bic,
                                         gamma_pvalue=res.pvalues.get("gamma[1]", np.nan)))
                print("fitted", t, flush=True)
        finally:
            os.chdir(cwd)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    main()

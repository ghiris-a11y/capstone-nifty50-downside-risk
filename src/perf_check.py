"""Responsiveness check of the dashboard: per tab, bytes downloaded, time until the tab is ready, main-thread
blocking (long tasks over 50 ms, which is when clicks feel ignored), and whether the menu links can actually be
clicked (nothing covering them, and the route changes within one second of a click).

  python src/perf_check.py [--url https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/] [--width 1440]
"""
import argparse
import time

from playwright.sync_api import sync_playwright

TABS = [("start", "#/"), ("overview", "#/overview"), ("models", "#/models"), ("regimes", "#/regimes"), ("stock", "#/stock"),
        ("features", "#/features"), ("live", "#/live"), ("glossary", "#/glossary"), ("about", "#/about")]
INIT = """
window.__long = []; window.__lt = 0;
new PerformanceObserver(l => l.getEntries().forEach(e => { window.__long.push(e.duration); })).observe({type: 'longtask', buffered: true});
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/")
    ap.add_argument("--width", type=int, default=1440)
    a = ap.parse_args()
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        ctx = br.new_context(viewport={"width": a.width, "height": 900})
        ctx.add_init_script(INIT)
        page = ctx.new_page()
        got = {"bytes": 0}
        page.on("response", lambda r: got.__setitem__("bytes", got["bytes"] + int(r.headers.get("content-length", 0) or 0)))
        for name, frag in TABS:
            got["bytes"] = 0
            t0 = time.time()
            page.goto(a.url + frag, wait_until="load")
            page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=120000)
            ready = time.time() - t0
            page.wait_for_timeout(1500)
            lt = page.evaluate("() => window.__long.slice()")
            tbt = sum(max(0, d - 50) for d in lt)
            # can the menu links be clicked? element at each link's centre must be the link (or inside it)
            covered = page.evaluate("""() => [...document.querySelectorAll('nav a')].filter(a => a.offsetParent).map(a => {
                const r = a.getBoundingClientRect(); const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return el && (a === el || a.contains(el)) ? null : (a.innerText + ' covered by ' + (el ? el.tagName + '.' + el.className : 'nothing'));
            }).filter(Boolean)""")
            print(f"{name:9s} ready {ready:5.1f}s  downloaded {got['bytes'] / 1e6:5.1f} MB  long tasks {len(lt):3d}  blocking {tbt / 1000:5.2f}s  covered {covered[:2]}", flush=True)
        # click test: from the stock tab (the heaviest), click to Glossary and time the route change
        page.goto(a.url + "#/stock", wait_until="load")
        page.wait_for_timeout(500)
        link = page.locator("nav a", has_text="Glossary").first
        if link.is_visible():
            t0 = time.time(); link.click(timeout=10000)
            page.wait_for_function("location.hash.includes('glossary')", timeout=15000)
            print(f"click Glossary while the stock tab loads: route changed after {time.time() - t0:.2f}s")
        br.close()


if __name__ == "__main__":
    main()

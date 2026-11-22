/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    // Breakpoints in size order (custom ones under "extend" would be emitted after lg/xl and override them).
    // mp = large phone (400 px+); xs = wider than the phone layout; ph = phone layout (480 px and below; the report
    // screenshots are taken at 480 px).
    screens: { mp: "400px", xs: "481px", sm: "640px", md: "768px", lg: "1024px", xl: "1280px", "2xl": "1536px", ph: { max: "480px" } },
    extend: {
      colors: {
        // model palette (unchanged): GARCH = red, ML = blue, warnings = amber
        garch: { 50: "#fff5f0", 100: "#fee0d2", 500: "#cb181d", 700: "#a50f15", 900: "#67000d" },
        ml: { 50: "#f7fbff", 100: "#deebf7", 500: "#3182bd", 700: "#08519c" },
        warn: { 100: "#fdf0d0", 500: "#d18f00", 700: "#8a5d00" },
        // UI chrome: ink on warm paper ("risk ledger"); never blue (= ML) or orange (= warning).
        // The token is still called navy so existing classes keep working; its values are now ink.
        navy: { 700: "#4a453c", 800: "#2b2822", 900: "#1d1b16" },
        page: "#F3EFE6",
        paper: "#FFFDF8",
        line: "#DCD4C3",
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        serif: ["Fraunces", "Georgia", "serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: { lg: "4px", xl: "6px" },
      boxShadow: { card: "none" },
    },
  },
  plugins: [],
};

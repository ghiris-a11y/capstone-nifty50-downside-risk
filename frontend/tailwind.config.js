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
        // UI chrome: navy and charcoal only (blue means ML, orange/amber means warning)
        navy: { 700: "#22304f", 800: "#18244a", 900: "#0f1b3d" },
        page: "#F4F5F7",
        line: "#E5E7EB",
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"], serif: ["Inter", "system-ui", "sans-serif"] },
      boxShadow: { card: "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.04)" },
    },
  },
  plugins: [],
};

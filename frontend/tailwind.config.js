/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        garch: { 50: "#fff5f0", 100: "#fee0d2", 500: "#cb181d", 700: "#a50f15", 900: "#67000d" },
        ml: { 50: "#f7fbff", 100: "#deebf7", 500: "#3182bd", 700: "#08519c" },
        warn: { 100: "#fdf0d0", 500: "#d18f00", 700: "#8a5d00" },
      },
      fontFamily: { serif: ["'Times New Roman'", "Times", "serif"] },
    },
  },
  plugins: [],
};

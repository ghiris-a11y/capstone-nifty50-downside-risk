import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages serves the site from /<repository-name>/. Data files are fetched with relative
// './data/...' paths, so the same build works locally (npm run preview) and on Pages.
export default defineConfig({
  base: "/capstone-nifty50-downside-risk/",
  plugins: [react()],
  build: { outDir: "dist", chunkSizeWarningLimit: 5000 },
});

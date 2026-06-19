import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wa: { green: "#25D366", dark: "#1ea952" },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;

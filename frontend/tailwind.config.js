/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#12172C",
          deep: "#0B0E1D",
          panel: "#1C2348",
          line: "#2A3260",
        },
        parchment: {
          DEFAULT: "#F3EEE0",
          dim: "#EAE3CE",
          ink: "#1D1930",
        },
        brass: {
          DEFAULT: "#C9A15C",
          light: "#E3C588",
          dark: "#9C7A3E",
        },
        moss: {
          DEFAULT: "#3F6355",
          light: "#5C8573",
          dark: "#2C4A3F",
        },
      },
      fontFamily: {
        display: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,14,29,0.06), 0 8px 24px -8px rgba(11,14,29,0.18)",
        "card-dark": "0 1px 2px rgba(0,0,0,0.3), 0 12px 32px -12px rgba(0,0,0,0.55)",
      },
      backgroundImage: {
        "ink-radial":
          "radial-gradient(120% 120% at 15% 0%, #1B2348 0%, #12172C 45%, #0B0E1D 100%)",
      },
    },
  },
  plugins: [],
};

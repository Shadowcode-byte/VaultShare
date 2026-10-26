/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#1E2761", light: "#2E3A80", dark: "#161C4A" },
        ice: { DEFAULT: "#CADCFC", light: "#EEF3FC" },
      },
      fontFamily: {
        serif: ["Cambria", "Georgia", "serif"],
        sans: ["Calibri", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

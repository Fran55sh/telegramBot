/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#d3bbff",
        "primary-container": "#6d28d9",
        "on-primary-container": "#dac5ff",
        secondary: "#adc6ff",
        "secondary-container": "#0566d9",
        tertiary: "#4edea3",
        "tertiary-container": "#006544",
        surface: "#0b1326",
        "surface-container": "#171f33",
        "surface-container-low": "#131b2e",
        "surface-container-high": "#222a3d",
        "surface-variant": "#2d3449",
        background: "#0b1326",
        "on-background": "#dae2fd",
        "on-surface": "#dae2fd",
        "on-surface-variant": "#ccc3d7",
        outline: "#958da1",
        "outline-variant": "#4a4455",
        error: "#ffb4ab",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Geist", "ui-monospace", "monospace"],
      },
      spacing: {
        gutter: "16px",
      },
    },
  },
  plugins: [],
};

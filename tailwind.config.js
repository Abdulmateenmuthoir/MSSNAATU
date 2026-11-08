/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./apps/**/*.py",
  ],
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        paper: "rgb(var(--paper) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        surface2: "rgb(var(--surface-2) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        brand: "rgb(var(--brand) / <alpha-value>)",
        brandsoft: "rgb(var(--brand-soft) / <alpha-value>)",
        onbrand: "rgb(var(--on-brand) / <alpha-value>)",
        gold: "rgb(var(--gold) / <alpha-value>)",
        goldsoft: "rgb(var(--gold-soft) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)",
        success: "rgb(var(--success) / <alpha-value>)",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Manrope"', "ui-sans-serif", "system-ui", "sans-serif"],
        arabic: ['"Amiri"', "serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgb(16 32 25 / 0.04), 0 12px 32px -12px rgb(16 32 25 / 0.12)",
        lift: "0 2px 4px rgb(16 32 25 / 0.05), 0 22px 48px -18px rgb(16 32 25 / 0.22)",
        insetline: "inset 0 0 0 1px rgb(var(--line))",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      maxWidth: {
        prose: "70ch",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fade: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        rise: "rise .65s cubic-bezier(0.22, 1, 0.36, 1) both",
        fade: "fade .4s ease both",
      },
    },
  },
  plugins: [],
};

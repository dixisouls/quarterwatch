/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        sans: ["'DM Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      colors: {
        stone: {
          25: "#FDFCFB",
          50: "#FAFAF9",
          100: "#F5F4F2",
          200: "#E8E5E1",
          300: "#D5D0C9",
          400: "#B8B0A6",
          500: "#9A9088",
          600: "#7A706A",
          700: "#5C5450",
          800: "#403C39",
          900: "#28241F",
          950: "#18150F",
        },
        amber: {
          25: "#FFFDF5",
          50: "#FFFBEB",
          100: "#FEF3C7",
          200: "#FDE68A",
          300: "#FCD34D",
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
          700: "#B45309",
          800: "#92400E",
          900: "#78350F",
        },
        signal: {
          green: "#16A34A",
          red: "#DC2626",
          yellow: "#CA8A04",
          blue: "#2563EB",
        },
      },
      boxShadow: {
        card: "0 1px 3px rgba(40,36,31,0.06), 0 1px 2px rgba(40,36,31,0.04)",
        "card-hover": "0 4px 12px rgba(40,36,31,0.08), 0 2px 4px rgba(40,36,31,0.05)",
        input: "0 0 0 3px rgba(245,158,11,0.15)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease forwards",
        "slide-up": "slideUp 0.4s ease forwards",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
        shimmer: "shimmer 1.8s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-600px 0" },
          "100%": { backgroundPosition: "600px 0" },
        },
      },
    },
  },
  plugins: [],
};

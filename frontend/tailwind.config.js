/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Manrope", "sans-serif"],
      },
      colors: {
        primary: "#0E6F75",
      },
    },
  },
  plugins: [require("daisyui")],
};

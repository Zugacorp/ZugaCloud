/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a192f',
        secondary: '#112240',
        border: '#233554',
        hover: '#2a4065',
      },
    },
  },
  plugins: [],
} 
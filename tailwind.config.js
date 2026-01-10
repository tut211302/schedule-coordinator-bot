/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        'line-green': '#00B900',
        'line-green-light': '#e8f5e9',
      },
    },
  },
  plugins: [],
}

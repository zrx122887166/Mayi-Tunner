/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  prefix: 'tw-',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#165DFF',
          hover: '#0E42D2',
        },
      },
    },
  },
  plugins: [],
  corePlugins: {
    preflight: false,
  },
}


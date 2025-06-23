/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}", // Include all files in the src folder
  ],
  theme: {
    extend: {
      // Add customizations here if needed
      colors: {
        primary: "#646cff",
        secondary: "#535bf2",
      },
    },
  },
  plugins: [],
};

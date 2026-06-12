import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        panel: "#f7f7f3",
        line: "#d8d8ce",
        pine: "#12372a",
        coral: "#d95f43",
        sky: "#3b82b6",
      },
      boxShadow: {
        soft: "0 18px 40px rgba(23, 23, 23, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

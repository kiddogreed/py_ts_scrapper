import axios from "axios";

// Server-side client — never exposed to the browser
const scraperClient = axios.create({
  baseURL: process.env.SCRAPER_API_URL ?? "http://localhost:8000",
  timeout: 35_000,
  headers: { "Content-Type": "application/json" },
});

export default scraperClient;

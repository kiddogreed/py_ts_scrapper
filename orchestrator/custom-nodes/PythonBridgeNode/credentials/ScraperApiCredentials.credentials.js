"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ScraperApiCredentials = void 0;
// Credential type for the Python FastAPI scraper service.
// Set in n8n UI under Credentials → New → "Scraper API".
class ScraperApiCredentials {
    constructor() {
        this.name = 'scraperApi';
        this.displayName = 'Scraper API';
        this.documentationUrl = 'https://github.com/your-org/py_ts_scrapper';
        this.properties = [
            {
                displayName: 'Base URL',
                name: 'baseUrl',
                type: 'string',
                default: 'http://scraper-api:8000',
                placeholder: 'http://scraper-api:8000',
                description: 'Base URL of the FastAPI scraper service (no trailing slash)',
            },
            {
                displayName: 'API Secret',
                name: 'apiSecret',
                type: 'string',
                typeOptions: { password: true },
                default: '',
                description: 'Value of SCRAPER_API_SECRET from .env (leave blank if not configured)',
            },
        ];
    }
}
exports.ScraperApiCredentials = ScraperApiCredentials;
//# sourceMappingURL=ScraperApiCredentials.credentials.js.map
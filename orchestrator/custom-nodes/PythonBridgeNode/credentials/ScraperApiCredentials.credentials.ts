import {
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

// Credential type for the Python FastAPI scraper service.
// Set in n8n UI under Credentials → New → "Scraper API".
export class ScraperApiCredentials implements ICredentialType {
	name = 'scraperApi';
	displayName = 'Scraper API';
	documentationUrl = 'https://github.com/your-org/py_ts_scrapper';
	properties: INodeProperties[] = [
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

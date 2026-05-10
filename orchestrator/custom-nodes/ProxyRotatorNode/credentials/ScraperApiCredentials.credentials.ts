import {
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

// Same credential definition as PythonBridgeNode — kept in sync manually.
// Both nodes authenticate against the same FastAPI scraper service.
// Cannot import cross-package because TypeScript rootDir would be violated.
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

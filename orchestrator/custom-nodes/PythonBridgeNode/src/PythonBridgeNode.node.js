"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PythonBridgeNode = void 0;
const n8n_workflow_1 = require("n8n-workflow");
/**
 * PythonBridgeNode
 *
 * A custom n8n node that calls the Python FastAPI scraper service.
 * Supports two operations:
 *   - scrape: POST /scrape/ → browser or HTTP scrape, returns HTML + intercepted XHR
 *   - parse:  POST /parse/  → extract structured data from raw HTML
 */
class PythonBridgeNode {
    constructor() {
        this.description = {
            displayName: 'Python Bridge',
            name: 'pythonBridge',
            icon: 'file:python-bridge.svg',
            group: ['transform'],
            version: 1,
            subtitle: '={{$parameter["operation"]}} → FastAPI',
            description: 'Call the Python FastAPI scraper service (scrape or parse)',
            defaults: { name: 'Python Bridge' },
            inputs: ['main'],
            outputs: ['main'],
            credentials: [
                {
                    name: 'scraperApi',
                    required: true,
                },
            ],
            properties: [
                // ── Operation selector ─────────────────────────────────────────
                {
                    displayName: 'Operation',
                    name: 'operation',
                    type: 'options',
                    noDataExpression: true,
                    options: [
                        {
                            name: 'Scrape URL',
                            value: 'scrape',
                            description: 'Navigate to a URL and return its HTML (uses Playwright or curl_cffi)',
                            action: 'Scrape a URL',
                        },
                        {
                            name: 'Parse HTML',
                            value: 'parse',
                            description: 'Extract structured data from raw HTML using rule-based + JSON-LD extraction',
                            action: 'Parse raw HTML',
                        },
                    ],
                    default: 'scrape',
                },
                // ── SCRAPE fields ──────────────────────────────────────────────
                {
                    displayName: 'URL',
                    name: 'url',
                    type: 'string',
                    required: true,
                    default: '',
                    placeholder: 'https://example.com/product',
                    description: 'The URL to scrape',
                    displayOptions: { show: { operation: ['scrape'] } },
                },
                {
                    displayName: 'Use Browser (JavaScript)',
                    name: 'javascript',
                    type: 'boolean',
                    default: true,
                    description: 'Whether to use a headless browser (Playwright). Disable for faster HTTP-only scraping.',
                    displayOptions: { show: { operation: ['scrape'] } },
                },
                {
                    displayName: 'Wait For Selector',
                    name: 'waitFor',
                    type: 'string',
                    default: '',
                    placeholder: '.product-price',
                    description: 'CSS selector to wait for before capturing HTML (browser mode only)',
                    displayOptions: { show: { operation: ['scrape'] } },
                },
                {
                    displayName: 'Intercept Pattern',
                    name: 'interceptPattern',
                    type: 'string',
                    default: '',
                    placeholder: '/api/product',
                    description: 'Capture XHR/fetch responses whose URL contains this string',
                    displayOptions: { show: { operation: ['scrape'] } },
                },
                {
                    displayName: 'Timeout (ms)',
                    name: 'timeoutMs',
                    type: 'number',
                    default: 30000,
                    description: 'Request timeout in milliseconds',
                    displayOptions: { show: { operation: ['scrape'] } },
                },
                // ── PARSE fields ───────────────────────────────────────────────
                {
                    displayName: 'HTML',
                    name: 'html',
                    type: 'string',
                    required: true,
                    default: '',
                    description: 'Raw HTML to parse (typically the output of a Scrape operation)',
                    typeOptions: { rows: 4 },
                    displayOptions: { show: { operation: ['parse'] } },
                },
                {
                    displayName: 'Source URL',
                    name: 'sourceUrl',
                    type: 'string',
                    default: '',
                    placeholder: 'https://example.com/product',
                    description: 'The original URL of the HTML (used to resolve relative links)',
                    displayOptions: { show: { operation: ['parse'] } },
                },
                {
                    displayName: 'Extract Links',
                    name: 'extractLinks',
                    type: 'boolean',
                    default: false,
                    description: 'Whether to include all hyperlinks from the page in the result',
                    displayOptions: { show: { operation: ['parse'] } },
                },
                {
                    displayName: 'Extract Meta Tags',
                    name: 'extractMeta',
                    type: 'boolean',
                    default: true,
                    description: 'Whether to extract Open Graph and other meta tags',
                    displayOptions: { show: { operation: ['parse'] } },
                },
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        const credentials = await this.getCredentials('scraperApi');
        const baseUrl = credentials.baseUrl.replace(/\/$/, '');
        const apiSecret = credentials.apiSecret;
        const headers = {
            'Content-Type': 'application/json',
        };
        if (apiSecret) {
            headers['X-API-Secret'] = apiSecret;
        }
        for (let i = 0; i < items.length; i++) {
            const operation = this.getNodeParameter('operation', i);
            try {
                let responseData;
                if (operation === 'scrape') {
                    const url = this.getNodeParameter('url', i);
                    const javascript = this.getNodeParameter('javascript', i);
                    const waitFor = this.getNodeParameter('waitFor', i);
                    const interceptPattern = this.getNodeParameter('interceptPattern', i);
                    const timeoutMs = this.getNodeParameter('timeoutMs', i);
                    const body = { url, javascript, timeout_ms: timeoutMs };
                    if (waitFor)
                        body.wait_for = waitFor;
                    if (interceptPattern)
                        body.intercept_pattern = interceptPattern;
                    const response = await this.helpers.httpRequest({
                        method: 'POST',
                        url: `${baseUrl}/scrape/`,
                        body,
                        headers,
                        json: true,
                    });
                    responseData = response;
                }
                else if (operation === 'parse') {
                    const html = this.getNodeParameter('html', i);
                    const sourceUrl = this.getNodeParameter('sourceUrl', i);
                    const extractLinks = this.getNodeParameter('extractLinks', i);
                    const extractMeta = this.getNodeParameter('extractMeta', i);
                    const body = {
                        html,
                        extract_links: extractLinks,
                        extract_meta: extractMeta,
                    };
                    if (sourceUrl)
                        body.source_url = sourceUrl;
                    const response = await this.helpers.httpRequest({
                        method: 'POST',
                        url: `${baseUrl}/parse/`,
                        body,
                        headers,
                        json: true,
                    });
                    responseData = response;
                }
                else {
                    throw new n8n_workflow_1.NodeOperationError(this.getNode(), `Unknown operation: ${operation}`, { itemIndex: i });
                }
                returnData.push({ json: responseData, pairedItem: { item: i } });
            }
            catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: { error: error.message },
                        pairedItem: { item: i },
                    });
                    continue;
                }
                throw error;
            }
        }
        return [returnData];
    }
}
exports.PythonBridgeNode = PythonBridgeNode;
//# sourceMappingURL=PythonBridgeNode.node.js.map
import {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
} from 'n8n-workflow';

/**
 * ProxyRotatorNode
 *
 * A custom n8n node that interacts with the FastAPI proxy management endpoints.
 * Supports three operations:
 *   - rotate:   GET  /proxy/rotate  → returns the next healthy proxy
 *   - status:   GET  /proxy/status  → returns pool health stats
 *   - validate: POST /proxy/validate → test a specific proxy
 */
export class ProxyRotatorNode implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Proxy Rotator',
		name: 'proxyRotator',
		icon: 'file:proxy-rotator.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["operation"]}}',
		description: 'Rotate, validate, and inspect proxies from the FastAPI proxy pool',
		defaults: { name: 'Proxy Rotator' },
		inputs: ['main'],
		outputs: ['main'],
		credentials: [
			{
				name: 'scraperApi',
				required: true,
			},
		],
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				options: [
					{
						name: 'Rotate (Get Next Proxy)',
						value: 'rotate',
						description: 'Return the next healthy proxy from the pool',
						action: 'Get next healthy proxy',
					},
					{
						name: 'Pool Status',
						value: 'status',
						description: 'Return health statistics for the entire proxy pool',
						action: 'Get proxy pool status',
					},
					{
						name: 'Validate Proxy',
						value: 'validate',
						description: 'Test a specific proxy against a neutral endpoint',
						action: 'Validate a specific proxy',
					},
					{
						name: 'Retire Proxy',
						value: 'retire',
						description: 'Mark a proxy as dead (too many failures)',
						action: 'Retire a failed proxy',
					},
				],
				default: 'rotate',
			},

			// ── VALIDATE / RETIRE fields ───────────────────────────────────
			{
				displayName: 'Proxy Host',
				name: 'proxyHost',
				type: 'string',
				required: true,
				default: '',
				placeholder: '1.2.3.4',
				description: 'IP address or hostname of the proxy to validate or retire',
				displayOptions: { show: { operation: ['validate', 'retire'] } },
			},
			{
				displayName: 'Proxy Port',
				name: 'proxyPort',
				type: 'number',
				required: true,
				default: 8080,
				description: 'Port of the proxy to validate or retire',
				displayOptions: { show: { operation: ['validate', 'retire'] } },
			},

			// ── Options ────────────────────────────────────────────────────
			{
				displayName: 'Include Proxy URL in Output',
				name: 'includeUrl',
				type: 'boolean',
				default: true,
				description: 'Whether to include the full proxy URL (with credentials) in the output item',
				displayOptions: { show: { operation: ['rotate'] } },
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		const credentials = await this.getCredentials('scraperApi');
		const baseUrl = (credentials.baseUrl as string).replace(/\/$/, '');
		const apiSecret = credentials.apiSecret as string | undefined;

		const headers: Record<string, string> = {};
		if (apiSecret) {
			headers['X-API-Secret'] = apiSecret;
		}

		for (let i = 0; i < items.length; i++) {
			const operation = this.getNodeParameter('operation', i) as string;

			try {
				let responseData: IDataObject;

				if (operation === 'rotate') {
					const includeUrl = this.getNodeParameter('includeUrl', i) as boolean;
					const response = await this.helpers.httpRequest({
						method: 'GET',
						url: `${baseUrl}/proxy/rotate`,
						headers,
						json: true,
					}) as IDataObject;

					// Optionally strip the proxy URL from the output (contains credentials)
					if (!includeUrl) {
						delete response.url;
					}
					responseData = response;

				} else if (operation === 'status') {
					responseData = await this.helpers.httpRequest({
						method: 'GET',
						url: `${baseUrl}/proxy/status`,
						headers,
						json: true,
					}) as IDataObject;

				} else if (operation === 'validate') {
					const host = this.getNodeParameter('proxyHost', i) as string;
					const port = this.getNodeParameter('proxyPort', i) as number;

					responseData = await this.helpers.httpRequest({
						method: 'POST',
						url: `${baseUrl}/proxy/validate`,
						body: { host, port },
						headers: { ...headers, 'Content-Type': 'application/json' },
						json: true,
					}) as IDataObject;

				} else if (operation === 'retire') {
					const host = this.getNodeParameter('proxyHost', i) as string;
					const port = this.getNodeParameter('proxyPort', i) as number;

					responseData = await this.helpers.httpRequest({
						method: 'POST',
						url: `${baseUrl}/proxy/retire`,
						body: { host, port },
						headers: { ...headers, 'Content-Type': 'application/json' },
						json: true,
					}) as IDataObject;

				} else {
					throw new NodeOperationError(this.getNode(), `Unknown operation: ${operation}`, { itemIndex: i });
				}

				returnData.push({ json: responseData, pairedItem: { item: i } });

			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: { error: (error as Error).message },
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

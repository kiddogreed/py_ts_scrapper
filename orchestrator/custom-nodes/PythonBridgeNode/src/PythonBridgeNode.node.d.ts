import { IExecuteFunctions, INodeExecutionData, INodeType, INodeTypeDescription } from 'n8n-workflow';
/**
 * PythonBridgeNode
 *
 * A custom n8n node that calls the Python FastAPI scraper service.
 * Supports two operations:
 *   - scrape: POST /scrape/ → browser or HTTP scrape, returns HTML + intercepted XHR
 *   - parse:  POST /parse/  → extract structured data from raw HTML
 */
export declare class PythonBridgeNode implements INodeType {
    description: INodeTypeDescription;
    execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]>;
}
//# sourceMappingURL=PythonBridgeNode.node.d.ts.map
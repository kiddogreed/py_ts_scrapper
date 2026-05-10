import { IExecuteFunctions, INodeExecutionData, INodeType, INodeTypeDescription } from 'n8n-workflow';
/**
 * ProxyRotatorNode
 *
 * A custom n8n node that interacts with the FastAPI proxy management endpoints.
 * Supports three operations:
 *   - rotate:   GET  /proxy/rotate  → returns the next healthy proxy
 *   - status:   GET  /proxy/status  → returns pool health stats
 *   - validate: POST /proxy/validate → test a specific proxy
 */
export declare class ProxyRotatorNode implements INodeType {
    description: INodeTypeDescription;
    execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]>;
}
//# sourceMappingURL=ProxyRotatorNode.node.d.ts.map
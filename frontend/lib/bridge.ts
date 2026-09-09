import { demoAgentRun, demoApprove, demoCatalog, demoExecute } from './demo';
import type {
  AuditResponse,
  Catalog,
  Decision,
  DemoRole,
  ExecuteResponse,
  RuntimeMode,
} from './contracts';

const base = () => (process.env.MCPBRIDGE_API_URL || '').trim().replace(/\/+$/, '');
export const runtimeMode = (): RuntimeMode =>
  base() ? 'connected-python-mcp' : 'deterministic-public-demo';

async function readJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  let body: unknown = {};
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    throw new Error('backend returned malformed JSON');
  }
  if (!res.ok) {
    const detail = body && typeof body === 'object' && 'detail' in body
      ? String((body as {detail?: unknown}).detail || '')
      : '';
    throw new Error(detail || `backend request failed (${res.status})`);
  }
  return body as T;
}

export async function getCatalog(): Promise<Catalog> {
  if (!base()) return demoCatalog;
  return readJson<Catalog>(await fetch(`${base()}/v1/catalog`, {cache:'no-store'}));
}

export async function executeTool(
  role: DemoRole,
  server: string,
  tool: string,
  args: Record<string, unknown>,
): Promise<ExecuteResponse> {
  if (!base()) return demoExecute(role, server, tool, args);
  return readJson<ExecuteResponse>(await fetch(`${base()}/v1/execute`, {
    method:'POST',
    headers:{'content-type':'application/json','x-demo-role':role,'x-demo-actor':'web-demo'},
    body:JSON.stringify({server,tool,arguments:args}),
    cache:'no-store',
  }));
}

export async function runAgent(role: DemoRole, request: string): Promise<ExecuteResponse> {
  if (!base()) return demoAgentRun(role, request);
  return readJson<ExecuteResponse>(await fetch(`${base()}/v1/agent/run`, {
    method:'POST',
    headers:{'content-type':'application/json','x-demo-role':role,'x-demo-actor':'web-agent'},
    body:JSON.stringify({request}),
    cache:'no-store',
  }));
}

export async function approveTool(
  role: DemoRole,
  token: string,
  decision: Decision,
  edited_arguments?: Record<string, unknown>,
): Promise<ExecuteResponse> {
  if (!base()) return demoApprove(role, token, decision, edited_arguments);
  return readJson<ExecuteResponse>(await fetch(`${base()}/v1/approve`, {
    method:'POST',
    headers:{'content-type':'application/json','x-demo-role':role,'x-demo-actor':'web-reviewer'},
    body:JSON.stringify({approval_token:token,decision,edited_arguments}),
    cache:'no-store',
  }));
}

export async function getAudit(): Promise<AuditResponse> {
  if (!base()) {
    return {events:[],note:'The zero-key public fallback keeps the visible session trail in the browser.'};
  }
  return readJson<AuditResponse>(await fetch(`${base()}/v1/audit?limit=20`, {cache:'no-store'}));
}

import { NextResponse } from 'next/server';
import { executeTool, runtimeMode } from '@/lib/bridge';
import type { DemoRole } from '@/lib/contracts';

export const dynamic = 'force-dynamic';
const roles = new Set<DemoRole>(['viewer', 'operator', 'approver']);

export async function POST(req: Request) {
  const length = Number(req.headers.get('content-length') || 0);
  if (length > 64 * 1024) return NextResponse.json({error:'payload too large'},{status:413});
  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({error:'malformed JSON'},{status:400}); }
  if (!body || Array.isArray(body) || typeof body !== 'object') return NextResponse.json({error:'JSON object required'},{status:422});
  const value = body as Record<string, unknown>;
  const allowed = new Set(['role','server','tool','arguments']);
  const unknown = Object.keys(value).filter((key) => !allowed.has(key));
  if (unknown.length) return NextResponse.json({error:`Unknown fields: ${unknown.join(', ')}`},{status:422});
  const role = (value.role || 'operator') as DemoRole;
  if (!roles.has(role)) return NextResponse.json({error:'role must be viewer, operator or approver'},{status:422});
  if (typeof value.server !== 'string' || typeof value.tool !== 'string' || !value.arguments || Array.isArray(value.arguments) || typeof value.arguments !== 'object') return NextResponse.json({error:'server, tool and arguments are required'},{status:422});
  try {
    return NextResponse.json(await executeTool(role,value.server,value.tool,value.arguments as Record<string,unknown>),{headers:{'x-mcpbridge-mode':runtimeMode(),'cache-control':'no-store'}});
  } catch (error) {
    return NextResponse.json({error:error instanceof Error?error.message:'execution failed'},{status:403});
  }
}

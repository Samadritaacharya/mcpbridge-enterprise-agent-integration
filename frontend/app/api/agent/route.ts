import { NextResponse } from 'next/server';
import { runAgent, runtimeMode } from '@/lib/bridge';
import type { DemoRole } from '@/lib/contracts';

export const dynamic = 'force-dynamic';
const roles = new Set<DemoRole>(['viewer','operator','approver']);

export async function POST(req: Request) {
  const length = Number(req.headers.get('content-length') || 0);
  if (length > 64 * 1024) return NextResponse.json({error:'payload too large'},{status:413});
  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({error:'malformed JSON'},{status:400}); }
  if (!body || Array.isArray(body) || typeof body !== 'object') return NextResponse.json({error:'JSON object required'},{status:422});
  const value = body as Record<string, unknown>;
  const allowed = new Set(['role','request']);
  const unknown = Object.keys(value).filter((key) => !allowed.has(key));
  if (unknown.length) return NextResponse.json({error:`Unknown fields: ${unknown.join(', ')}`},{status:422});
  const role = (value.role || 'operator') as DemoRole;
  if (!roles.has(role) || typeof value.request !== 'string' || value.request.trim().length < 5 || value.request.length > 2000) return NextResponse.json({error:'valid role and request (5-2000 chars) are required'},{status:422});
  try {
    return NextResponse.json(await runAgent(role,value.request.trim()),{headers:{'x-mcpbridge-mode':runtimeMode(),'cache-control':'no-store'}});
  } catch (error) {
    return NextResponse.json({error:error instanceof Error?error.message:'agent run failed'},{status:403});
  }
}

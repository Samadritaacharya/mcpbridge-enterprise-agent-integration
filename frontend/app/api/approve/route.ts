import { NextResponse } from 'next/server';
import { approveTool, runtimeMode } from '@/lib/bridge';
import type { Decision, DemoRole } from '@/lib/contracts';

export const dynamic = 'force-dynamic';
const decisions = new Set<Decision>(['approve','edit','reject']);
const roles = new Set<DemoRole>(['viewer','operator','approver']);

export async function POST(req: Request) {
  let body: unknown;
  try { body = await req.json(); } catch { return NextResponse.json({error:'malformed JSON'},{status:400}); }
  if (!body || Array.isArray(body) || typeof body !== 'object') return NextResponse.json({error:'JSON object required'},{status:422});
  const value = body as Record<string, unknown>;
  const role = (value.role || 'approver') as DemoRole;
  const decision = value.decision as Decision;
  if (!roles.has(role) || typeof value.approval_token !== 'string' || !decisions.has(decision)) return NextResponse.json({error:'approval_token, valid role and valid decision are required'},{status:422});
  if (decision === 'edit' && (!value.edited_arguments || Array.isArray(value.edited_arguments) || typeof value.edited_arguments !== 'object')) return NextResponse.json({error:'edited_arguments are required for edit'},{status:422});
  try {
    return NextResponse.json(await approveTool(role,value.approval_token,decision,value.edited_arguments as Record<string,unknown>|undefined),{headers:{'x-mcpbridge-mode':runtimeMode(),'cache-control':'no-store'}});
  } catch (error) {
    return NextResponse.json({error:error instanceof Error?error.message:'approval failed'},{status:403});
  }
}

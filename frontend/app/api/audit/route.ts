import { NextResponse } from 'next/server';
import { getAudit, runtimeMode } from '@/lib/bridge';
export const dynamic = 'force-dynamic';
export async function GET(){try{return NextResponse.json(await getAudit(),{headers:{'x-mcpbridge-mode':runtimeMode(),'cache-control':'no-store'}})}catch(error){return NextResponse.json({error:error instanceof Error?error.message:'audit unavailable'},{status:502})}}

import { NextResponse } from 'next/server';
import { getCatalog, runtimeMode } from '@/lib/bridge';
export const dynamic='force-dynamic';
export async function GET(){try{return NextResponse.json(await getCatalog(),{headers:{'x-mcpbridge-mode':runtimeMode(),'cache-control':'no-store'}})}catch(error){return NextResponse.json({error:error instanceof Error?error.message:'catalog unavailable'},{status:502})}}

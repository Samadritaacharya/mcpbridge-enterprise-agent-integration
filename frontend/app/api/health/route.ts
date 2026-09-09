import { NextResponse } from 'next/server';
import { runtimeMode } from '@/lib/bridge';
export const dynamic='force-dynamic';
export function GET(){return NextResponse.json({ok:true,service:'mcpbridge-web',runtime_mode:runtimeMode(),backend_configured:Boolean((process.env.MCPBRIDGE_API_URL||'').trim()),protocol_target:'2026-07-28',transport:'Streamable HTTP',paid_api_required:false,deployment_sha:process.env.VERCEL_GIT_COMMIT_SHA || 'local'});}

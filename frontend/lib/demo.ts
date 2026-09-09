import crypto from 'node:crypto';
import type {
  Catalog,
  Decision,
  DemoRole,
  ExecuteResponse,
  PlannedCall,
  ToolPolicy,
} from './contracts';

const policy = (
  server: string,
  name: string,
  effect: 'read' | 'write',
  approval_required: boolean,
  description: string,
): ToolPolicy => ({
  server,
  name,
  effect,
  approval_required,
  description,
  allowed_roles:
    effect === 'read' ? ['viewer', 'operator', 'approver'] : ['operator', 'approver'],
});

export const demoCatalog: Catalog = {
  protocol_target: '2026-07-28',
  transport: 'Streamable HTTP',
  servers: {
    github: {
      protocol_version: '2026-07-28',
      tools: [
        {name:'search_repository', description:'Search synthetic repository metadata.', policy:policy('github','search_repository','read',false,'Search synthetic repository metadata.')},
        {name:'get_repository_status', description:'Read CI/deployment status.', policy:policy('github','get_repository_status','read',false,'Read CI/deployment status.')},
        {name:'create_github_issue', description:'Create a synthetic GitHub issue.', policy:policy('github','create_github_issue','write',true,'Create a synthetic GitHub issue.')},
      ],
      resources:[{uri_template:'repo://{repo}',name:'repository_resource',description:'Synthetic repository status.'}],
      prompts:[{name:'release_risk_review',description:'Evidence-first release-risk review.'}],
    },
    itsm: {
      protocol_version: '2026-07-28',
      tools: [
        {name:'get_incident', description:'Read an incident.', policy:policy('itsm','get_incident','read',false,'Read an incident.')},
        {name:'create_incident', description:'Create an incident after approval.', policy:policy('itsm','create_incident','write',true,'Create an incident after approval.')},
        {name:'create_change_request', description:'Create a change after approval.', policy:policy('itsm','create_change_request','write',true,'Create a change after approval.')},
      ],
      resources:[{uri_template:'incident://{incident_id}',name:'incident_resource',description:'Synthetic incident details.'}],
      prompts:[{name:'incident_analysis',description:'Evidence-first incident analysis.'}],
    },
    business: {
      protocol_version: '2026-07-28',
      tools: [
        {name:'get_supplier', description:'Read supplier data.', policy:policy('business','get_supplier','read',false,'Read supplier data.')},
        {name:'compare_suppliers', description:'Compare suppliers.', policy:policy('business','compare_suppliers','read',false,'Compare suppliers.')},
        {name:'query_purchase_orders', description:'Read purchase orders.', policy:policy('business','query_purchase_orders','read',false,'Read purchase orders.')},
        {name:'generate_decision_pack', description:'Generate advisory decision pack.', policy:policy('business','generate_decision_pack','read',false,'Generate advisory decision pack.')},
      ],
      resources:[{uri_template:'supplier://{supplier_id}',name:'supplier_resource',description:'Synthetic supplier record.'}],
      prompts:[{name:'supplier_comparison',description:'Supplier comparison prompt.'}],
    },
  },
};

function sign(payload: object) {
  const raw = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const secret = process.env.MCPBRIDGE_DEMO_SECRET || 'portfolio-demo-secret';
  const sig = crypto.createHmac('sha256', secret).update(raw).digest('base64url');
  return `${raw}.${sig}`;
}

function verify(token: string) {
  const [raw, sig] = token.split('.');
  if (!raw || !sig) throw new Error('invalid approval token');
  const secret = process.env.MCPBRIDGE_DEMO_SECRET || 'portfolio-demo-secret';
  const expected = crypto.createHmac('sha256', secret).update(raw).digest('base64url');
  const suppliedBuffer = Buffer.from(sig);
  const expectedBuffer = Buffer.from(expected);
  if (
    suppliedBuffer.length !== expectedBuffer.length ||
    !crypto.timingSafeEqual(suppliedBuffer, expectedBuffer)
  ) {
    throw new Error('invalid approval token');
  }
  return JSON.parse(Buffer.from(raw, 'base64url').toString()) as {
    server: string;
    tool: string;
    arguments: Record<string, unknown>;
    exp: number;
  };
}

function readResult(server: string, tool: string, args: Record<string, unknown>) {
  if (tool === 'get_incident') return {id:args.incident_id || 'INC-428',service:'payments-api',severity:'SEV-2',status:'investigating',summary:'Elevated checkout latency after deployment.'};
  if (tool === 'get_repository_status') return {repo:args.repo || 'payments-api',ci:'degraded',open_prs:6,open_issues:12,last_deploy:'2026-09-09T08:40:00Z'};
  if (tool === 'compare_suppliers') return {summary:'Alpha is lower cost/faster; Beta has longer warranty and security-update coverage.',authority:'advisory-only'};
  if (tool === 'query_purchase_orders') return [{po:'PO-9021',supplier_id:args.supplier_id || 'SUP-ALPHA',status:'approved'}];
  if (tool === 'search_repository') return [{name:'payments-api',ci:'degraded'},{name:'platformpulse',ci:'green'}];
  if (tool === 'get_supplier') return {id:args.supplier_id || 'SUP-ALPHA',unit_price_eur:438,lead_time_days:28,risk:'medium'};
  return {recommendation:'Prefer Alpha for cost/lead-time sensitivity; retain Beta for resilience-led requirements.',requires_human_decision:true};
}

export function demoPlan(request: string): PlannedCall {
  const q = request.toLowerCase();
  if (q.includes('change') && (q.includes('create') || q.includes('request'))) {
    return {server:'itsm',tool:'create_change_request',arguments:{service:'payments-api',summary:request,risk:'medium',implementation_window:'next approved maintenance window'},reason:'Write intent detected: change-management action.'};
  }
  if (q.includes('create incident') || q.includes('open incident')) {
    return {server:'itsm',tool:'create_incident',arguments:{title:'Agent-proposed incident',service:'payments-api',severity:'SEV-2',summary:request},reason:'Write intent detected: incident creation.'};
  }
  if (q.includes('github issue') || q.includes('create issue')) {
    return {server:'github',tool:'create_github_issue',arguments:{repo:'payments-api',title:'Agent-proposed follow-up',body:request,severity:'medium'},reason:'Write intent detected: repository issue creation.'};
  }
  if (q.includes('incident')) return {server:'itsm',tool:'get_incident',arguments:{incident_id:q.includes('431')?'INC-431':'INC-428'},reason:'Read-only ITSM investigation.'};
  if (q.includes('repository') || q.includes('repo') || q.includes('ci') || q.includes('deploy')) return {server:'github',tool:'get_repository_status',arguments:{repo:q.includes('payment')?'payments-api':'platformpulse'},reason:'Read-only repository health request.'};
  if (q.includes('purchase order') || q.includes(' po ')) return {server:'business',tool:'query_purchase_orders',arguments:{supplier_id:q.includes('beta')?'SUP-BETA':'SUP-ALPHA'},reason:'Read-only business-system query.'};
  if (q.includes('supplier') || q.includes('alpha') || q.includes('beta')) return {server:'business',tool:'compare_suppliers',arguments:{left:'SUP-ALPHA',right:'SUP-BETA'},reason:'Read-only supplier comparison.'};
  return {server:'business',tool:'generate_decision_pack',arguments:{question:request},reason:'Default advisory decision-pack route.'};
}

export function demoExecute(
  role: DemoRole,
  server: string,
  tool: string,
  args: Record<string, unknown>,
): ExecuteResponse {
  const p = Object.values(demoCatalog.servers)
    .flatMap((item) => item.tools)
    .find((item) => item.policy.server === server && item.name === tool)?.policy;
  if (!p) throw new Error('tool is not allowlisted');
  if (!p.allowed_roles.includes(role)) throw new Error(`role ${role} cannot call ${server}.${tool}`);
  if (p.approval_required) {
    const approval_token = sign({server,tool,arguments:args,exp:Date.now()+5*60_000});
    return {status:'approval_required',effect:'write',server,tool,arguments:args,approval_token,message:'Sensitive MCP write is blocked until an approver explicitly approves, edits or rejects it.'};
  }
  return {status:'completed',effect:'read',server,tool,arguments:args,result:readResult(server,tool,args)};
}

export function demoAgentRun(role: DemoRole, request: string): ExecuteResponse {
  const plan = demoPlan(request);
  return {...demoExecute(role, plan.server, plan.tool, plan.arguments), plan};
}

export function demoApprove(
  role: DemoRole,
  token: string,
  decision: Decision,
  edited?: Record<string, unknown>,
): ExecuteResponse {
  if (role !== 'approver') throw new Error('only the approver role can authorize a write');
  const body = verify(token);
  if (body.exp < Date.now()) throw new Error('approval token expired');
  if (decision === 'reject') return {status:'rejected',effect:'write',server:body.server,tool:body.tool,arguments:body.arguments};
  if (decision === 'edit' && !edited) throw new Error('edited arguments are required for edit');
  const args = decision === 'edit' ? edited! : body.arguments;
  return {status:'completed',effect:'write',server:body.server,tool:body.tool,arguments:args,result:{synthetic:true,status:'created',id:`${body.tool.includes('change')?'CHG':body.tool.includes('incident')?'INC':'ISS'}-${Math.floor(1000+Math.random()*8000)}`}};
}

'use client';

import { useEffect, useMemo, useState } from 'react';
import type {
  AuditEvent,
  Catalog,
  Decision,
  DemoRole,
  ExecuteResponse,
  ToolDescriptor,
} from '@/lib/contracts';

const presets = [
  {label:'Investigate incident',server:'itsm',tool:'get_incident',args:{incident_id:'INC-428'}},
  {label:'Check repository health',server:'github',tool:'get_repository_status',args:{repo:'payments-api'}},
  {label:'Compare suppliers',server:'business',tool:'compare_suppliers',args:{left:'SUP-ALPHA',right:'SUP-BETA'}},
  {label:'Create change request',server:'itsm',tool:'create_change_request',args:{service:'payments-api',summary:'Roll back suspect deployment after latency spike',risk:'medium',implementation_window:'next approved maintenance window'}},
  {label:'Create GitHub issue',server:'github',tool:'create_github_issue',args:{repo:'payments-api',title:'Follow up on latency regression',body:'Add regression test and deployment guardrail.',severity:'medium'}},
] as const;

const agentPresets = [
  'Show me incident INC-428 and its current status.',
  'Check the payments repository CI and deployment health.',
  'Compare Supplier Alpha and Beta for cost, lead time and resilience.',
  'Create a change request for payments-api after the latency incident.',
];

type SessionEvent = {
  ts: string;
  phase: string;
  server: string;
  tool: string;
  role: DemoRole;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && !Array.isArray(value) && typeof value === 'object';
}

export default function GatewayConsole() {
  const [catalog,setCatalog] = useState<Catalog|null>(null);
  const [role,setRole] = useState<DemoRole>('operator');
  const [selected,setSelected] = useState<(typeof presets)[number]>(presets[0]);
  const [agentRequest,setAgentRequest] = useState(agentPresets[0]);
  const [result,setResult] = useState<ExecuteResponse|null>(null);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [sessionAudit,setSessionAudit] = useState<SessionEvent[]>([]);
  const [backendAudit,setBackendAudit] = useState<AuditEvent[]>([]);
  const [editArguments,setEditArguments] = useState('{}');
  const [runtime,setRuntime] = useState('loading');

  useEffect(() => {
    Promise.all([
      fetch('/api/catalog').then((response) => response.json() as Promise<Catalog>),
      fetch('/api/health').then((response) => response.json() as Promise<{runtime_mode?:string}>),
    ])
      .then(([nextCatalog, health]) => {
        setCatalog(nextCatalog);
        setRuntime(health.runtime_mode || 'unknown');
      })
      .catch(() => setError('Catalog unavailable'));
  }, []);

  const tools = useMemo(
    () => catalog
      ? Object.entries(catalog.servers).flatMap(([server, descriptor]) =>
          descriptor.tools.map((tool) => ({...tool, server})),
        )
      : [],
    [catalog],
  );

  function record(next: ExecuteResponse) {
    setResult(next);
    if (next.arguments) setEditArguments(JSON.stringify(next.arguments,null,2));
    setSessionAudit((events) => [
      {ts:new Date().toISOString(),phase:next.status,server:next.server,tool:next.tool,role},
      ...events,
    ].slice(0,10));
  }

  async function post(path: string, body: Record<string, unknown>) {
    const response = await fetch(path, {
      method:'POST',
      headers:{'content-type':'application/json'},
      body:JSON.stringify(body),
    });
    const payload = await response.json() as Record<string, unknown>;
    if (!response.ok) throw new Error(String(payload.error || `Request failed (${response.status})`));
    return payload as ExecuteResponse;
  }

  async function runTool() {
    setBusy(true); setError('');
    try {
      record(await post('/api/execute',{role,server:selected.server,tool:selected.tool,arguments:selected.args}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Execution failed');
    } finally { setBusy(false); }
  }

  async function runAgent() {
    setBusy(true); setError('');
    try {
      record(await post('/api/agent',{role,request:agentRequest}));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Agent run failed');
    } finally { setBusy(false); }
  }

  async function decide(decision: Decision) {
    if (!result?.approval_token) return;
    setBusy(true); setError('');
    try {
      let edited: Record<string, unknown>|undefined;
      if (decision === 'edit') {
        let parsed: unknown;
        try { parsed = JSON.parse(editArguments); } catch { throw new Error('Edited arguments must be valid JSON'); }
        if (!isRecord(parsed)) throw new Error('Edited arguments must be a JSON object');
        edited = parsed;
      }
      record(await post('/api/approve',{
        role,
        approval_token:result.approval_token,
        decision,
        ...(edited ? {edited_arguments:edited} : {}),
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Decision failed');
    } finally { setBusy(false); }
  }

  async function loadAudit() {
    setError('');
    try {
      const response = await fetch('/api/audit',{cache:'no-store'});
      const payload = await response.json() as {events?:AuditEvent[];error?:string};
      if (!response.ok) throw new Error(payload.error || 'Audit unavailable');
      setBackendAudit(payload.events || []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Audit unavailable');
    }
  }

  return <main>
    <div className="gridGlow" />
    <nav>
      <a href="#top" className="brand">MCP<span>Bridge</span></a>
      <div className="navlinks">
        <a href="#console">Console</a><a href="#catalog">MCP Catalog</a><a href="#architecture">Architecture</a>
        <a href="https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration" target="_blank" rel="noreferrer">Source ↗</a>
      </div>
    </nav>

    <section id="top" className="hero">
      <div>
        <div className="eyebrow">MODEL CONTEXT PROTOCOL · ENTERPRISE AGENT INTEGRATION</div>
        <h1>Give AI agents tools.<br/><em>Keep humans in control.</em></h1>
        <p>MCPBridge exposes synthetic GitHub, ITSM and business capabilities as MCP tools, resources and prompts, then places allowlists, role permissions, explicit human approval and auditable execution between agent intent and sensitive writes.</p>
        <div className="heroTags"><span>MCP 2026-07-28</span><span>Streamable HTTP</span><span>LangGraph HITL</span><span>Policy Gateway</span><span>Audit Chain</span></div>
        <div className="runtimeBanner"><b>{runtime === 'connected-python-mcp' ? 'CONNECTED PYTHON MCP' : 'ZERO-KEY PUBLIC DEMO'}</b><span>{runtime === 'connected-python-mcp' ? 'Next.js → Python gateway → official MCP Client/Servers' : 'Deterministic portfolio fallback; real MCP + LangGraph are verified in CI.'}</span></div>
      </div>
      <div className="network"><div className="core">MCPBridge<small>policy + approval</small></div>{['GitHub MCP','ITSM MCP','Business MCP'].map((label,index)=><div key={label} className={`node n${index+1}`}>{label}</div>)}</div>
    </section>

    <section className="stats"><div><b>3</b><span>MCP servers</span></div><div><b>10</b><span>allowlisted tools</span></div><div><b>3</b><span>resources</span></div><div><b>3</b><span>prompts</span></div><div><b>HITL</b><span>write control</span></div></section>

    <section id="console" className="console">
      <div className="sectionHead"><span>01 · AGENT GATEWAY</span><h2>Read automatically. Gate every write.</h2><p>Use natural-language routing or invoke a specific MCP contract. Viewer, operator and approver roles make the policy boundary visible rather than burying authorization inside the model.</p></div>
      <div className="consoleGrid">
        <div className="panel">
          <label>Demo role</label><div className="roleRow">{(['viewer','operator','approver'] as DemoRole[]).map((item)=><button key={item} className={role===item?'active':''} onClick={()=>setRole(item)}>{item}</button>)}</div>
          <label>Agent request</label><textarea value={agentRequest} onChange={(event)=>setAgentRequest(event.target.value)} rows={3}/><div className="agentPresets">{agentPresets.map((request)=><button key={request} onClick={()=>setAgentRequest(request)}>{request}</button>)}</div><button className="primary" disabled={busy} onClick={runAgent}>{busy?'Executing…':'Plan + execute through gateway →'}</button>
          <div className="divider"><span>OR INVOKE A CONTRACT</span></div>
          <label>Workflow</label><div className="presetList">{presets.map((preset)=><button key={preset.label} className={selected.label===preset.label?'active':''} onClick={()=>{setSelected(preset);setResult(null)}}><span>{preset.label}</span><small>{preset.server}.{preset.tool}</small></button>)}</div>
          <label>Tool arguments</label><pre>{JSON.stringify(selected.args,null,2)}</pre><button className="secondary" disabled={busy} onClick={runTool}>Invoke selected MCP contract →</button>{error&&<p className="error">{error}</p>}
        </div>

        <div className="panel result">
          <div className="resultHead"><div><span>Execution state</span><b>{result?.status||'ready'}</b></div><div className="mode">{catalog?.protocol_target||'2026-07-28'}</div></div>
          {!result?<div className="empty">Run an agent request or MCP contract to inspect routing, policy, tool output and approval behavior.</div>:<>
            {result.plan&&<div className="planCard"><span>Planner decision</span><b>{result.plan.server}.{result.plan.tool}</b><p>{result.plan.reason}</p></div>}
            <div className="call"><span>{result.server}</span><strong>{result.tool}</strong><i className={result.effect==='write'?'write':'read'}>{result.effect||'read'}</i></div>
            <pre className="output">{JSON.stringify(result.result||result.arguments||result.message,null,2)}</pre>
            {result.audit_event?.event_hash&&<div className="auditProof"><span>Audit event</span><code>{result.audit_event.event_hash.slice(0,18)}…</code><small>request {result.audit_event.request_hash?.slice(0,14)}…</small></div>}
            {result.status==='approval_required'&&<div className="approval"><b>Human approval required</b><p>This write has been proposed but not executed. Only the <strong>approver</strong> role may release it.</p><label>Editable arguments for “edit”</label><textarea value={editArguments} onChange={(event)=>setEditArguments(event.target.value)} rows={8}/><div>{(['approve','edit','reject'] as Decision[]).map((decision)=><button key={decision} disabled={busy||role!=='approver'} onClick={()=>decide(decision)}>{decision}</button>)}</div>{role!=='approver'&&<small>Switch Demo role to approver to review this action.</small>}</div>}
          </>}
        </div>
      </div>
    </section>

    <section id="catalog" className="catalog"><div className="sectionHead"><span>02 · MCP SURFACE</span><h2>Tools, resources and prompts are first-class contracts.</h2><p>The Python catalog is discovered through real MCP Clients in connected mode; every discovered tool must also exist in the fail-closed policy registry.</p></div><div className="serverGrid">{catalog&&Object.entries(catalog.servers).map(([name,server])=><article key={name}><header><b>{name.toUpperCase()} MCP</b><span>{server.protocol_version}</span></header><h3>Tools</h3>{server.tools.map((tool:ToolDescriptor)=><div className="tool" key={tool.name}><code>{tool.name}</code><span className={tool.policy.effect}>{tool.policy.effect}{tool.policy.approval_required?' · approval':''}</span><p>{tool.description}</p></div>)}<h3>Resources</h3>{server.resources.map((resource)=><code className="resource" key={resource.uri_template}>{resource.uri_template}</code>)}<h3>Prompts</h3>{server.prompts.map((prompt)=><code className="resource" key={prompt.name}>{prompt.name}</code>)}</article>)}</div></section>

    <section id="architecture" className="architecture"><div className="sectionHead"><span>03 · CONTROL PLANE</span><h2>Agent autonomy ends at the policy boundary.</h2></div><div className="flow">{['User intent','Deterministic planner','MCP Client','Tool registry','Policy + role check','Human interrupt','MCP execution','Hash-linked audit'].map((label,index)=><div key={label}><span>{String(index+1).padStart(2,'0')}</span><b>{label}</b></div>)}</div><div className="principles"><article><b>Protocol-native</b><p>Official MCP Python SDK server/client contracts, modern 2026 protocol target, Streamable HTTP and in-process protocol tests.</p></article><article><b>Least privilege</b><p>Read/write effects are explicit. Viewer/operator/approver roles are separate and non-allowlisted tools fail closed.</p></article><article><b>Human authority</b><p>Sensitive writes are proposals first. HMAC tokens bind the exact proposed tool call; LangGraph interrupt/resume is verified separately in CI.</p></article><article><b>Inspectable automation</b><p>Each proposal or execution emits a request hash plus previous/current event hashes for tamper-evident linking.</p></article></div></section>

    <section className="audit"><div className="sectionHead"><span>04 · AUDITABILITY</span><h2>Inspect what the gateway did.</h2><button className="secondary compact" onClick={loadAudit}>Load backend audit</button></div>{backendAudit.length>0?<>{backendAudit.map((event)=><div className="auditRow" key={event.event_id}><span>{event.timestamp?.slice(11,19)}</span><b>{event.decision}</b><code>{event.server}.{event.tool}</code><small>{event.event_hash?.slice(0,16)}…</small></div>)}</>:sessionAudit.length===0?<p className="emptyLine">No session events yet.</p>:sessionAudit.map((event,index)=><div className="auditRow" key={`${event.ts}-${index}`}><span>{event.ts.slice(11,19)}</span><b>{event.phase}</b><code>{event.server}.{event.tool}</code><small>{event.role}</small></div>)}</section>

    <footer><b>MCPBridge</b><span>Synthetic systems · portfolio-safe · no confidential enterprise data</span><a href="https://github.com/Samadritaacharya/mcpbridge-enterprise-agent-integration" target="_blank" rel="noreferrer">GitHub ↗</a></footer>
  </main>;
}

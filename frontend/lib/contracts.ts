export type DemoRole = 'viewer' | 'operator' | 'approver';
export type Effect = 'read' | 'write';
export type Decision = 'approve' | 'edit' | 'reject';
export type RuntimeMode = 'deterministic-public-demo' | 'connected-python-mcp';

export type ToolPolicy = {
  server: string;
  name: string;
  effect: Effect;
  allowed_roles: DemoRole[];
  approval_required: boolean;
  description: string;
};

export type ToolDescriptor = {
  name: string;
  description: string;
  input_schema?: Record<string, unknown>;
  policy: ToolPolicy;
};

export type ResourceDescriptor = {
  uri_template: string;
  name: string;
  description?: string;
};

export type PromptDescriptor = {
  name: string;
  description: string;
};

export type CatalogServer = {
  protocol_version: string;
  tools: ToolDescriptor[];
  resources: ResourceDescriptor[];
  prompts: PromptDescriptor[];
};

export type Catalog = {
  protocol_target: string;
  transport: string;
  servers: Record<string, CatalogServer>;
};

export type AuditEvent = {
  event_id?: string;
  timestamp?: string;
  actor?: string;
  role?: string;
  phase?: string;
  server?: string;
  tool?: string;
  decision?: string;
  request_hash?: string;
  previous_hash?: string;
  event_hash?: string;
};

export type PlannedCall = {
  server: string;
  tool: string;
  arguments: Record<string, unknown>;
  reason: string;
};

export type ExecuteResponse = {
  status: 'completed' | 'approval_required' | 'rejected';
  effect?: Effect;
  server: string;
  tool: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  approval_token?: string;
  message?: string;
  audit_event?: AuditEvent;
  decision?: Decision;
  plan?: PlannedCall;
};

export type AuditResponse = {
  events: AuditEvent[];
  chain_valid?: boolean;
  persistence?: string;
  note?: string;
};

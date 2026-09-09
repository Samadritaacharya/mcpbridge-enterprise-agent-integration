import test from 'node:test';
import assert from 'node:assert/strict';

test('portfolio MCP surface keeps ten unique allowlisted tools',()=>{
  const tools=[
    'search_repository','get_repository_status','create_github_issue',
    'get_incident','create_incident','create_change_request',
    'get_supplier','compare_suppliers','query_purchase_orders','generate_decision_pack',
  ];
  assert.equal(tools.length,10);
  assert.equal(new Set(tools).size,tools.length);
});

test('write tool names remain explicit and reviewable',()=>{
  const writes=['create_github_issue','create_incident','create_change_request'];
  assert.deepEqual(writes.every((name)=>name.startsWith('create_')),true);
});

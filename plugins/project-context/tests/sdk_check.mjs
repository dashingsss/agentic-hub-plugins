import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const payload = path.resolve(process.argv[2]);
const sdk = process.env.MCP_SDK_ESM;
if (!sdk) throw new Error('请通过 MCP_SDK_ESM 指定现有独立 MCP SDK，仅作开发验证依赖');
const { Client } = await import(pathToFileURL(path.join(sdk, 'client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(path.join(sdk, 'client/stdio.js')));
const config = JSON.parse(readFileSync(path.join(payload, 'mcps/project-context/mcp.json'), 'utf8')).mcpServers['project-context'];
const cache = mkdtempSync(path.join(tmpdir(), 'project-context-sdk-'));
let calls = 0;
let client;
const connect = async () => {
  client = new Client({ name: '项目资料导航独立协议测试', version: '1.0.0' });
  await client.connect(new StdioClientTransport({ command: config.command, args: config.args,
    cwd: path.join(payload, 'mcps/project-context'), env: { ...process.env, PROJECT_CONTEXT_STATE_DIR: cache } }));
};
const invoke = async (name, args = {}, failure = false) => {
  const response = await client.callTool({ name, arguments: args });
  calls += 1;
  assert.equal(Boolean(response.isError), failure);
  const data = JSON.parse(response.content[0].text);
  assert.equal(data.ok, !failure);
  return data;
};
try {
  await connect();
  assert.equal((await client.listTools()).tools.length, 6);
  assert.equal((await invoke('context_status')).version, '1.0.0');
  const demo = await invoke('context_demo');
  const workspace = { workspace_id: demo.workspace_id };
  const found = await invoke('context_find', { ...workspace, query: '登录设计 tokenlogin 离线缓存' });
  assert.equal(found.pack.primary[0].rel, 'docs/login-design.md');
  await invoke('context_control', { ...workspace, action: 'pin', path: 'docs/login-design.md' });
  await invoke('context_control', { ...workspace, action: 'exclude', path: 'docs/login-old.md' });
  await invoke('context_read', { ...workspace, path: 'docs/login-design.md', expected_sha256: found.pack.primary[0].sha256 });
  await invoke('context_read', { ...workspace, path: '../outside.md' }, true);
  await client.close();
  await connect();
  const status = await invoke('context_status', workspace);
  assert.deepEqual(status.exclusions, ['docs/login-old.md']);
  assert.deepEqual(status.pins, ['docs/login-design.md']);
  assert.match(status.reads[0].status, /未变化/);
  console.log(JSON.stringify({ result: 'PASS', tools: 6, tool_calls: calls, independent_restart: true,
    payload, note: '独立 MCP SDK 验证，不等于 WorkSwarm 用户验收' }));
} finally {
  if (client) await client.close();
  rmSync(cache, { recursive: true, force: true });
}

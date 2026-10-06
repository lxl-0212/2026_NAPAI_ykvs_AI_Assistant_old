import { spawn } from 'node:child_process';
import readline from 'node:readline';
import { resolve } from 'node:path';

export class MCPClient {
  constructor() { this.proc = null; this.nextId = 1; this.pending = new Map(); this.tools = []; }
  async connect() {
    if (this.proc) return;
    const cwd = resolve(process.env.MCP_SERVER_DIR || process.cwd());
    const python = process.env.PYTHON_BIN || 'python3';
    this.proc = spawn(python, ['hello_tool.py'], { cwd, stdio: ['pipe', 'pipe', 'pipe'], env: process.env });
    this.proc.on('error', (err) => {
      for (const [, p] of this.pending) p.reject(err);
      this.pending.clear();
    });
    this.proc.on('exit', (code, signal) => {
      const e = new Error(`MCP server exited (code=${code}, signal=${signal})`);
      for (const [, p] of this.pending) p.reject(e);
      this.pending.clear();
      this.proc = null;
    });
    this.proc.stderr.on('data', b => console.error(`[MCP] ${String(b).trim()}`));
    readline.createInterface({ input: this.proc.stdout }).on('line', line => this._handleLine(line));
    await this._request('initialize', {
      protocolVersion: '2025-06-18',
      capabilities: {},
      clientInfo: { name: 'ykvs-ai-assistant', version: '1.0.0' }
    });
    this._notify('notifications/initialized', {});
    const listed = await this._request('tools/list', {});
    this.tools = listed?.tools ?? [];
    console.log(`[MCP] tools: ${this.tools.map(t => t.name).join(', ')}`);
  }
  _handleLine(line) {
    if (!line.trim()) return;
    let msg;
    try { msg = JSON.parse(line); } catch { return; }
    if (msg.id == null) return;
    const p = this.pending.get(msg.id);
    if (!p) return;
    this.pending.delete(msg.id);
    msg.error ? p.reject(new Error(msg.error.message || JSON.stringify(msg.error))) : p.resolve(msg.result);
  }
  _request(method, params = {}) {
    if (!this.proc) throw new Error('MCP server 尚未連線');
    const id = this.nextId++;
    return new Promise((resolvePromise, reject) => {
      this.pending.set(id, { resolve: resolvePromise, reject });
      this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    });
  }
  _notify(method, params = {}) {
    if (this.proc) this.proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
  }
  getOpenAITools() {
    return this.tools.map(t => ({
      type: 'function',
      function: { name: t.name, description: t.description || '', parameters: t.inputSchema || { type: 'object', properties: {} } }
    }));
  }
  async callTool(name, args = {}) {
    const r = await this._request('tools/call', { name, arguments: args });
    return (r?.content || []).filter(x => x?.type === 'text').map(x => x.text).join('\n') || JSON.stringify(r ?? {}, null, 2);
  }
}

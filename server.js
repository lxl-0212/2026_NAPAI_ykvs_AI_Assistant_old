import 'dotenv/config';
import express from 'express';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { MCPClient } from './mcp-client.js';
import { OpenAILLMClient } from './llm-client-openai.js';
import { getQuickReply } from './quick-reply.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
process.chdir(ROOT);

const mcp = new MCPClient();
await mcp.connect();
const llm = new OpenAILLMClient(mcp);

const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(express.static(join(ROOT, 'web')));
app.get('/healthz', (_req, res) => res.json({ ok: true }));

function looksLikeSchoolQuestion(q) {
  return /鶯歌|校|分機|電話|教室|場館|處室|老師|教師|主任|組長|姓名|行事曆|行程|請假|手機|行動載具|獎懲|品德|生活秩序|法規|規定|成績|段考|考試|補考|重修|補修|學分|畢業|編班|轉班|抵免|學習歷程/.test(q);
}

app.post('/chat', async (req, res) => {
  const { messages } = req.body ?? {};
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: 'messages (array) is required' });
  }
  try {
    const last = [...messages].reverse().find(m => m?.role === 'user');
    const query = String(last?.content ?? '');
    const quick = await getQuickReply(query, mcp);
    if (quick !== null && !looksLikeSchoolQuestion(query)) {
      return res.json({ reply: quick, messages: [...messages, { role:'assistant', content:quick }] });
    }
    const result = await llm.chat(messages, { forceSchoolTool: looksLikeSchoolQuestion(query) });
    res.json(result);
  } catch (err) {
    console.error('[chat error]', err);
    res.status(500).json({ error: err?.message || String(err) });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`→ YKVS AI Assistant old version: http://localhost:${PORT}`));

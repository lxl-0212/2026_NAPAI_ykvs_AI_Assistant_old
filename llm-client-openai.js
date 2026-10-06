import OpenAI from 'openai';

export class OpenAILLMClient {
  constructor(mcp,{baseURL=process.env.OPENAI_BASE_URL||'https://generativelanguage.googleapis.com/v1beta/openai/',apiKey=process.env.OPENAI_API_KEY||process.env.GEMINI_API_KEY||'dummy',model=process.env.OPENAI_MODEL||'gemini-3.1-flash-lite',maxTokens=1200}={}) {
    this.openai=new OpenAI({baseURL,apiKey,maxRetries:0,timeout:45000}); this.mcp=mcp; this.model=model; this.maxTokens=maxTokens;
  }
  _normalize(messages){ return messages.map(m=>Array.isArray(m.content)?{role:m.role,content:m.content.filter(x=>x?.type==='text').map(x=>x.text).join('')}:m); }
  async chat(messages,{maxIterations=4,forceSchoolTool=false}={}) {
    const system={role:'system',content:`你是「鶯歌工商校務 AI 助理」的舊版。你的目標是讓學生與老師可以用自然語言直接描述問題，並快速理解答案與下一步怎麼做。

重要規則：
1. 涉及鶯歌工商的分機、人名、處室、教室、場館、行事曆、請假、校務規定等資訊，必須先使用 search_school_info 查詢校方資料，不可以憑記憶猜測。
2. 查到資料後，請用自然、簡單、容易理解的繁體中文回答；不要把 JSON 原封不動丟給使用者。
3. 回答重點放在「答案是什麼」以及「師生接下來怎麼做」。必要時用條列式。
4. 不要主動顯示資料來源、來源網址、引用連結、文件名稱或「資料來源」欄位。這是舊版的特色。
5. 使用者沒有要求法規原文時，不要貼大量條文；先用白話說明怎麼做。
6. 資料查不到時要明確說「目前找不到相關校務資料」，不要自行編造。
7. 一般聊天問題可以直接回答；校務問題以 MCP 查到的資料為準。`};
    let history=[system,...this._normalize(messages)];
    for(let i=0;i<maxIterations;i++){
      const req={model:this.model,max_tokens:this.maxTokens,tools:this.mcp.getOpenAITools(),messages:history};
      if(forceSchoolTool && i===0) req.tool_choice={type:'function',function:{name:'search_school_info'}};
      const resp=await this.openai.chat.completions.create(req);
      const msg=resp.choices[0].message; history.push(msg);
      if(!msg.tool_calls?.length) return {reply:String(msg.content||'').replace(/<\|channel>.*?<channel\|>/gs,'').trim(),messages:history.slice(1)};
      const results=await Promise.all(msg.tool_calls.map(async tc=>{let args={};try{args=JSON.parse(tc.function.arguments||'{}')}catch{};try{return {role:'tool',tool_call_id:tc.id,content:await this.mcp.callTool(tc.function.name,args)}}catch(e){return {role:'tool',tool_call_id:tc.id,content:`Error: ${e.message}`}}}));
      history.push(...results);
    }
    throw new Error('AI 查詢超過預期次數，請再試一次。');
  }
}

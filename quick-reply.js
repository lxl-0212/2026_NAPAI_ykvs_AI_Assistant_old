const TIME_ZONE='Asia/Taipei';
function isDateOrWeekdayQuestion(q){return /星期幾|禮拜幾|週幾|今天幾號|今日幾號|今天日期|今日日期|今天星期|今日星期/.test(q)}
function isTimeQuestion(q){return /現在幾點|當地時間|當地幾點/.test(q)}
export async function getQuickReply(query,_mcp,now=new Date()){
  if(/天氣|氣溫|下雨|降雨|天候/.test(query)) return null;
  if(!isDateOrWeekdayQuestion(query)&&!isTimeQuestion(query)) return null;
  const text=new Intl.DateTimeFormat('zh-TW',{timeZone:TIME_ZONE,year:'numeric',month:'long',day:'numeric',weekday:'long',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(now);
  if(isTimeQuestion(query)) return `現在台灣時間是 ${text}。`;
  return `今天是 ${text}。`;
}

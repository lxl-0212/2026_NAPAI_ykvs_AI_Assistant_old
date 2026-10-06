# 鶯歌工商 Mini AI Assistant｜舊版

這是提供與新版比較用的「舊版自然語言助理」。

## 舊版特色
- 師生可以直接用自然語言輸入問題。
- AI 先查鶯歌工商校務資料，再用白話整理回答。
- 重點放在「答案是什麼」與「接下來怎麼做」。
- **不主動顯示資料來源／來源網址**，以便和新版來源查證版比較。
- 查不到資料時不猜測。

## 啟動
```bash
npm install
python3 -m pip install -r requirements.txt
GEMINI_API_KEY=你的金鑰 npm start
```

Render 環境變數請設定 `GEMINI_API_KEY`。也可使用 OpenAI-compatible endpoint。

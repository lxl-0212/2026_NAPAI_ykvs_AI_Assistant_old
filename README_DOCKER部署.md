# 鶯歌工商 AI Assistant｜Docker 部署版

這一版是給 Render 使用的 Docker 版本。

## 為什麼要用 Docker？

本專案同時需要：
- Node.js：網站與 AI API
- Python 3：MCP 校務資料查詢工具

Render 原本使用 Node Runtime 時，會出現：
`Error: spawn python3 ENOENT`

代表執行環境找不到 Python。Docker 版會在同一個容器內安裝 Node.js、Python 3 與 MCP 套件。

## GitHub 上傳方式

1. 下載 ZIP。
2. 解壓縮。
3. 打開 `ykvs-ai-assistant-old-version-docker` 資料夾。
4. 把裡面的「全部檔案與資料夾」放到 GitHub Repository 根目錄。
5. 不要只上傳 ZIP 檔。
6. Commit changes。

專案根目錄應該可以看到：
- Dockerfile
- package.json
- requirements.txt
- render.yaml
- backend-node/
- mcp-server-py/
- web/

## Render 設定

Runtime：`Docker`

Dockerfile Path：`./Dockerfile`

Build Command：留空

Start Command：留空（使用 Dockerfile 的 CMD）

Health Check Path：`/healthz`

Environment Variables：依你的 AI API 設定填入，例如：
- `GEMINI_API_KEY`
- `OPENAI_BASE_URL`（若使用其他 OpenAI-compatible API）
- `OPENAI_MODEL`

## 部署後測試

先開：
`/healthz`

正常應看到：
`{"ok":true}`

再測試：
- 我要查資處科6D電腦教室分機
- 資處6D電腦教室分機
- 6D電腦教室電話
- 我要找教務主任電話
- 我段考生病沒去，接下來要怎麼辦
- 請假規定

## 重要

這版保留舊版資料結構與自然語言查詢方式，只把 Render 執行環境改成 Docker，讓 Node + Python MCP 可以一起執行。

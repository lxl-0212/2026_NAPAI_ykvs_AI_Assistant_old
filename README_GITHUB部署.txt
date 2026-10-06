鶯歌工商 AI 助理｜GitHub 根目錄 Docker 版

這個壓縮包就是「GitHub 根目錄版」，解壓縮後，將裡面的全部檔案與資料夾上傳到 GitHub repository 根目錄。

Render 設定：
- Language: Docker
- Docker Build Context Directory: .
- Dockerfile Path: ./Dockerfile
- Docker Command: 留空（Dockerfile 已設定 CMD）
- Health Check Path: /healthz
- Plan: Free
- Environment Variable: GEMINI_API_KEY = 你的 Gemini API Key

重要：不要再把 Docker Command 設為 node backend-node/server.js；這個版本的 server.js 在 GitHub 根目錄。

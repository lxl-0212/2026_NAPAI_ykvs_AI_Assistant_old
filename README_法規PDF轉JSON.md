# 鶯歌工商法規 PDF → JSON 擴充工具

這份工具沿用既有 `search_school_info(query)` MCP，不新增 API key 或第二套查詢伺服器。各處室經校方公開或核准的規定 PDF 可批次抽取成 JSON；工具保留原文段落、頁碼、版本與官方網址，供 MCP 依問題檢索並讓模型附來源回答。

## JSON 會保留什麼

每份 PDF 的每個檢索段落都含有：`data_id`、`category`、`department`、`unit`、`title`、`content`、`keywords`、`publication_date`、`version`、`source_url`、`source_pdf`、`page_start`、`page_end`、`last_verified_date`、`owner`、`review_status`、`sha256`。

程式只抽取和分段原文，不會自行推斷申請資格、金額、期限或處分。每段預設標示「待人工抽核」。若 PDF 是影像掃描，工具會停止並提示須先 OCR 和校對，不會輸出空白內容。

## 用您列出的四份文件擴充

1. 從校方公告頁下載訓育組兩份助學金 PDF，以及教學組兩份 PDF。將原始檔放在 `scripts/pdf_inputs/`，檔名與清單中的 `file` 欄位一致；不必手動拆成 CSV。
2. 開啟 `scripts/新增處室法規清單範例.json`，確認每個 `file` 與實際檔名一致。
3. 檢查每個 `source_url` 確實仍可開啟，將 `last_verified_date` 改成實際檢查日，並依校方文件更新版本、公告日期、關鍵字和資料維護單位。
4. 將工具包解壓至 `/content/ykvs_regulation_update`，在 Colab 上傳四份 PDF 到對應的 `scripts/pdf_inputs/`：

```python
from google.colab import files
from pathlib import Path
import zipfile

uploaded_zip = files.upload()  # 選取法規轉換工具 ZIP
update_root = Path('/content/ykvs_regulation_update')
with zipfile.ZipFile(next(iter(uploaded_zip))) as z:
    z.extractall(update_root)

uploaded_pdfs = files.upload()  # 選取四份 PDF
pdf_dir = Path('/content/nchu-mcp-workshop-2026/mini-project/scripts/pdf_inputs')
pdf_dir.mkdir(parents=True, exist_ok=True)
for name, data in uploaded_pdfs.items():
    (pdf_dir / name).write_bytes(data)
```

若實際下載檔名不同，請修改清單的 `file` 欄位，讓它和 `scripts/pdf_inputs/` 內的檔名一致。

5. 備份目前 MCP 程式，再複製支援新 JSON 查詢的工具程式與轉換器：

```python
from pathlib import Path
import shutil

project = Path('/content/nchu-mcp-workshop-2026/mini-project')
updated = update_root / 'nchu-mcp-workshop-2026/mini-project'
shutil.copy2(project / 'mcp-server-py/hello_tool.py', '/content/hello_tool.before_regulation_json.py')
shutil.copy2(updated / 'mcp-server-py/hello_tool.py', project / 'mcp-server-py/hello_tool.py')
(project / 'scripts').mkdir(parents=True, exist_ok=True)
shutil.copy2(updated / 'scripts/pdf_to_regulations_json.py', project / 'scripts/pdf_to_regulations_json.py')
shutil.copy2(updated / 'scripts/新增處室法規清單範例.json', project / 'scripts/新增處室法規清單範例.json')
```

6. 在 Colab 專案根目錄執行轉檔：

```python
%cd /content/nchu-mcp-workshop-2026/mini-project
!pip -q install pdfplumber
!python scripts/pdf_to_regulations_json.py \
  --manifest scripts/新增處室法規清單範例.json \
  --output mcp-server-py/data/ykvs_mvp_source_pack/data/additional_regulations.json
```

7. 抽查 JSON 文件數、頁數、每筆 `source_url`、頁碼和文字；逐頁對照原 PDF 的資格、金額、期限、申請方式及例外條款。確認後，將每筆 `review_status` 從「待人工抽核」改成教師核可狀態，並保留原始 PDF。
8. 執行原有 server 重啟 cell。既有 MCP 工具會讀取 `additional_regulations.json`，不用新增 MCP 名稱或 API Key。

## 常用參數和限制

```text
--manifest     多文件設定清單（必要）
--output       JSON 輸出檔案（必要）
--chunk-chars  每段字數上限，預設 1000
```

預設只接受 HTTPS 的 `ykvs.ntpc.edu.tw` 官方網址。若校方核准的文件由其他官方網域提供，經教師確認來源後才加 `--allow-non-school-source`。`last_verified_date` 必須填成 `YYYY-MM-DD`，不能留下範例文字。

## 查詢測試建議

- 「訓育組清寒助學金的申請資格和期限是什麼？請附校方來源。」
- 「員生社安心就學助學金和清寒助學金各自的申請條件是什麼？」
- 「學生學習評量補充規定中，定期評量成績如何計算？」
- 「學生抵免學分要符合什麼條件、何時申請？」
- 再測不同問法、來源連結能否開啟，以及資料未記載的問題。找不到依據時應回覆資料未提供，不自行補條文。

## 資料維護原則

只納入鶯歌工商官方公開或校方核准文件；原始 PDF 不刪除。每份文件記錄處室、維護單位、版本日期、官方來源、最後檢核日和更新責任單位。PDF 抽取文字不是校方正式解釋，需由負責處室確認內容與現行效力後才供正式使用。

## 本版驗證紀錄

以目前專案已有的四份生輔組 PDF（行動載具、班級秩序競賽、學生獎懲、學生請假）實際轉換，產生 4 份文件索引、204 個頁碼段落；檢查必填欄位和官方 HTTPS 來源完整，並確認 MCP 可依 metadata／關鍵字取回段落及來源連結。這是程式與索引流程測試，不代表新列的四份文件已完成下載或條文校對。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract school-published policy PDFs into searchable, provenance-preserving JSON.

This utility extracts and chunks text only. It does not interpret eligibility,
amounts, deadlines, penalties, or determine whether a document is still in force.
Every output record is marked for human review and retains its PDF page and URL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit("缺少 pdfplumber。請在 Colab 執行：!pip install pdfplumber") from exc

SCHEMA_VERSION = "ykvs-regulations-1.0"
HEADING_RE = re.compile(
    r"^(?:第[一二三四五六七八九十百零〇\d]+[章節條款])|"
    r"^(?:[一二三四五六七八九十]+[、.．])|"
    r"^(?:[（(][一二三四五六七八九十\d]+[）)])|"
    r"^(?:[0-9]+[.、])"
)


def compact_spaces(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\x00", "")
    lines = [re.sub(r"[ \t\u3000]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line:
            out.append(line)
        elif out and out[-1] != "":
            out.append("")
    return "\n".join(out).strip()


def split_long(text: str, limit: int) -> list[str]:
    """Split at sentence/list boundaries where possible; never discard source text."""
    if len(text) <= limit:
        return [text] if text else []
    pieces: list[str] = []
    rest = text
    boundaries = "。！？；\n"
    while len(rest) > limit:
        cut = max(rest.rfind(mark, 0, limit + 1) for mark in boundaries)
        if cut < max(120, limit // 3):
            cut = limit
        else:
            cut += 1
        piece = rest[:cut].strip()
        if piece:
            pieces.append(piece)
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def chunk_page(text: str, limit: int) -> list[tuple[str, str]]:
    """Return (heading, text) chunks confined to one PDF page."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|(?<=。)\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    result: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []
    size = 0

    def flush() -> None:
        nonlocal buffer, size
        if buffer:
            result.append((heading, "\n".join(buffer).strip()))
            buffer, size = [], 0

    for paragraph in paragraphs:
        if HEADING_RE.match(paragraph):
            flush()
            heading = paragraph[:100]
        for piece in split_long(paragraph, limit):
            if buffer and size + len(piece) + 1 > limit:
                flush()
            buffer.append(piece)
            size += len(piece) + 1
    flush()
    return result


def require_official_url(value: str, allow_non_school: bool = False) -> str:
    value = str(value or "").replace("\\&", "&").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"來源網址須使用完整 HTTPS 網址：{value!r}")
    host = parsed.hostname or ""
    if not allow_non_school and not (host == "ykvs.ntpc.edu.tw" or host.endswith(".ykvs.ntpc.edu.tw")):
        raise ValueError(f"來源網址非鶯歌工商官方網域：{host}")
    return value


def build_document(entry: dict, base_dir: Path, chunk_chars: int, allow_non_school: bool) -> tuple[dict, list[dict]]:
    required = ("file", "department", "unit", "category", "title", "last_verified_date")
    missing = [key for key in required if not str(entry.get(key, "")).strip()]
    if not str(entry.get("source_url", entry.get("official_url", ""))).strip():
        missing.append("source_url")
    if missing:
        raise ValueError(f"文件設定缺少欄位：{', '.join(missing)}")
    verified_date = str(entry["last_verified_date"]).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified_date):
        raise ValueError("last_verified_date 必須填實際校對日期，格式 YYYY-MM-DD；不可保留範例文字。")

    pdf_path = (base_dir / entry["file"]).resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"找不到 PDF：{pdf_path}")
    official_url = require_official_url(entry.get("source_url", entry.get("official_url", "")), allow_non_school)
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    doc_id = str(entry.get("document_id") or f"ykvs-{digest[:12]}")
    title = str(entry["title"]).strip()
    keywords = list(dict.fromkeys(str(x).strip() for x in entry.get("keywords", []) if str(x).strip()))

    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            pages_text.append(compact_spaces(page.extract_text() or ""))
    useful_chars = sum(len(text) for text in pages_text)
    if useful_chars < 40:
        raise ValueError(f"PDF 幾乎沒有可抽取文字（{useful_chars} 字元），可能是掃描影像；須先 OCR 並人工校對。")

    doc_info = {
        "document_id": doc_id,
        "department": str(entry["department"]).strip(),
        "unit": str(entry["unit"]).strip(),
        "category": str(entry["category"]).strip(),
        "title": title,
        "publication_date": str(entry.get("publication_date", "")).strip(),
        "version": str(entry.get("version", "")).strip(),
        "source_url": official_url,
        "source_pdf": pdf_path.name,
        "page_count": page_count,
        "sha256": digest,
        "keywords": keywords,
        "owner": str(entry.get("owner", entry["unit"])).strip(),
        "last_verified_date": verified_date,
        "extracted_character_count": useful_chars,
    }
    records: list[dict] = []
    serial = 0
    for page_num, page_text in enumerate(pages_text, start=1):
        for heading, content in chunk_page(page_text, chunk_chars):
            serial += 1
            rid = f"{doc_id}-p{page_num:03d}-c{serial:03d}"
            records.append({
                "data_id": rid,
                "document_id": doc_id,
                "category": doc_info["category"],
                "department": doc_info["department"],
                "unit": doc_info["unit"],
                "title": title,
                "section_heading": heading,
                "content": content,
                "keywords": keywords,
                "publication_date": doc_info["publication_date"],
                "version": doc_info["version"],
                "source_url": official_url,
                "source_pdf": pdf_path.name,
                "page_start": page_num,
                "page_end": page_num,
                "last_verified_date": doc_info["last_verified_date"],
                "owner": doc_info["owner"],
                "review_status": "待人工抽核",
                "sha256": digest,
            })
    return doc_info, records


def convert(manifest_path: Path, output_path: Path, chunk_chars: int = 1000, allow_non_school: bool = False) -> dict:
    manifest_path = manifest_path.resolve()
    config = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = config.get("documents") if isinstance(config, dict) else config
    if not isinstance(entries, list) or not entries:
        raise ValueError("清單需是非空陣列，或包含 documents 陣列的 JSON 物件。")
    documents, records, errors = [], [], []
    for index, entry in enumerate(entries, start=1):
        try:
            doc, doc_records = build_document(entry, manifest_path.parent, chunk_chars, allow_non_school)
            documents.append(doc)
            records.extend(doc_records)
        except Exception as exc:
            errors.append({"index": index, "file": entry.get("file", ""), "error": str(exc)})
    if errors:
        raise ValueError("有文件未完成轉換，未寫出 JSON：\n" + "\n".join(
            f"- 第{x['index']}份 {x['file']}: {x['error']}" for x in errors
        ))
    output = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_scope": "鶯歌工商官方公開或校方核准文件；內容由 PDF 文字抽取，需人工抽核",
        "document_count": len(documents),
        "record_count": len(records),
        "documents": documents,
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="將多份校方規定 PDF 抽取、分段並輸出可供 MCP 檢索的 JSON。")
    parser.add_argument("--manifest", required=True, type=Path, help="文件清單 JSON；PDF 路徑相對於清單檔")
    parser.add_argument("--output", required=True, type=Path, help="輸出 JSON，例如 data/ykvs_mvp_source_pack/data/additional_regulations.json")
    parser.add_argument("--chunk-chars", type=int, default=1000, help="單段字數上限，預設 1000")
    parser.add_argument("--allow-non-school-source", action="store_true", help="允許非 ykvs.ntpc.edu.tw 的 HTTPS 來源")
    args = parser.parse_args()
    if args.chunk_chars < 200:
        parser.error("--chunk-chars 不可小於 200")
    try:
        output = convert(args.manifest, args.output, args.chunk_chars, args.allow_non_school_source)
    except Exception as exc:
        print(f"轉換失敗：{exc}", file=sys.stderr)
        return 2
    print(f"轉換完成：{output['document_count']} 份文件，{output['record_count']} 個段落")
    print(f"輸出：{args.output.resolve()}")
    print("注意：所有段落標記為「待人工抽核」；完成逐頁核對並更新資料版本後才部署。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

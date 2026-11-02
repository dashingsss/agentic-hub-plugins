"""WorkSwarm native Tool adapter for the independently implemented PDF engine."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from openjiuwen.core.foundation.tool import Tool, ToolCard

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "runtime" / "pdf_review.py"


def error(code, message):
    return {"ok": False, "error": {"code": code, "message": message}}


def candidates():
    explicit = os.environ.get("WORKSWARM_PDF_PYTHON")
    if explicit:
        return [explicit]
    result = []
    if not getattr(sys, "frozen", False) and Path(sys.executable).stem.lower().startswith("python"):
        result.append(sys.executable)
    result.extend(p for p in [shutil.which("python"), shutil.which("python3")] if p)
    return list(dict.fromkeys(result))


def execute(inputs):
    if not isinstance(inputs, dict):
        return error("BAD_INPUT", "输入必须是对象。")
    raw = json.dumps(inputs, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(raw) > 256000:
        return error("INPUT_LIMIT", "输入超过 256 KB。")
    available = candidates()
    if not available:
        return error("PYTHON_MISSING", "未找到 Python 3.10+；请安装 Python 或设置 WORKSWARM_PDF_PYTHON 为 python 可执行文件路径。")
    fallback = None
    for executable in available:
        try:
            probe = subprocess.run([executable, str(BACKEND)], input=b'{"action":"status"}', capture_output=True, timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            state = json.loads(probe.stdout.decode("utf-8"))
            if not state.get("ready"):
                fallback = state
                continue
            completed = subprocess.run([executable, str(BACKEND)], input=raw, capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if completed.returncode or len(completed.stdout) > 2 * 1024 * 1024:
                return error("BACKEND_FAILED", "本机 PDF 运行时未正常返回；请检查 Python 版本与依赖。")
            parsed = json.loads(completed.stdout.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else error("BACKEND_FAILED", "PDF 运行时返回格式不正确。")
        except (FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired):
            continue
    if fallback:
        if inputs.get("action") in {"status", "help"}:
            return fallback
        return error("DEPENDENCIES_MISSING", "找到 Python，但缺少 PDF 依赖。请调用 status 查看缺项，按包内 requirements.txt 安装，或设置 WORKSWARM_PDF_PYTHON。")
    return error("PYTHON_UNAVAILABLE", "无法启动指定的 Python；请检查 WORKSWARM_PDF_PYTHON 和系统 PATH。")


class PdfReviewTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="pdf_review", name="pdf_review",
            description="在明确的工作目录中发现和预览 PDF，搜索文字，生成高亮/便签/印章/表单/签名图修改计划，收到用户确认后应用并另存副本。原生文件操作，不依赖 MCP 查看器。先 help/status。",
            input_params={"type": "object", "properties": {
                "workspace_dir": {"type": "string", "description": "用户当前工作目录的绝对路径；所有文档、图片、预览和输出均限制在此目录。"},
                "action": {"type": "string", "enum": ["status", "help", "list_pdfs", "open", "preview", "search", "plan", "apply", "save_as"], "description": "修改先 plan，展示候选预览并等用户确认，再 apply；不能直接声称已编辑。"},
                "payload": {"type": "object", "additionalProperties": True, "description": "各操作参数见 help 与包内 Skill；plan/apply/save_as 必须传 expected_revision。"}
            }, "required": ["workspace_dir", "action"], "additionalProperties": False}, parallel_safe=False,
        ))

    async def invoke(self, inputs, **kwargs):
        try:
            return await asyncio.to_thread(execute, inputs)
        except Exception:
            return error("TOOL_FAILED", "PDF 工具未完成操作，请检查输入格式、Python 与工作目录权限。")

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)

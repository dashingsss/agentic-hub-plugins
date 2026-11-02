"""Verify actual DeepAgent load, model-visible tool, Runner call and unload.

No model call, fake host, monkeypatch or MCP shim is used.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tempfile
import openjiuwen

sys.dont_write_bytecode = True
from openjiuwen.core.runner import Runner
from openjiuwen.core.single_agent.schema.agent_card import AgentCard
from openjiuwen.core.sys_operation import SysOperation, SysOperationCard
from openjiuwen.harness.deep_agent import DeepAgent
from openjiuwen.harness.rails import SkillUseRail
from openjiuwen.harness.schema.config import DeepAgentConfig


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


async def verify(payload, report):
    before = hashes(payload)
    manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pdf-host-") as temporary:
        workspace = Path(temporary)
        skills = workspace / "host-skills"
        skills.mkdir()
        card = AgentCard(id="pdf-native-host-check", name="PDF原生工具验证")
        agent = DeepAgent(card).configure(DeepAgentConfig(card=card, language="cn", auto_create_workspace=False, cwd=str(workspace), sys_operation=SysOperation(SysOperationCard(id="pdf-test-files")), enable_tool_resilience_rail=False))
        await agent.register_rail(SkillUseRail(skills_dir=str(skills), skill_mode="all", include_tools=False, enable_cache=False))
        record = await agent.load_plugin(str(payload))
        try:
            infos = await agent.ability_manager.list_tool_info(names=["pdf_review"])
            assert [i.name for i in infos] == ["pdf_review"], infos
            bound = agent.ability_manager.get("pdf_review")
            assert bound.exposure.value == "direct"
            tool = Runner.resource_mgr.get_tool(tool_id=bound.id)
            assert tool is not None
            status = await tool.invoke({"workspace_dir": str(workspace), "action": "status"})
            assert status["ok"] and status["ready"], status
            listing = await tool.invoke({"workspace_dir": str(workspace), "action": "list_pdfs"})
            assert listing["ok"] and listing["files"] == [], listing
            help_result = await tool.invoke({"workspace_dir": str(workspace), "action": "help"})
            assert help_result["ok"] and "确认" in help_result["message"], help_result
        finally:
            await agent.unload_extension(record)
        assert await agent.ability_manager.list_tool_info(names=["pdf_review"]) == []
    assert hashes(payload) == before, "Host load changed payload bytes"
    versions = {}
    for package in ["openjiuwen", "jiuwenswarm"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "editable module; metadata unavailable"
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "payload": str(payload), "version": manifest["version"], "actual_deepagent_loader": True, "sdk_source": str(Path(openjiuwen.__file__).resolve()), "model_visible_tools": ["pdf_review"], "exposure": "direct", "runner_status_ready": True, "empty_workspace_list": True, "chinese_help": True, "unload_verified": True, "payload_unchanged": True, "installed_distribution_metadata": versions, "workswarm_frontend": "not tested; user testing still required", "model_calls": 0}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(verify(args.payload.resolve(), args.report.resolve()))

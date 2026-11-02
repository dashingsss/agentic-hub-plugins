# 交接：PDF阅览与批注助手（AH-20261030-pdf-viewer）

更新时间 2026-10-30（Asia/Singapore）。当前阶段 **Build 完成，等用户测试**。未推送、未开 PR、未提交 Hub、未记录任何验收。

## 一句话状态

中文原生移植包已构建并通过 29 项本地功能检查，本地测试 ZIP 已生成（`manifest.json` 在归档根）。用户尚未在 WorkSwarm 中测试；交互批注能力是否可用取决于宿主是否渲染 MCP App 查看器。

## 身份与链接

| 项 | 值 |
| --- | --- |
| 候选 | `CAND-CLD-022`（Plugin Candidates，物理行 107） |
| 任务 | `AH-20261030-pdf-viewer`（Development Tasks，行 57） |
| 负责人 | Nguyen Trung Dung |
| 上游 | `anthropics/knowledge-work-plugins`，提交 `2574e29377c7173d0cecffef29a6ecbd7f8ccb5d`，目录 `pdf-viewer`，声明版本 0.2.0 |
| 命名映射 | PDF Viewer → PDF阅览与批注助手 → `pdf-viewer` |
| 稳定内部 ID | `repo:agent-plugin:pdf-viewer` |
| 本地分支 / 提交 | `feat/pdf-viewer` / `40c8673`（在克隆 `C:\Users\ASUS\agentic-hub-plugins-pdf-viewer`，浅克隆 depth 1，main = `400e1e7`） |
| 重复检查 | `Duplicate Check = Partial Overlap - Extend Existing Capability`，主要重叠对象 办公文档能力包 `58423394089843bcb863654f02ab937a@1.0.3` |

## 交付物

| 用途 | 路径 | SHA-256 | 大小 |
| --- | --- | --- | --- |
| 用户导入 WorkSwarm 的本地测试包 | `plugins/pdf-viewer/test-packages/pdf-viewer-1.0.0-native.zip` | `16b432a3e04344b41e269bc40105fd119aa6411f0834a82c362f955ea4befa39` | 40,572 B |
| 市场发布包（Submit 归档，**不能**用于 UI 导入） | `releases/agent-plugin/pdf-viewer/1.0.0/pdf-viewer-1.0.0.zip` | `7c36ab0252af7856c4abc956199ff98df941edd022a4b14561e0dee1272c3195` | 41,418 B |

本地测试包内容（7 个文件）：`manifest.json`、`README.md`、`THIRD_PARTY_NOTICES.md`、`licenses/claude-knowledge-work-plugins/LICENSE`、`licenses/modelcontextprotocol-ext-apps/LICENSE`、`skills/pdf-viewer/SKILL.md`、`mcps/pdf-viewer/mcp.json`。

## 包的设计要点

- 移植 `mode: ported`；复用上游 Apache-2.0 的 Skill 指令与 `.mcp.json`，中文化并按工作流重排，逐文件修改说明见 `THIRD_PARTY_NOTICES.md`。
- MCP 服务由上游未固定版本改为固定 `@modelcontextprotocol/server-pdf@2.0.4`（stdio、显式 registry、`timeout_s: 180`），实现不重分发，运行时由 `npx` 拉取。
- 依赖：Node.js >= 20，首次启动需联网。包内不附带 `node_modules` 或 Node 运行时。
- 许可见证：Apache-2.0 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`，MCP 项目许可 `0382b0057770ca05e9c350a50aa3b1c1fea84da0bc81d723bf00b9aa841be58a`，均已在 ZIP 内逐一校验。

## 已验证内容

`plugins/pdf-viewer/tests/test_functional.py`（容器内，不进载荷）自建最小单页 PDF，按 `mcp.json` 真实启动服务并完成 stdio JSON-RPC。**源目录与解压后的本地测试包各跑一轮，29/29 通过**：

- `initialize` → `PDF Server 2.0.0`，协议 `2025-06-18`
- `tools/list` → 9 个工具齐全；`list_pdfs`、`interact` 无 `_meta`，其余 7 个绑定 App UI 资源
- `list_pdfs` 返回登记文件；`display_pdf` 返回 `viewUUID` 与 `totalBytes=563`（与文件实际大小一致）
- 无查看器时 `interact` 8.0–8.1 秒后返回 `Viewer never connected`，`isError=true`，进程未崩溃
- 不支持的 `interact` 动作在入参校验阶段被拒（`Input validation error ... Invalid option`）
- 格式检查：`asset_release.py check` 通过；`pack` 通过；包内许可哈希与 `provenance.json` 一致；载荷无缓存/依赖/隐藏文件

复现命令（需要 PyYAML，仓库 `requirements-dev.txt`）：

```bash
PY=<带 PyYAML 的 python>
$PY tools/asset_release.py check plugins/pdf-viewer
python plugins/pdf-viewer/tests/test_functional.py
python plugins/pdf-viewer/tests/build_native_package.py   # 生成+校验+解压副本重跑
```

## 关键限制（决定用户测试成败）

上游核心是 MCP App 交互查看器。所有 `interact` 动作经内存命令队列交给查看器轮询；宿主不渲染该 UI 时，任何批注/表单/签名/另存都会在约 8 秒后失败。此时仅 `list_pdfs` 与 `display_pdf` 元数据可用。

该限制已写入包内 `README.md`、`manifest.scope`、`SKILL.md` 的错误处理段，并对用户明示，未包装成"可用"。

另记录一个上游 Windows 缺陷（未修改上游）：`display_pdf` 传 `file:///C:/...` 会拼成 `C:\C:\Users\...` 并报 `Local file not in allowed list`；传 `C:/Users/...` 普通路径或 `list_pdfs` 返回值正常。Skill 已示范正确写法。

## 用户测试步骤（交给用户执行）

1. 导入 `pdf-viewer-1.0.0-native.zip`，确认卡片显示 `PDF阅览与批注助手` / 1.0.0。
2. "打开工作目录里的 sample.pdf，先只做只读检查" → 应看到 `list_pdfs` + `display_pdf` 结果，无批注。
3. 请求高亮或盖章 → 决定性一步：要么出现查看器，要么 `Viewer never connected`。
4. 若查看器出现，再用一次性 PDF 试一个表单字段和一张签名图。

测试完成后需要用户提供：当前版本的原始截图（覆盖工具调用与结果）、明确的测试完成/通过确认。两者齐备后才可进入 Submit 阶段。

## 跟踪表同步状态

已写入并 CSV 回读确认：

- 候选 `CAND-CLD-022`：`Owner = Nguyen Trung Dung`、`Candidate Status = Planned`、`Duplicate Check = Partial Overlap - Extend Existing Capability`、`Linked Development Task IDs = AH-20261030-pdf-viewer`、`Notes`（选择日期/范围/命名映射）、`Related Assets and Differences`（1,291 字符比对结论）
- 任务行 57：`Task ID`、`Task Name = [CAND-CLD-022] PDF Viewer WorkSwarm Native Port`、`Component Type = Plugin`、`Change Type = New Asset`、`Owner`、`Status = Ready for Testing`、`Final Plugin Name = PDF阅览与批注助手`

**未同步（两项）**：候选 `Notes` 的 Build 记录行、`Progress Reports` 新行。原因：这两处长文本写入在界面显示但未提交，多次重试仍未落盘。精确待写入值见 `tracking/pending/AH-20261030-pdf-viewer.md`（该目录被 gitignore，仅本地）。恢复可用写入路径（已授权 Sheets 连接器或人工粘贴）后按该文件逐项写入并回读。

## 下一步与待决策

1. 等用户测试结果。
2. 若查看器可用 → 收集截图与完成确认 → 进入 Phase 3 Submit（推分支、开 PR、附原始截图、过 CI、合并、清理分支、同步记录）。
3. 若查看器不可用 → 二选一，需用户决定：
   - 按 AGENTS 的"宿主不适配"归类：取消任务行、候选置 `Excluded / Unassigned`，并在 Notes 记录原因；
   - 或授权转为 `mode: native` 的独立实现（用本地 PDF 库实现批注/表单/签名，不依赖 App UI），届时是新范围，需要 `NATIVE_DESIGN.md` 与新版本。
4. 无论哪条路径，都不由贡献者执行 Hub 提交；Hub 证据属 Song Haoran。

## 不要做的事

- 不要把市场发布包当测试包交给用户（会报 `missing manifest.json`）。
- 不要在未收到当前版本测试确认与原始截图前推送或开 PR。
- 不要绕过 `interact` 的查看器依赖去声称交互功能可用。
- 不要重写已确认的 `M107` 比对单元格（已落盘）。

# PDF阅览与批注助手 1.0.0 功能测试报告

任务 `AH-20261030-pdf-viewer`，候选 `CAND-CLD-022`，负责人 Nguyen Trung Dung。测试日期 2026-10-30（Asia/Singapore）。

## 测试环境

- Windows 11（MSYS bash 宿主），Python 3.14.9（构建测试用虚拟环境仅安装 PyYAML 6.0.3）。
- Node.js v20.20.0，npm 10.8.2（`C:\nvm4w\nodejs\npx.cmd`）。
- 运行时服务：`@modelcontextprotocol/server-pdf@2.0.4`，由 `npx` 从 registry.npmjs.org 拉取。
- 未使用任何账号、API key 或远程模型调用。

## 测试方法

测试脚本：`tests/test_functional.py`（容器内，不进入载荷）。脚本自行生成一份结构合法的最小单页 PDF（563 字节），按包内 `mcps/pdf-viewer/mcp.json` 的 `command`/`args` 启动真实 MCP 服务，并通过 stdio 完成 JSON-RPC 握手与工具调用。

运行命令：

```bash
python tests/test_functional.py
```

## 结果：29 项全部通过（源目录）

静态检查（18 项）：

| 检查 | 结果 |
| --- | --- |
| `mcp.json` 只声明一个服务，服务名 `pdf-viewer` | 通过 |
| 启动命令为 `npx` | 通过 |
| 服务版本固定为 `@modelcontextprotocol/server-pdf@2.0.4` | 通过 |
| 传输为 `--stdio` | 通过 |
| `timeout_s` 已设置（180） | 通过 |
| `manifest.package_type=plugin`、`id=pdf-viewer` | 通过 |
| manifest 声明 Skill 与 MCP 配置 | 通过 |
| manifest 中文展示名 `PDF阅览与批注助手` | 通过 |
| `SKILL.md` frontmatter `name` 与目录一致 | 通过 |
| `SKILL.md` 为中文，且记录 `Viewer never connected` 情形 | 通过 |
| `SKILL.md` 保留"不构成法律效力数字签名"的限制 | 通过 |
| 载荷含 `README.md`、`THIRD_PARTY_NOTICES.md`、Apache-2.0 全文 | 通过 |
| 载荷不含 `node_modules` | 通过 |

协议检查（11 项）：

| 检查 | 实测 |
| --- | --- |
| `initialize` | 通过，`serverInfo={"name":"PDF Server","version":"2.0.0"}`，协议 `2025-06-18` |
| `tools/list` | 通过，9 个工具全部存在：`list_pdfs`、`read_pdf_bytes`、`display_pdf`、`interact`、`submit_page_data`、`submit_save_data`、`submit_viewer_state`、`poll_pdf_commands`、`save_pdf` |
| `list_pdfs` 是无 `_meta` 的普通工具 | 通过 |
| `list_pdfs` 返回登记过的本地文件 | 通过，返回 `file://C%3A%5CWINDOWS%5CTEMP%5Cpdf-viewer-test-...%5Csample.pdf` |
| `display_pdf` 传入普通路径 | 通过，返回 `viewUUID` 与 `totalBytes=563`（与实际文件大小一致） |
| `list_pdfs` 容忍多余参数 | 通过 |
| 无查看器时 `interact`（`get_text`） | 通过，8.0–8.1 秒后返回 `Viewer never connected for viewUUID ...`，`isError=true`，进程未崩溃 |
| 不支持的 `interact` 动作 | 通过，入参校验阶段返回 `Input validation error: ... action: Invalid option` |
| 服务端 stderr 诊断 | 通过，输出 `[pdf-server] Registered local file`、`Ready`、`[interact] ... failed after 8042ms` |

## 实际失败情形与处理

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `interact` 全部动作在约 8 秒后失败 | 宿主未挂载 MCP App 查看器，命令队列无人轮询 | 在 Skill 错误处理段明确说明这是宿主能力限制，只保留只读元数据能力；不重试同一 `viewUUID` |
| `display_pdf` 传 `file:///C:/...` 报 `Local file not in allowed list: C:\C:\Users\...` | 上游 Windows 路径解析缺陷 | 包内文档与 Skill 示范使用普通路径或 `list_pdfs` 返回值 |
| 首轮 `SKILL.md` 写的是 `Unknown action` | 与真实报错不一致 | 已按实测改为 `Input validation error: ... Invalid option`，并重跑测试 |
| 测试脚本直接以 `npx` 启动在 Windows 失败（WinError 2） | `CreateProcess` 不能执行 shell 包装脚本 | 测试侧解析为 `npx.cmd`；包内 `mcp.json` 保持 `npx`，与宿主启动器行为一致 |

## 未覆盖（不声称通过）

- WorkSwarm 实际导入、插件卡片渲染、中文界面显示。
- MCP App 查看器在 WorkSwarm 中的渲染与 `interact` 全链路（批注、表单、签名、另存）——需要宿主支持 App UI，属用户实测范围。
- 远程 HTTPS 来源（arXiv 等）未在离线测试中验证。
- 仅测单页最小 PDF；未测大型文档分块读取的边界。

## 最终 ZIP 复核

两个包都由同一次源目录测试产出，且都从解压副本重跑过。

### WorkSwarm 本地测试包（交给用户导入 UI）

- 路径：`plugins/pdf-viewer/test-packages/pdf-viewer-1.0.0-native.zip`
- SHA-256：`16b432a3e04344b41e269bc40105fd119aa6411f0834a82c362f955ea4befa39`，40,572 字节
- 结构：`manifest.json` 位于归档根，另有 `README.md`、`THIRD_PARTY_NOTICES.md`、`licenses/`、`skills/pdf-viewer/SKILL.md`、`mcps/pdf-viewer/mcp.json`，共 7 个文件；不含 `plugin.yaml`、测试、缓存或 `node_modules`。
- 包内许可哈希：Apache-2.0 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`、MCP 项目许可 `0382b0057770ca05e9c350a50aa3b1c1fea84da0bc81d723bf00b9aa841be58a`，均与 `provenance.json` 记录一致。
- 解压副本重跑：29 项全部通过（以 `PDF_VIEWER_PAYLOAD` 指向解压目录执行同一脚本）。

### 市场发布包（Submit 阶段归档用，不能用于 UI 导入）

- 路径：`releases/agent-plugin/pdf-viewer/1.0.0/pdf-viewer-1.0.0.zip`
- 结构：外层 `pdf-viewer/plugin.yaml`，内层 `pdf-viewer/pdf-viewer/` 载荷，与上表 7 个文件逐字节一致（`artifact.json` 记录逐文件 SHA-256）。

### 两端一致性

市场包内层载荷与本地测试包为同一组源文件，7 个文件哈希一致；差异只在归档外层结构与是否包含 `plugin.yaml`。

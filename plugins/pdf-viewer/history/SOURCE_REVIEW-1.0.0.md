# PDF Viewer 来源、许可与范围复核

复核日期：2026-10-30（Asia/Singapore）。候选 `CAND-CLD-022`，任务 `AH-20261030-pdf-viewer`，负责人 Nguyen Trung Dung（成员表确认）。用户在当前对话中明确选择该候选并要求开始移植，候选已登记为 `Planned` 并链接任务；本文件只记录复核结论，不代表提交。

## 命名映射

上游 `PDF Viewer` 0.2.0 → 中文展示名 `PDF阅览与批注助手` → 内部 slug `pdf-viewer`。候选 ID、任务 ID 与上游研究名保持不变。

## 功能比对

- 主要重叠对象：办公文档能力包 `58423394089843bcb863654f02ab937a@1.0.3`（Publisher Swenling，Official Category Office and Productivity）。其公开描述覆盖 PDF/Word/Excel/PPT 的解析、转换、批量处理、编辑、比较与脱敏，属于**成批、可脚本化**的文档处理。本候选的输入是单个文档，动作是"在查看器中逐批标注并由人确认"，输出是带标注、可另存的可视副本。
- 结论：`Partial Overlap - Extend Existing Capability`。重叠在"操作 PDF"这一层；本包新增的是交互式可视审阅闭环（查看器、逐批确认、截图核对、签名图放置），这些能力不在办公文档能力包的公开描述内。办公文档能力包的内部实现未逐一检查，因此不主张完全无重叠。
- 其他参照：PDF 正文与表格提取 `0cc89834d061425a87a9a12172998bb6@1.0.0` 面向文本/表格抽取；PDF 指定页文字修改 `185a0bec86fa44f5b0ffeb0637db0865@1.0.0` 面向替换文字；`1f53f98b3e4348d69a42b25b6c6ce459` Peer Review 会在 PDF 上加便签与高亮，但其触发与产出是学术审稿，不提供通用查看器与表单/签名流程。均不构成完整覆盖。
- 已核对：当前 51 条开发任务、以及本轮登记后的任务表，无其他 PDF 查看器类在研任务。

## 材料与许可

| 上游 | 固定引用 | 许可 | 复用材料 | 结论 |
| --- | --- | --- | --- | --- |
| anthropics/knowledge-work-plugins `pdf-viewer` 目录 | 提交 `2574e29377c7173d0cecffef29a6ecbd7f8ccb5d`，目录内 manifest 声明 0.2.0 | Apache-2.0（目录内 `LICENSE`，11,358 字节，SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`） | `skills/view-pdf/SKILL.md`、`.mcp.json` | 许可明确，`mode: ported`；已按第 4(b) 条在中文化改写处记录修改；完整许可逐字节入包 |
| modelcontextprotocol/ext-apps `examples/pdf-server`（npm `@modelcontextprotocol/server-pdf@2.0.4`） | `gitHead` `7af9a75da720b8a81be0f9aff47b25f75e9530ad` | `package.json` 声明 MIT；仓库 `LICENSE` 含 MIT→Apache-2.0 过渡说明 | 不复制实现，只作为运行时服务由 `npx` 拉取 | 不重分发，故无衍生义务；许可文本仍入包备查 |

- 该 `pdf-viewer` 目录在本修订下没有根 `NOTICE` 或子目录 NOTICE，因此不附 NOTICE，也未虚构署名内容。
- 未复用：上游 `.claude-plugin/` 清单、`commands/*.md`、`CONNECTORS.md`、图标、截图、演示素材、品牌素材，以及任何账号凭据。
- 许可取舍说明：上游 `.mcp.json` 使用未固定版本的 `npx -y @modelcontextprotocol/server-pdf --stdio`。可复现性要求固定版本，本包固定为 `2.0.4` 并显式指定 registry；此改动记录在 `THIRD_PARTY_NOTICES.md` 的逐文件表中。

## 运行时依赖与分发边界

- 宿主侧要求 Node.js >= 20（`server-pdf@2.0.4` 的 `engines.node`），首次启动需要网络由 `npx` 安装。
- 服务端直接依赖 `zod`、`express`、`cors`、`pdfjs-dist`、`@cantoo/pdf-lib` 与 `@modelcontextprotocol/{node,client,server,express,ext-apps}`。本包**不**附带 `node_modules`，也不附带 Node 运行时；用户机器按各自原始许可获得这些依赖。
- 若将来改为内置依赖，必须重新逐包复核许可并把许可文件纳入包内，本复核结论不覆盖该情形。

## 宿主能力边界（重要）

上游的核心价值是 MCP App 交互查看器。本轮真实协议测试（见 `TEST_REPORT.md`）确认：

- `list_pdfs` 与 `interact` 是不带 `_meta` 的普通工具；`read_pdf_bytes`、`display_pdf`、`save_pdf`、`poll_pdf_commands` 与三个 `submit_*` 绑定 App UI 资源 `ui://pdf-viewer/mcp-app.html`。
- 没有查看器轮询命令队列时，`interact` 在约 8 秒后以 `Viewer never connected` 失败；测试在 8.0–8.1 秒观察到该结果。
- 因此本包在 WorkSwarm 中的可用程度取决于该宿主是否渲染 MCP App UI。本包不声称 WorkSwarm 已支持；这是用户实测的门槛，已写入包内 README、manifest `scope` 与 Skill 的错误处理段。

## 上游缺陷记录（不修改上游，仅在包内文档说明）

- `display_pdf` 传入 `file:///C:/...` 形式时，在 Windows 上会把路径拼成 `C:\C:\Users\...` 并报 `Local file not in allowed list`；传入 `C:/Users/...` 普通路径或 `list_pdfs` 返回的百分号编码形式可正常工作。包内 Skill 因此示范使用普通路径与 `list_pdfs` 结果，并在错误处理段给出对应提示。

## 最终 ZIP 复核

打包后需逐项确认并在 `TEST_REPORT.md` 记录：载荷仅含 `manifest.json`、`README.md`、`THIRD_PARTY_NOTICES.md`、`licenses/`、`skills/`、`mcps/`；无 `node_modules`、测试、缓存或隐藏文件；外层 `plugin.yaml` 与同名内层目录；包内两份许可哈希与 `provenance.json` `license_evidence` 一致；从解压副本重跑功能测试通过。

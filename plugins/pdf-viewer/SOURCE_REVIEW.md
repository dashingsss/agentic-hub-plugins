# PDF阅览与批注助手 1.1.0 来源与范围复核

日期：2026-10-30（Asia/Singapore）。任务 `AH-20261030-pdf-viewer`，候选 `CAND-CLD-022`，负责人 Nguyen Trung Dung。稳定 ID `repo:agent-plugin:pdf-viewer`。

## 本版结论

`mode: native`、`permission_status: original`。用户在当前对话授权实施修复；先写 NATIVE_DESIGN.md，再按需求独立实现 Python Tool、PDF 运行时、中文 Skill、文档和测试。原生实现用于解决宿主集成缺陷，并非因旧版上游禁止复用。

命名保持：PDF Viewer → PDF阅览与批注助手 → pdf-viewer。1.1.0 用页面 PNG 和逐批确认替代实时 MCP App 查看器，不提供实时拖拽 UI。所有文件限制在明确工作目录。旧 MCP 配置已删除；未复制上游服务、Web UI、图标、字体、截图或品牌素材。

## 已见材料与历史

- anthropics/knowledge-work-plugins，`2574e29377c7173d0cecffef29a6ecbd7f8ccb5d`，pdf-viewer 0.2.0：已见历史中文 Skill、MCP 配置和公开功能说明。1.0.0 曾按 Apache-2.0 复用 Skill/配置；1.1.0 从功能要求重新编写。
- modelcontextprotocol/ext-apps，`7af9a75da720b8a81be0f9aff47b25f75e9530ad`，server-pdf 2.0.4：已见公开服务片段以诊断 roots 和查看器依赖，本版未复制其实现。
- 历史许可保持原字节：`licenses/claude-knowledge-work-plugins/LICENSE`（SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30）；`licenses/modelcontextprotocol-ext-apps/LICENSE`（0382b0057770ca05e9c350a50aa3b1c1fea84da0bc81d723bf00b9aa841be58a）。历史上游目录无须保留的 NOTICE，不虚构 NOTICE。
- 1.0.0 来源/测试报告存入 `history/`，旧 ZIP 与发布归档保持不变。历史 29 项通过包含预期失败断言及测试侧登记路径，不能作为批注成功或宿主验收证据。实际 WorkSwarm 测试暴露未登记目录和 `Viewer never connected` 两项阻塞。

## 运行库与分发边界

| 库/版本 | 来源 | 许可与署名证据 | 使用 |
| --- | --- | --- | --- |
| pypdf 6.10.2 | https://pypi.org/project/pypdf/6.10.2/ | BSD-3-Clause；Mathieu Fenniak、Ashish Kulkarni、Steve Witham 等；完整安装许可另附 | 结构、批注、字段、保存 |
| ReportLab 4.4.9 | https://pypi.org/project/reportlab/4.4.9/ | BSD-3-Clause；Copyright 2000–2024 ReportLab Inc.；完整 LICENSE 另附 | 文字/图片与表单外观；STSong-Light 是标准 CID 字体引用，不打包字体程序 |
| Pillow 12.2.0 | https://pypi.org/project/Pillow/12.2.0/ | MIT-CMU；Secret Labs AB、Fredrik Lundh、Jeffrey A. Clark 及贡献者；完整 LICENSE 含第三方说明 | 图片校验、尺寸 |
| pypdfium2 5.10.1 / PDFium | https://pypi.org/project/pypdfium2/5.10.1/ | 包装层 Apache-2.0 / BSD-3-Clause 双许可，参考 BSD 条款；PDFium 及依赖另有条款；安装许可目录全文随附参考 | 渲染与文字边界，未修改库 |

四库通过 requirements.txt 单独安装。ZIP 不分发库代码、二进制、字体或 Python/Node 运行时，不自动安装。复制安装许可只供参考，不替代未来内置实现时的分发审核。全部 36 份随附许可参考（含历史两份）在 provenance.json 的 `license_reference_files` 记录原字节 SHA-256，构包逐一校验。原有权利不被重新许可；原创代码统一许可仍由项目负责人决定。独立实现不自动豁免专利、商标或服务条款。

## 功能重叠与定位

实时回读办公文档能力包 `58423394089843bcb863654f02ab937a@1.0.3`（Swenling，行 219），仍覆盖广义办公解析、转换、编辑、批处理。未逐项检查其内部实现。保留 `Partial Overlap - Extend Existing Capability`；不因换库或去掉 MCP 声称新业务能力。本版聚焦原已选择的单文档可视审阅、候选计划、逐批确认、真实表单/签名图片及原稿保留，可作为通用文档能力的审阅入口。M107 原比对不改，范围变化记录在 Notes/进展报告。

## 归档与验收边界

本地测试 ZIP 的 manifest 位于根目录；市场 ZIP 是仓库规定的双层包装。内层逐字节对比结果见 TEST_REPORT.md。中文说明、错误、帮助、工具声明与许可哈希均核对；载荷不含测试、缓存、隐藏文件或依赖实现。

仅声称实际本地 PDF 测试和真实 SDK 加载结果。WorkSwarm 前端导入、会话调用和原始截图仍需用户对 1.1.0 当前哈希重新确认。保持 Build；不推送、不建 PR、不执行 Hub 提交。

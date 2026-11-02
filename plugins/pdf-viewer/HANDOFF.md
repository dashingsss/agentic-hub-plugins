# 交接：PDF阅览与批注助手 1.1.0 原生修复

更新日期：2026-11-02（Asia/Singapore）。当前阶段 **Submit：当前1.1.0用户完成及原图齐备，本地集成检查通过**。
负责人 Nguyen Trung Dung；任务 `AH-20261030-pdf-viewer`；候选 `CAND-CLD-022`；稳定 ID `repo:agent-plugin:pdf-viewer`。
命名：PDF Viewer → PDF阅览与批注助手 → pdf-viewer。

## 当前目录与修复

- 工作目录：`D:\jiuwen_repos\agentic-hub-plugins-pdf-viewer-repair`。
- 原有分支 `feat/pdf-viewer`，原本地 HEAD `f288e58`；本次继续保留本地 Build，不推送、不创建 PR 或 Hub 提交。
- 1.0.0 旧交接保存在 `history/HANDOFF-1.0.0.md`，旧来源/报告与 ZIP 保留，不视为新版本验收。
- 旧包九工具注册成功，但目录未登记、交互操作依赖未连接的 MCP App 查看器。1.1.0 独立实现一个原生工具 `pdf_review`，不再启动 MCP、Node/npx 或实时拖拽查看器。
- 新流程：明确 workspace_dir → 页面 PNG → plan 候选修改 → 展示并等待用户确认 → apply → save_as 独立副本。支持真实高亮/便签/印章、AcroForm 填写/勾选、模拟签名图片，保留原稿。
- `NATIVE_DESIGN.md`、`SOURCE_REVIEW.md`、provenance 与 36 份许可参考完整；依赖单独安装，未内置实现或二进制。

## 当前精确测试包（两者不可混用）

| 用途 | 路径 | SHA-256 |
| --- | --- | --- |
| WorkSwarm 前端导入，manifest 在根目录 | `plugins/pdf-viewer/test-packages/pdf-viewer-1.1.0-native.zip` | `8930599d09c7f573d7cda772b46f5a5f81156009bc1120d497620140b677411e` |
| 仓库/Hub 双层包装，不能用于 UI 导入 | `releases/agent-plugin/pdf-viewer/1.1.0/pdf-viewer-1.1.0.zip` | `9b8711cb927647b3fcf0743e8ce093480e5a0ddf949bdf8e88387e3dd019cc54` |

原生包 398982 字节；两个包的 43 个运行文件与当前源码全部字节一致。2026-11-02 复核未改动运行文件或 ZIP。
构包脚本现拒绝覆盖不同内容的同版本 ZIP；同内容复核不重写归档。已实际验证新文件确定性、同内容保留及不同内容拒绝。

## 2026-11-02 实际续接验证

- 资产 check 通过；源码真实 PDF **14/14**、原生 ZIP 解压目录 **14/14**，没有跳过。
- 源码与解压目录均通过真实 DeepAgent.load_plugin / SkillUseRail / Runner：`pdf_review` 对主智能体 direct 可见，status ready、空目录发现及中文 help 可调用，卸载无残留，运行文件未被改变。没有模型调用或修改用户宿主。
- 使用现有 SDK checkout `D:/jiuwen_repos/agent-core-latest`，提交 `0ab5913b250d565b35bff3828dae438939cb1acd`；仅原有无关 browser_move/decision/config.py 有本地改动，本次未改动 SDK。
- `D:\Python 3\python.exe` Python3.12.6：pypdf6.10.2、ReportLab4.4.9、Pillow12.2.0、pypdfium2 5.10.1。默认安装元数据 openjiuwen0.1.16；测试显式 PYTHONPATH 选择 SDK checkout 后读到0.1.19，两者不可混称宿主版本。
- 重渲染并实际查看已另存的中文高亮/便签、填写后姓名/邮箱/勾选/签名、中文印章/形状，以及旋转/裁剪候选 PNG；无观察到的乱码或定位错误。不是用户原始截图或前端验收。
- 记录在 `test-packages/resume-verification-20261102.json`；原始日志/图片在忽略目录 `.research/resume-pdf-20261102/`。
- 既有 check-repo 曾因其他资产 CRLF 许可哈希变化失败；本次未重新运行整个仓库检查或修复无关资产，不声称仓库全绿或 CI 已通过。

## 用户现在可以测试

1. 导入上表 **native** ZIP，启用 **PDF阅览与批注助手 1.1.0**，新建会话。旧版不算本版验收。
2. 独立测试工作目录已准备：`D:\jiuwen_repos\agentic-hub-plugins-pdf-viewer-repair\dist\pdf-viewer\1.1.0\manual-workspace`；包含 sample.pdf、带真实字段的 test-form.pdf、test-signature.png。不要覆盖用户原有文件。
3. 先让工具运行 status/list_pdfs/open 并展示真实 PNG。依赖缺失时设置 WorkSwarm 的 `WORKSWARM_PDF_PYTHON` 为本机已有依赖的 `D:\Python 3\python.exe`，再按宿主要求重启；本次未自动修改或重启宿主。
4. 按 `MANUAL_TESTING.md` 的中文提示完成计划→确认→应用→另存，以及真实表单/模拟签名；外部阅读器检查输出。
5. 返回本 **1.1.0 当前哈希** 的明确完成/通过或失败说明和原始截图，覆盖工具调用、PNG 预览、另存及字段/批注结果。

## 跟踪与交付边界

2026-11-02 实时回读原任务和候选，仍由 Nguyen Trung Dung 负责；Task Ready for Testing、Candidate Planned，PR/截图字段为空。旧报告323/324已落盘，不再把旧交接的两项同步问题当作未解决事项。使用稳定 ID 定位，不固定物理行号。
本版尚无用户完成确认或原始测试截图。AGENTS.md 要求这些材料齐备且阻塞解决后才能 push/PR/merge。先维持本地 Build；不把本次自动测试/渲染图算用户验收，不沿用其他插件或1.0.0的确认。
Song Haoran 负责后续 Hub 提交和项目负责人验收；不写入 Asset Ledger。

## 2026-11-02 后续：用户完成与材料齐备

用户已明确回复“Testing is complete and passed”，关联当前1.1.0原生哈希8930599d09c7；13张原始截图已收集核对，详见 USER_TEST_CONFIRMATION.md 和 evidence/1.1.0。先前待用户说明现为历史。已只读核对真实另存注释 PDF/源摘要；截图裁切、unsupported interact 与用户确认的适用范围均保留，不虚构完整结果。运行载荷和两ZIP未改。现在可按 AGENTS 进入 Submit：基于当前 main 集成、真实仓库测试/CI、创建 PR 附原图、核验永久链接后合并清理；此前不声称实际 PR/合并已发生。Song Haoran 仍负责 Hub 与项目负责人验收。

当前交付工作树 D:/jiuwen_repos/agentic-hub-plugins-pdf-viewer-submit-20261102，分支 port/pdf-viewer-20261102，基于 main b3dad00；53资产/63ZIP检查及本资产14实际功能/真实宿主加载通过，13原图已保留。两种1.1.0 ZIP未改。后续创建PR、核验永久图像链接和真实Linux CI后合并；历史1.0.0归档只供诊断，不是本次验收或Hub交付版本。用户原始D:修复目录和ZIP仍保留。

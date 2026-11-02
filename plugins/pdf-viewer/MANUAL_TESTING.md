# WorkSwarm 1.1.0 修复版测试

导入 `test-packages/pdf-viewer-1.1.0-native.zip`，确认 **PDF阅览与批注助手 / 1.1.0**，新建会话并选择插件。不要用 releases 市场包装 ZIP 导入。新版只有一个原生工具 `pdf_review`，使用 PNG 预览与确认，不会弹出旧 MCP 查看器。

先准备 PDF，再搜索。可将 `test-packages/workswarm-test-files/` 的 sample.pdf、test-form.pdf、test-signature.png 复制到当前工作目录。同名文件已存在时使用新的测试子目录，不覆盖原文件。

需要 Python 3.10+ 和 requirements.txt 中的四库。status 报缺项时，用实际解释器执行 `python -m pip install -r <解压插件目录>/requirements.txt`。需要时设置 WORKSWARM_PDF_PYTHON 为该 python.exe 绝对路径并重启 WorkSwarm。本机已有依赖的解释器为 `D:\Python 3\python.exe`；其他机器按实际路径设置。插件不自动联网安装。

## 1. 准备文件（已复制测试文件可跳过）

> 请先用宿主文件生成能力，在当前工作目录创建 sample.pdf：两页，第一页包含“付款期限为收到发票后 30 天。”和“Payment is due within 30 days.”，第二页写“第二页测试”。再创建 test-form.pdf，含真实 AcroForm 文本字段 name、email 和复选框 approved；创建 test-signature.png，绘制明显标为 TEST 的模拟签名。保留并报告路径，暂时不搜索或修改 PDF。不能生成真实表单时请报告，不用普通文字冒充字段。

这一步准备输入，允许不调用插件工具；插件负责预览、修改现有 PDF。

## 2. 工具与只读预览

> 使用 PDF阅览与批注助手 1.1.0。取得当前工作目录绝对路径，用 pdf_review 依次执行 status、list_pdfs、open sample.pdf。展示第一页实际 PNG，报告页数、review_id、revision，先不批注。必须显示真实工具调用；工具缺失或依赖不齐时原样报告，不用其他库冒充通过。

应返回 ready=true、目录 PDF、两页和 revision=0。通过宿主文件查看工具展示 PNG。

## 3. 生成计划并停在确认前

> 在 sample.pdf 第一页高亮“付款期限为收到发票后 30 天。”，空白处加便签“请复核”和印章“仅供测试”。用 pdf_review plan 生成变更和候选 PNG，展示并等待我确认，暂不 apply 或另存。

应有 plan_id、applied=false；当前 revision 仍为 0。

## 4. 确认与另存

> 我确认应用刚才展示的计划。用 pdf_review apply，然后另存为 sample-annotated.pdf。同名文件存在时用新文件名。展示保存结果、校验状态和预览，并确认未覆盖 sample.pdf。

外部阅读器核对真实高亮、便签详情和印章。再让代理改便签、删除印章，重新计划、确认并另存另一副本，检查删除无残留。

## 5. 真实表单与模拟签名

> 用 pdf_review 打开 test-form.pdf，先列出字段并展示预览。name 填“测试用户”，email 填“pdf-test@example.com”，勾选 approved。在签名框内放置 test-signature.png 并保持比例。生成计划与预览，等我确认再应用。

> 我确认应用这个表单与签名计划。另存 test-form-completed.pdf，报告路径与校验结果。用保存文件核对字段值和页面，说明图片签名不属于密码学数字签名。

外部阅读器检查中文姓名、邮箱、勾选和签名图；表单仍可编辑。

完成后请提供当前 1.1.0 的明确通过/未通过说明和覆盖工具调用、预览、另存的原始截图。导入/下载不算测试完成。截图勿含凭据或会话密钥。AGENTS.md 要求本版确认和原始截图齐备、阻塞解决后才允许推送/PR；本轮保持本地 Build。

## 本机已准备的独立测试目录（2026-11-02）

`D:\jiuwen_repos\agentic-hub-plugins-pdf-viewer-repair\dist\pdf-viewer\1.1.0\manual-workspace`

包含 sample.pdf、带真实字段的 test-form.pdf、test-signature.png，可直接把 workspace_dir 设为此路径。输入文件已从随附样例逐字节复制；未覆盖已有文件。

首次提示：

> 使用 PDF阅览与批注助手 1.1.0，workspace_dir 设置为 `D:\jiuwen_repos\agentic-hub-plugins-pdf-viewer-repair\dist\pdf-viewer\1.1.0\manual-workspace`。调用 pdf_review 依次执行 status、list_pdfs、open sample.pdf，展示实际第一页 PNG，报告页数与 revision。先不编辑；工具或依赖不可用时如实报告。

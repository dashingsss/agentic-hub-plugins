# PDF阅览与批注助手 1.1.0 功能测试报告

日期 2026-10-30（Asia/Singapore）。任务 AH-20261030-pdf-viewer；候选 CAND-CLD-022；负责人 Nguyen Trung Dung。阶段：Build，本地实现/验证完成，待用户测试新版。未记录用户通过、原始验收截图、PR、推送或 Hub 提交。

## 修复及历史

1.0.0 在实际 WorkSwarm 会话已启动服务并注册九工具，但本地目录未登记；远程 PDF 返回 viewUUID 后，interact 因无查看器轮询失败。历史报告存于 history/，原 29 项包含预期失败和测试侧注入路径，不代表成功批注。

1.1.0 改为独立原生 `pdf_review` 工具；workspace_dir 明确限制文件边界，Python 库实际编辑并生成 PNG 页面。无 MCP、Node、npx 或 iframe 查看器。预览→计划→用户确认→应用→另存副本，不覆盖原稿。

## 环境与方法

- Windows，Python 3.12.6，pypdf 6.10.2，ReportLab 4.4.9，Pillow 12.2.0，pypdfium2 5.10.1，PyYAML。
- 测试自行生成中文两页 PDF、带真实 AcroForm 的表单、模拟签名 PNG、旋转/裁剪/孤立字段/歧义字段/加密/损坏/合成签署标记 PDF。没有外部模型、账号或网络调用。
- PDFium 渲染检查代替不可用的 Poppler。重开保存后的 PDF 检查内容、字段树、Widget 值、外观和图片资源；再检查真实渲染。
- 原生 Tool 使用实际已安装 OpenJiuwen Tool/ToolCard，不 mock。完整插件加载另使用本地 SDK checkout `D:/jiuwen_repos/agent-core-latest`，提交 0ab5913b250d565b35bff3828dae438939cb1acd；相关 loader/DeepAgent/SkillUseRail 文件无本地修改。设置 PYTHONPATH 选择该 checkout，并未修改/升级用户宿主。安装元数据 openjiuwen 0.1.19 / jiuwenswarm 0.2.3 不代表所选 checkout 的版本。

## 14 项真实功能用例：源目录及解压 ZIP 均通过

| 用例 | 检查 |
| --- | --- |
| discover_open_search_zoom | 中文目录发现、两页打开、中文文字定位、第 2 页缩放 |
| annotations_edit_delete_save_and_original_preserved | 中文高亮、真实便签、印章、修改便签、删除印章无残留、原稿哈希不变 |
| chinese_form_checkbox_signature_reopen | 中文姓名/邮箱、复选框 /Yes、字段树与每个 Widget 值一致、非空外观、真实图片资源、原稿保留 |
| confirmation_and_stale_revision | 未确认不应用，旧 revision 拒绝重复应用 |
| access_bounds_and_no_overwrite | ../ 逃逸、内部目录输入/输出、原稿及已有文件覆盖拒绝 |
| invalid_inputs | 字段缺失、找不到文字、越界、不支持动作、损坏/加密 PDF 明确失败 |
| native_host_tool_and_missing_runtime | 真 Tool 类由 manifest 加载并 invoke，Python -S 缺依赖诊断、指定不存在的解释器失败 |
| orphan_and_ambiguous_forms | 安全恢复孤立控件、真实填写；字段树与无关联同名控件冲突明确拒绝 |
| rotated_and_cropped_pages | 旋转/裁剪后的文字定位和候选高亮预览 |
| signed_pdf_read_only_and_changed_plan | 含合成签署标记的 PDF 拒绝编辑、快照保持原字节；计划 PDF 篡改拒绝应用 |
| duplicate_ids_locking_and_image_mutation | 重复 ID 拒绝、互斥锁阻止交叉写入、后续构建拒绝已变化的图片 |
| empty_workspace | 空工作目录返回真实空列表 |
| shapes_and_chinese_stamp | 矩形、圆、下划线真实注释，中文印章与自由文字保存 |
| workspace_junction_boundary | 真实 Windows junction 外部路径被拒，发现阶段不遍历该联接 |

所有失败断言均用于边界回归；成功编辑/保存由上述实际内容和渲染验证，不把错误响应算作业务功能通过。pypdf 对初始中文外观的字体编码产生警告；工具随后用 ReportLab 生成真实中文 Widget 外观，重开后的值与 PNG 均已检查。

## 真实宿主 SDK 加载

`tests/host_checks.py` 通过 DeepAgent.load_plugin 读取完整 manifest，绑定真实 SkillUseRail、文件操作与 Runner 资源管理器；模型可见一个 direct 工具 pdf_review，实际执行 status（ready=true）、空目录 list_pdfs 和中文 help；卸载后工具移除，载荷字节不变。不调用模型、不 mock loader、不注入 MCP 根。

源目录和最终 ZIP 解压目录均验证通过，最终记录：`test-packages/host-1.1.0.json`。这证明 SDK 加载/调用，不代表用户运行中的 WorkSwarm 前端已验收。系统旧的 site-packages SDK 不含新 load_plugin 接口，首次测试配置因此失败，改为明确选择已有 SDK checkout；没有更改插件规避真实加载。

## 人工图像核对

PDFium 重渲染已另存的 sample-annotated.pdf、test-form-completed.pdf、shapes-and-stamp.pdf；检查中文文字、高亮位置、便签图标、已删除印章、表单值、勾选与签名图区域。旋转/裁剪候选页面也已实际查看，定位正确，无裁切或乱码。图像位于本机 outputs/pdf-viewer-repair-20261030/final-package/visual-qa/；不是用户原始截图或验收证据。

## 当前本地测试包

- `test-packages/pdf-viewer-1.1.0-native.zip`，398,982 字节。
- SHA-256：`8930599d09c7f573d7cda772b46f5a5f81156009bc1120d497620140b677411e`。
- manifest.json 在归档根；一个原生工具，无 mcps；全部 36 份许可参考哈希、声明路径及中文 UTF-8 检查通过。无测试、依赖实现、隐藏文件或缓存进入载荷。
- `test-packages/verification-1.1.0.json` 记录成员/许可及包摘要。市场包路径 `releases/agent-plugin/pdf-viewer/1.1.0/pdf-viewer-1.1.0.zip`，其内层与 native ZIP 的全部文件逐字节一致；包装外层按仓库规范。artifact.json 记录市场包哈希和逐文件哈希。
- 实测两包内层为相同的 43 个文件，市场 ZIP SHA-256 `9b8711cb927647b3fcf0743e8ce093480e5a0ddf949bdf8e88387e3dd019cc54`；逐字节结果另存 `test-packages/payload-match-1.1.0.json`。

## 仓库级检查与记录同步

本资产 check、pack、git diff --check 通过。额外运行 check-repo 时，其他既有资产出现许可哈希不匹配；逐资产诊断共 39 项，均不属于 pdf-viewer。抽查 action-first-mode 的已提交 LICENSE 哈希等于 provenance，工作目录副本为 Git 的 CRLF 转换，导致字节哈希变化；未修改这些无关文件或全局 Git 配置。不能声称整个仓库检查通过。本资产 payload 有 -text 属性，实际归档与源码哈希一致。

云端任务行 57 已设 Ready for Testing，候选保留 Planned/原归属，补齐来源许可状态及 Notes；Progress Reports 行 323 回填历史记录、行 324 记录本次修复。写后逐值回读验证，M107 原比对未改。表格原有格式、日期、下拉与表范围保持；本次仅用 API 格式回读，未做浏览器渲染核对。原交接的两个待同步项已在这些记录中处理，原 C: 目录的 pending 文件属于历史副本。仍未填写用户验收、截图或 PR 字段。

## 复现

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& 'D:\Python 3\python.exe' tools/asset_release.py check plugins/pdf-viewer
& 'D:\Python 3\python.exe' plugins/pdf-viewer/tests/test_functional.py
$env:PDF_REVIEW_HOST_SDK='D:\jiuwen_repos\agent-core-latest'
& 'D:\Python 3\python.exe' plugins/pdf-viewer/tests/build_native_package.py
& 'D:\Python 3\python.exe' tools/asset_release.py pack plugins/pdf-viewer
```

构包程序解压后用 PDF_VIEWER_PAYLOAD 指向解压目录重跑，设置 PDF_REVIEW_HOST_SDK 时再执行真实 SDK 加载。保留测试图像可设置 PDF_REVIEW_TEST_ARTIFACTS。需要依赖已安装，不自动安装。

## 未覆盖与下一步

用户须导入此精确 1.1.0 ZIP，在新 WorkSwarm 会话检验 pdf_review、宿主 PNG 展示及外部阅读器的导出效果，提供明确完成确认和原始截图；步骤见 MANUAL_TESTING.md。尚未测试所有操作系统、所有第三方阅读器、1000 页/50 MiB 极限性能、任意复杂 PDF 控件或真实密码学签名验证。仅保留签署文件原字节并限制编辑，不验证签名有效性；不做 OCR、实时拖拽或密码学签名。

## 2026-11-02 续接复核

在用户指定的 D: 修复目录继续。复核资产 check、源码14/14、原生 ZIP 解压14/14及两者真实 DeepAgent/SkillUseRail/Runner 加载与卸载，全部通过。43个运行文件及两种 ZIP 哈希均未变化。重开并渲染五张图实际核对中文高亮/便签、表单/勾选/签名、印章/形状、旋转与裁剪，未观察到乱码或定位错误。构包脚本增加同版本不覆盖保护（载荷外），实测新建包确定、同内容不重写、不同内容明确拒绝；两个现有ZIP保持原字节。

当前默认解释器安装元数据 openjiuwen0.1.16，显式选择同一 SDK checkout 后测试内元数据为0.1.19；实际模块来源与提交均已记录，不将二者当作用户前端版本。没有修改 SDK、安装软件、重启宿主或调用模型。详见 test-packages/resume-verification-20261102.json，原始日志/图片在忽略目录 .research/resume-pdf-20261102。未重跑整体仓库套件或 CI，不继承全绿结论。

Git 暂存核对时，依赖许可原文含 CRLF 及原有行尾空格；为保持 36 份原许可摘要，不清理这些字节。自有代码/说明使用 CR-at-EOL 识别并排除原样保留的 licenses 目录进行 whitespace 检查；运行载荷、原许可、样例 PDF/PNG、报告与 artifact 摘要均另做实际 Git 索引字节核对。样例 PDF/PNG 标记为 -text，防止 Git 换行转换破坏 PDF 偏移。

过时1.0.0交接已存入 history/HANDOFF-1.0.0.md，HANDOFF.md 更新为当前修复及精确包；独立用户测试目录准备完成，中文说明见 MANUAL_TESTING.md。当前仍 Ready for Testing；尚无本版用户完成确认及原始截图，不推送或创建交付PR。Tracker进展 Report ID RPT-20261102-pdf-viewer-resume-110，实际云端回读后才声称同步成功。

## 2026-11-02 用户完成确认与原始截图

Nguyen Trung Dung 提供13张原始 PNG，并在明确指向1.1.0当前哈希和另存/预览/表单/签名测试的确认问题中回答 **“Testing is complete and passed”**。Report ID RPT-20261102-pdf-viewer-confirmed-110。先前“待用户”描述为当时历史状态，本节更新当前状态，不沿用1.0.0或其他插件验收。

13张原图已逐一查看并无损保存，详见 evidence/1.1.0/evidence.json。可见日期2026-10-30与本次收到/确认日期2026-11-02分别记录。大部分输出正文及页面/表单/签名渲染不在截图范围，不能把 DONE 当成功；interact 是不支持的旧动作，不计成功。独立用户确认、截图实际覆盖及自动验证分别列明，不推断裁切内容。

另只读检查截图中的真实 sample-annotated.pdf 和同一 review 状态：revision2、两页30063字节，真实 /Highlight 与 /Text、便签已改“测试批注：已复核”、stamp-1 已移除，源文件摘要仍匹配。只保存脱敏结构核对记录，不发布用户 PDF 或状态。两种1.1.0 ZIP/43运行文件未变化，详见 USER_TEST_CONFIRMATION.md。完整用户材料已收集，当前转入提交检查；实际 PR/图像链接/CI 在生成并核验后记录。

## 当前 main 提交集成验证（2026-11-02）

完整用户完成确认及13张原始截图收集后，从当前 main b3dad00f5049827288eaedbbc87b4cdbce12583c 创建独立 LF 交付工作树，仅集成本资产/归档和 PDF 范围的 .gitattributes，保留其他贡献者最新内容。check-repo 实际通过 **53资产/63归档**；原先其他资产许可失败来自旧 CRLF checkout，未改无关资产即可解决。这里只更新这项真实结论，不声称历史失败从未发生。

交付工作树再次执行真实 PDF 功能14/14及真实 DeepAgent/SkillUseRail/Runner 发现/direct/status/help/list/卸载，全部通过；43运行文件和两种1.1.0 ZIP与用户确认完全一致。报告元数据刷新不改变ZIP。详情见 test-packages/delivery-verification-20261102.json。未重跑本地完整 Windows 仓库套件；GitHub Linux 全套单测/包检查/Node MCP 集成须实际通过后才合并。

历史1.0.0归档仅留作诊断追溯，已知未通过用户测试，不是本次验收或推荐导入版本；当前交付和负责人后续Hub材料仅用明确确认的1.1.0。原目录/旧分支保存本地历史；最终PR基于当前main的新临时分支，合并后按实际头部和依赖检查清理。

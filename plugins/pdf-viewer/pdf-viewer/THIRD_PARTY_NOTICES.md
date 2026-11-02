# 第三方材料与独立实现说明

## 1.1.0

原生工具、PDF 审阅运行时和本版中文工作流按用户需求独立实现，未复制上游 PDF 服务实现。完整设计与已见材料记录在源码 NATIVE_DESIGN.md / SOURCE_REVIEW.md。

以下库按 requirements.txt 在运行机器单独安装，不随本 ZIP 重分发库源代码、二进制、字体或依赖目录。随附的许可文本用于查阅，不替代安装分发本身携带的完整许可：

| 软件 | 版本 | 用途 | 许可概况 |
| --- | --- | --- | --- |
| pypdf | 6.10.2 | PDF 结构、批注、表单与保存 | BSD-3-Clause |
| ReportLab | 4.4.9 | 页面文字、印章、图片与表单外观 | BSD 许可；安装分发另含字体等材料许可 |
| Pillow | 12.2.0 | 图片校验与尺寸 | MIT-CMU；完整分发许可含相关第三方材料说明 |
| pypdfium2 / PDFium | 5.10.1 | 页面渲染与文字边界 | 包装层 Apache-2.0 / BSD-3-Clause 双许可；PDFium 及其依赖有单独许可，保留安装分发完整许可 |

本插件使用库的公开 API，不修改这些库；不把库许可证用作团队原创代码的统一许可，也不猜测原始著作权归属。若将来内置任何依赖实现或字体，须重新逐项复核分发义务。

## 1.0.0 历史来源

旧版中文 Skill 与 MCP 配置复用了 anthropics/knowledge-work-plugins 的 pdf-viewer 0.2.0，提交 2574e29377c7173d0cecffef29a6ecbd7f8ccb5d，Apache-2.0。旧版服务依赖 modelcontextprotocol/ext-apps 提交 7af9a75da720b8a81be0f9aff47b25f75e9530ad 的 server-pdf 2.0.4。
旧版许可全文继续保留于 licenses/claude-knowledge-work-plugins/LICENSE 和 licenses/modelcontextprotocol-ext-apps/LICENSE，供历史追溯。旧版归档未改变。本版已删除旧 MCP 配置，并从需求重新编写 Skill 和运行时；这些历史许可不表示新版依赖旧查看器或获得相关品牌背书。

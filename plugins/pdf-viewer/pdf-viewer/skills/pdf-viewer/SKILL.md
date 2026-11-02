---
name: pdf-viewer
description: 在明确的本地工作目录内预览 PDF，逐批确认高亮、便签、印章、真实表单和签名图片修改，并另存校验副本。使用原生 pdf_review 工具与页面 PNG，不依赖 MCP App 查看器。
---

# PDF阅览与批注助手

全部 PDF 操作使用原生工具 `pdf_review`。1.1.0 已移除旧版 MCP 服务；不要调用 list_pdfs/display_pdf/interact 等旧 MCP 工具，也不要启动 npx。默认用中文说明操作和结果。

## 工作方式

1. 从宿主当前会话取得实际工作目录绝对路径，作为每次调用的 workspace_dir；不要猜测用户目录。只处理该目录内的 PDF、PNG/JPEG 和输出。
2. action=status，检查 ready。若为 false，报告缺少的 Python 依赖；按 README 安装 requirements.txt 或选择正确解释器后再继续。不要伪造工具调用或改用别的库声称本插件通过。
3. action=list_pdfs 列出该目录 PDF。目录为空时报告为空；创建测试 PDF 由宿主文件生成工具完成。相对路径基于 workspace_dir，不需要任何 MCP allow-list。
4. action=open，payload={"path":"sample.pdf"}。记录 review_id、revision、pages、form_fields、annotations 和 previews。
5. 用宿主文件查看工具读取 previews 中的 PNG，向用户展示实际页面；不能仅凭路径或返回成功声称页面显示正确。
6. 修改使用 action=plan。检查候选预览、展示具体页码/内容/位置与变更清单，等待用户对该计划明确确认。计划尚未应用，不能说“已修改”。
7. 用户确认后 action=apply，传 review_id、plan_id、expected_revision 和 confirmed=true。更新返回的 revision，再核对预览。
8. action=save_as，传当前 revision 与新文件名。必须以工具返回的 verified、path 和 sha256 为准；不覆盖原稿。提醒用户用 PDF 阅读器核对导出副本。

## 参数

工具顶层：`{"workspace_dir":"<当前工作目录绝对路径>","action":"<操作>","payload":{...}}`。help/status 不修改文档。

- list_pdfs：payload={}。
- open：path，相对路径或目录内的绝对路径。
- preview：review_id，pages=[1]，scale=1.25（0.5–3），每次最多 4 页；切换页即实现翻页，不伪称实时导航。
- search：review_id，query，可选 page。返回 page 与 rects；未匹配时保留空结果，不编造位置。仅用于审阅定位，不交付摘要。
- plan：review_id、expected_revision、commands，最多 5 条命令、影响最多 4 页。
- apply：review_id、expected_revision、plan_id、confirmed=true；只在用户确认后调用。
- save_as：review_id、expected_revision、path，例如 outputs/sample-annotated.pdf；返回前已重新打开验证。

## 计划命令

按文字高亮：
```json
{"action":"highlight_text","page":1,"text":"付款期限为收到发票后 30 天。","occurrence":1,"color":[1,0.85,0.1]}
```
occurrence 可用 "all"，每条最多 5 个匹配；扫描页请预览后改用用户确认的 rects，不自动做 OCR。

添加批注：
```json
{"action":"add_annotations","annotations":[
  {"id":"note-1","type":"note","page":1,"x":470,"y":150,"content":"请复核"},
  {"id":"stamp-1","type":"stamp","page":1,"x":370,"y":180,"width":150,"height":40,"content":"DRAFT"},
  {"id":"signature-1","type":"image","page":1,"image_path":"test-signature.png","x":150,"y":615,"width":200}
]}
```
按实际页面尺寸调整位置，不能机械套用示例。坐标单位为 PDF 点，可见页面左上角为原点，Y 向下。image 省略 height 时按原图比例计算；指定区域仍保持原图比例。
类型支持 highlight、underline、strikethrough、note、freetext、rectangle、circle、stamp、image。前三种用 rects=[[x,y,width,height]]；其他用 x/y/width/height。RGB color 三个数值都在 0–1；font_size 为 6–72。

修改与删除本次审阅新增的批注：
```json
{"action":"update_annotations","annotations":[{"id":"note-1","content":"已复核"}]}
```
```json
{"action":"remove_annotations","ids":["stamp-1"]}
```
便签是 PDF 注释，正文在便签详情中；预览页通常显示便签图标，向用户同时展示 content。印章、自由文字与签名图导出为页面内容，要继续调整这些项目，请保留原 review_id。

真实表单填写：
```json
{"action":"fill_form","fields":{"name":"测试用户","email":"pdf-test@example.com","approved":true}}
```
先从 form_fields 的名称、类型、widgets 页码/位置与实际预览确认视觉标签。示例字段名不代表所有文档都有这些字段；不存在就报告。值必须来自用户，不能编造姓名/金额/日期。按钮可用返回的 options；多选项时指定准确选项。不要用 freetext 冒充字段填写。

## 错误处理和边界

- PATH_OUTSIDE_WORKSPACE：请用户将文件放入本会话工作目录；不扩大到整个磁盘、不绕过路径校验。
- DEPENDENCIES_MISSING / PYTHON_MISSING：显示中文缺项与安装说明，不反复重试。
- STALE_REVISION / STALE_PLAN：重新 preview，按新 revision 生成计划并重新确认。
- PLAN_CHANGED / SNAPSHOT_CHANGED / IMAGE_CHANGED：材料发生变化，重新打开或重新计划，不沿用旧确认。
- FIELD_NOT_FOUND / FORM_STRUCTURE：报告实际字段或结构问题，不虚构填写成功。
- SIGNED_PDF / ENCRYPTED_PDF：改用用户提供的未签署/经授权解密的副本。
- OUTPUT_EXISTS：选择新的输出文件名，不覆盖原稿或已有文件。
- 不将图片签名描述为具有密码学或法律认证效力的数字签名。不提供实时查看器、不总结文档、不直接联网获取文件。

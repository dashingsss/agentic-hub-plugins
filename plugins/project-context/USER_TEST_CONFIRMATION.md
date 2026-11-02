# 项目资料导航 1.0.0 用户测试确认

- 用户/负责人：Wang Jie；任务 `AH-20261102-project-context`；候选 `CAND-DSH-196`；内部 ID `repo:agent-plugin:project-context`。
- 命名映射：`PolinniZhong/dsh-knit` → **项目资料导航** → `project-context`。
- 版本：中文 **1.0.0**；截图接收时间 2026-11-02 11:00:51.479 Asia/Singapore。
- 用户确认时间：2026-11-02 **11:01:53.803 Asia/Singapore**（原消息 UTC `2026-11-02T03:01:53.803Z`）。
- 用户原话：“可以，继续按照之前的流程去做吧”。这条回复紧接对当前版本的十三张测试截图及交付步骤的核对，构成本轮测试完成与后续交付授权；不把截图单独视为确认。
- 对话：`01a1627d-e063-7851-a189-e6b662469130`，当前会话，无可公开访问的会话链接。确认归原进度报告 `RPT-20261102-project-context-build`，不新建任务。

## 当前包不变性

| 包 | SHA-256 |
| --- | --- |
| 用户实测原生包 project-context-1.0.0-workswarm.zip | `e61a6702ada95ce8f2869d046675442c5ac42c35679df13d51fdd9e75523d195` |
| 对应规范交付包 project-context-1.0.0.zip | `6e153ee7694cf04ff6cf8dc5969632fde35928842ae391ec4e104a2e255ed669` |

提交前只读核对宿主安装目录 `~/.jiuwenswarm/agent/workspace/plugins/plugin_packages/local/project-context/`：manifest 1.0.0，22 个声明运行文件全部与源码、规范包、原生包及解压副本逐字节一致。没有改动测试后的载荷、名称、版本、wrapper 或 ZIP；只补载荷外的确认、来源审查、测试与交付记录。

## 实际用户结果

1. WorkSwarm 调用当前插件，中文任务检索到六个演示文件。主要资料为 `docs/login-design.md`，有命中行、内容指纹和来源引用关系；不把扫描或片段检索标成全文已读。
2. 用户明确固定登录设计并排除旧版，索引从六个变为五个；固定项与排除项返回实际路径。
3. 仅将独立演示目录中的“七天”改为“五天”。context_status 检测内容变化；旧指纹的 context_read 返回预期拒绝，读取记录的旧指纹和 read_at 保留。重新读取后，新对话显示新的指纹和内容未变化状态。
4. 新对话恢复 `2aec024791bc23566ce7` 的固定、排除与指定行读取记录；路径上跳和隐藏路径均返回明确拒绝，未将它们误计为连接错误。
5. 显式授权只读检索真实上游项目，索引 96 个文件、访问 117 个目录项、文本 2,247,248 字节；主要定位 `src/host/context.js`，命中行 334–358、659–693，支持项包含相应测试和校验脚本。

只读交叉核对现有插件缓存及文件：演示文档内容指纹 `b418f14bfea799c058fe3f0748fb9e6029eb7f7784c0f6dd6dcd8774f9b0b394` 与新读取记录一致，范围 1–8；真实源码 context.js 指纹 `f1b39bc872bb0bbff59544edc645eba39cd5c889ea9364984a23c355df1bf0a8`，读取记录范围 659–693。核对没有创建新演示项目、重置状态、重新执行用户操作或改写文件。

第十二张截图把 visited_count 误述为“文件数”，并用 117−96 推导“21 个文件跳过”。交付记录采用工具字段的准确含义：117 为含目录在内的目录项，96 为进入索引的文件；实际 omissions 分类数量保留为 3、6、2，不作上述文件数推算。这是结果解读的文字更正，未修改插件或原图。

十三张图片均直接保存用户在当前消息提供的 PNG 字节，不裁剪、不缩放、不转换，尺寸、大小、来源位置及 SHA-256 见 evidence.json。已检查可读性和敏感信息；画面中的本地路径属于本次用户明确用于交付的测试上下文，没有密钥或访问令牌。截图不进入运行 ZIP。

原图已在公开 fork 证据帖 https://github.com/dashingsss/agentic-hub-plugins/issues/4 上传，十三张全部下载核验与会话 PNG 的 SHA-256 一致；正式交付 PR 将直接展示同批图片，并把可访问的 PR 证据永久链接填回原任务。首次上传后的附件短暂返回 404，重查同一帖子后已全部可读且字节核验通过，没有重复创建证据帖。

## 确认记录

User test confirmation: Wang Jie confirmed completion of the current Chinese 项目资料导航 (project-context) 1.0.0 WorkSwarm testing and authorized the previous GitHub delivery workflow after review of thirteen current-version screenshots; confirmed by Wang Jie; date/time 2026-11-02 11:01:53.803 Asia/Singapore; Task ID AH-20261102-project-context; version 1.0.0; tested native ZIP SHA-256 e61a6702ada95ce8f2869d046675442c5ac42c35679df13d51fdd9e75523d195; corresponding canonical ZIP SHA-256 6e153ee7694cf04ff6cf8dc5969632fde35928842ae391ec4e104a2e255ed669; known blocking issues: none established for the accepted tested scope; evidence/source: current conversation 01a1627d-e063-7851-a189-e6b662469130, screenshot message 2026-11-02T03:00:51.479Z, confirmation message 2026-11-02T03:01:53.803Z, unchanged installed payload and read-only state verification.

这是当前包的用户测试确认，不是 Project Lead Acceptance。不宣称 Windows/Linux 实机、任意模型、完整 Git 忽略语法、图片/PDF、全部宿主自动监视或任意大小项目均已验证。不上传 Hub，不填写 Hub 截图或完成日期，不更新 Asset Ledger。

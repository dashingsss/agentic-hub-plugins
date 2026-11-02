# 来源、范围和再分发审查

2026-11-02；负责人 Wang Jie；候选 CAND-DSH-196；任务 AH-20261102-project-context；内部 ID `repo:agent-plugin:project-context`。

命名映射：`PolinniZhong/dsh-knit` → **项目资料导航** → `project-context` 1.0.0。

## 入口与登记

已按工作区 Annotate 复盘的 524 行流程及最新 main b3dad00 的完整 AGENTS.md 开始。候选原为 To Evaluate / Unassigned，无关联任务；实施前实际登记 Planned / Wang Jie，并创建 Researching 任务，回读双方 ID/所有者一致后才克隆上游。进度归原报告 RPT-20261102-project-context-build。独立 detached worktree `agentic-hub-plugins-project-context` 不改旧插件目录；本轮不提交、推送、创建 PR 或操作 Hub。

已比较 llm-wiki `9dd57bf573a742e1bf33940899c4e199` 1.0.0、Cue-Omni-Reader `4ec90e5a10e4419a8f97766613b9d57f` 1.0.0、共享记忆 `2619d14f47f94d66980b97a449d75c2a` 1.0.3、原文快照与精简预览 `c5590645f32b43aca302fc4a75254dc4` 1.0.1。增量是任务相关性 → 有证据的阅读顺序 → 固定/排除 → 通过本插件读取后核对变化的闭环，而不是泛化 Wiki、记忆存储、文件转码或另一个 grep。回查实际开发任务及 PR 无同范围认领；Asset Ledger 本轮不变。

## 固定来源与材料覆盖

上游 https://github.com/PolinniZhong/dsh-knit ，0.25.0，提交 `6c8c91a198efbcce1f4fae034e24f0b575f0b034`。保留候选表原 0.24.0 研究快照，不将旧描述冒充本次运行结果。原根 LICENSE 完整 MIT，版权 `Copyright (c) 2026 Polinni`；搜索未发现其他 LICENSE 或 NOTICE。没有执行安装器或 npm scripts。

| 原文件 / 实际使用 | SHA-256 / 分发位置 |
| --- | --- |
| src/host/relevance.js；中文/英文词法、BM25 字段加权排序，原字节复用 | `9dae39cd6d6d5336b887beb9a8c45b027c80969970350e9ebae93aad6259285f`；vendor/dsh-knit/relevance.js |
| src/host/context.js；证据分层和理由，原字节复用 | `f1b39bc872bb0bbff59544edc645eba39cd5c889ea9364984a23c355df1bf0a8`；vendor/dsh-knit/context.js |
| src/host/classification.js；供分层模块引用代码类型常量，原字节复用；目录/产物另由适配器保守过滤 | `bca1a991a1a3804ec4534488028474c72bf8163d1c0f132c1bf456fb09e1b559`；vendor/dsh-knit/classification.js |
| src/host/relations.js；文件引用/import/测试命名关系，原字节复用 | `6b56ad603a0e230224e97d87c3c95ef4eeb7eb745caf3f53b8d24e247db26a9b`；vendor/dsh-knit/relations.js |
| src/host/links.js；相对路径引用解析，原字节复用 | `405d5b54d3d83b34c65361d8678b636f109f45db134ab7b58b7a9668393aa0bb`；vendor/dsh-knit/links.js |
| src/host/passage.js；有原文偏移/行号的命中片段，原字节复用 | `fadd9e875f16d77ab3213d76a44e3d8692a7a2306f400e1dcc10ea622ed6ec4c`；vendor/dsh-knit/passage.js |

以上全部是根 MIT 覆盖的普通 JS；保留原文件头和注释。完整许可放在内层 licenses/dsh-knit/LICENSE，哈希 `8f0d3535cb8e31e61cf6ebf0d9d4f0aa9509659c3ff43d8d77e1f6c5f6972cbb`；原作者及免责声明不替换。原字节核心不改；新增宿主边界、Python 工具接入及中文指令在 runtime/ 与 skills/，修改范围在 THIRD_PARTY_NOTICES.md 声明。不假定统一许可或给整个团队仓库重新许可。

不分发上游 DSH/Cordis 注册器、客户端 UI、图标、媒体、字体、截图、完整 README、原 AGENTS.md 或第三方库。上游核心六文件无外部包导入；最终运行只需 Python/Node 标准库。新的演示文本与代码为明确标注的独立合成材料，没有搬运用户文档或网上文章。实际用户项目内容仅在运行时授权读取，根 MIT 不替代该内容的保密和版权边界。

## 兼容与安全取舍

上游整体 manifest 要求 Node >=22.19，不能据此让用户升级应用或全局 Node。已在 WorkSwarm 现有 Node 22.11.0 直接执行相关核心基线：`node --test test/context.test.mjs test/relations.test.mjs test/label.test.mjs test/eval.test.mjs`，75 项通过；只验证这一子集，不声称整个 DSH 应用已运行或原型 UI 已接入。

适配范围为显式授权目录、中文任务查询、只读分层 Context Pack、命中行/哈希、固定/排除及通过本插件读取后的变化。Python 用目录描述符相对打开和禁止符号链接维护文件边界，Node 只接收已验证文本快照做纯计算；不让 Node 子进程再次自行遍历用户目录。缓存仅写插件私有目录，项目源码不写。支持常见 .gitignore 规则，敏感/隐藏/生成目录另有不可解除的排除。不是安全扫描器，不宣称可以发现任意秘密。

不移植 DSH 宿主侧栏注入、自动会话事件订阅、外部 embedding、跨会话监控、图片/PDF 理解、符号级调用图或自动 Git 操作。所有“已读”只代表通过本插件成功返回过内容，不代表模型理解或宿主其他工具的读取。缓存不构成加密存储，错误/损坏必须保留并报告，不自动重置。

## 交接验证

已实际运行：上游核心 75 项；适配源码在 Python 3.9/3.11 各 37 项；原生解压包 37 项；独立 MCP SDK 源码/解压各 8 次工具调用和重启。真实公开上游项目扫描 96 个可用文件并定位 context.js；跳过项保留。中文默认行为、声明路径、许可和原模块哈希均已核对。完整命令、实际结果和未测边界见 TEST_REPORT.md。

2026-11-02 用户已按 WORKSWARM_TEST_PROMPTS.md 进行本轮宿主测试，提供十三张原始截图并明确授权继续交付。完成记录见 USER_TEST_CONFIRMATION.md，归原报告 RPT-20261102-project-context-build。开工段落中“本轮不提交”的表述为 Build 阶段边界；此次用户确认后进入 GitHub 交付，仍不操作 Hub 或提前登记 Asset Ledger。最新 origin/main c4bf10e 的 AGENTS.md 与开工规则相同；更新基线不改运行载荷。

规范包 `releases/agent-plugin/project-context/1.0.0/project-context-1.0.0.zip`，SHA-256 `6e153ee7694cf04ff6cf8dc5969632fde35928842ae391ec4e104a2e255ed669`。原生测试包 `local-tests/project-context/1.0.0/project-context-1.0.0-workswarm.zip`，SHA-256 `e61a6702ada95ce8f2869d046675442c5ac42c35679df13d51fdd9e75523d195`。源码、规范归档、原生归档和实际解压副本共 22 个载荷文件逐字节相同。完整 MIT 和六个原模块再次通过哈希测试，不存在缺失的分发许可条件；没有把该核对当作法律意见或 Hub 批准。

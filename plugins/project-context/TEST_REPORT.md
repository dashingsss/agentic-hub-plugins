# 项目资料导航 1.0.0 开发测试记录

2026-11-02；负责人 Wang Jie；CAND-DSH-196；AH-20261102-project-context。

## 环境与执行范围

macOS，系统 Python 3.9.6；复用现有隔离测试 Python 3.11.17（只用于开发检查，不修改 Conda base）；WorkSwarm 自带 Node v22.11.0。没有安装或升级运行依赖、全局环境、WorkSwarm 或安全设置。插件运行依赖只包含 Python/Node 标准库。

上游固定 dsh-knit 0.25.0 / `6c8c91a198efbcce1f4fae034e24f0b575f0b034`，已运行 `node --test test/context.test.mjs test/relations.test.mjs test/label.test.mjs test/eval.test.mjs`：75/75 通过。此为相关纯计算核心基线，不是整个 DSH 宿主验收。

## 已实际运行的适配测试

`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 plugins/project-context/tests/test_project_context.py`：37/37 通过。现有 Python 3.11.17 执行同一套：37/37 通过。

覆盖中文任务→主要资料真实定位→来源关系与行号/偏移/指纹；空匹配不填充；固定项独立展示；排除在排序、计数、关系之前生效；指定行读取与预期指纹；保持 mtime 不变仍识别内容变化；重新读取后恢复未变化；删除文件；跨进程状态保留与并发固定不丢记录；忽略/嵌套忽略；隐藏/凭据/构建物/二进制/UTF-8/大小预算；路径上跳、绝对路径、符号/硬链接、符号目录、目录替换；缓存权限/不存正文/损坏保留/状态符号链接拒绝；Node 缺失/过旧/后端超时；参数错误及源文件零修改；协议坏请求、超大请求后继续正常工作；完整 MIT 和六个原字节模块哈希。

独立协议测试：设置 `MCP_SDK_ESM` 指向已有 `upstream/claude-annotate/node_modules/@modelcontextprotocol/sdk/dist/esm`，运行 WorkSwarm Node 执行 `plugins/project-context/tests/sdk_check.mjs plugins/project-context/project-context`，实际使用 manifest 声明的 mcp.json 命令、参数和 cwd。SDK initialize、6 工具发现、8 次工具调用、读写状态后进程重启核对通过。SDK 仅为测试客户端依赖，不进入交付包、不作为运行依赖。这不等同于 WorkSwarm 界面加载和用户验收。

首轮有一个断言将“排除目标不得出现在结构结果”误写成“不得出现在任何其他文件文本”。README 原文本来含旧版文件链接；已将测试改为核对结果项、关系和计数，未清洗或改写用户资料来制造通过。最终 37 项均实际执行通过。

`python tools/asset_release.py check plugins/project-context` 已通过身份、目录、声明路径与许可元数据检查。

## 最终归档与回归

| 包 | SHA-256 |
| --- | --- |
| releases/agent-plugin/project-context/1.0.0/project-context-1.0.0.zip | `6e153ee7694cf04ff6cf8dc5969632fde35928842ae391ec4e104a2e255ed669` |
| 工作区 local-tests/project-context/1.0.0/project-context-1.0.0-workswarm.zip | `e61a6702ada95ce8f2869d046675442c5ac42c35679df13d51fdd9e75523d195` |

先用 `python tools/asset_release.py pack plugins/project-context` 生成规范包，再用 `python plugins/project-context/tests/build_workswarm.py <canonical-zip> <workspace>/local-tests/project-context/1.0.0` 从规范包提取同一载荷生成原生包。22 个实际运行文件逐字节一致；许可证全文、六个原模块哈希均核对通过。运行 ZIP 不含测试报告、交接文档、测试脚本、环境、node_modules 或缓存。

设置 `PROJECT_CONTEXT_PAYLOAD=/Users/dashing/Desktop/huaweisg/local-tests/project-context/1.0.0/extracted/project-context`，用系统 Python 3.9.6 执行同一功能套件：37/37 通过。独立 SDK 对此解压载荷执行实际配置/cwd、6 工具发现、8 次调用及重启：通过。中文 manifest/Skill/README、默认结果及错误、UTF-8 与声明路径已检查；原许可/代码/协议键值保持原文。

真实公开源码检索也实际执行：对已固定的 upstream/dsh-knit 查询 `Context Pack Primary Supporting Related 任务分层`，扫描 96 个可用文件、2,247,248 字节；主要定位 `src/host/context.js`，真实命中行 334–358 / 659–693，支持项包括 `test/context.test.mjs`、`test/context-eval.test.mjs`。报告包含保护、类型及读取/超限跳过项、complete=false，没有把它称为全仓覆盖。此结果来自实际插件算法，不是演示硬编码。未执行上游项目代码或修改源码。

仓库检查 `python tools/asset_release.py check-repo`：53 个源码资产、62 个发布 ZIP 结构通过。仓库 Python 回归 `python -m unittest discover -s tests -v`：580 项，490 通过、90 因现有可选依赖/条件跳过，新插件的 37 项未跳过。最初在受限进程内运行时，其他已有插件的本机 HTTP 服务/Node 查找失败；使用现有 WorkSwarm Node 的进程级 PATH，并允许临时 loopback 测试后，实际重跑通过。没有为此安装缺少的可选依赖、修改其他资产或全局 PATH。未将跳过项算作通过，也未声明运行 GitHub CI 或全部 Node 专项任务。

## 用户阶段边界

Build 交接时尚未进行用户验收；随后 Wang Jie 在 WorkSwarm 完成本轮实际测试，2026-11-02 11:00:51.479 提供十三张截图，11:01:53.803 明确授权按之前流程继续交付。详见 USER_TEST_CONFIRMATION.md。未将开发自测或截图单独当作用户确认；Project Lead Acceptance 仍未完成。

当前包实际宿主流程覆盖中文分层检索与行号/来源、固定与排除、指定行读取、修改后变化检测、旧指纹拒绝、重读后新指纹、新对话状态保留、路径上跳/隐藏路径拒绝及真实上游检索。只读核对宿主安装的 22 个载荷文件与双方 ZIP 全部一致；没有重建或更改测试包。真实项目访问 117 个目录项、索引 96 个文件，不能将差额算作被跳过文件数。

交付前同步至最新 main c4bf10e 后，再跑仓库 Python 回归：580 项，490 通过、90 条件跳过；check-repo：54 个源码资产、64 个 ZIP 结构通过。十三张原始 PNG 已通过本人公开 fork 的证据帖 https://github.com/dashingsss/agentic-hub-plugins/issues/4 上传，并逐张下载核验与当前会话字节 SHA-256 相同。完整清单见 evidence.json；正式 PR 创建时将同批图片直接展示到正文与证据评论，再验证永久链接。

继续执行 GitHub 交付及原任务同步，不上传 Hub，Asset Ledger 不变。原始图片不进入运行 ZIP，不以截图替代来源许可或功能测试。

Windows、DSH UI/钩子、全宿主自动读文件监控、完整 Git 忽略语法、图片/PDF、外部 embedding 均不在适配范围。Linux 没有本次实际机器实测，不能以源码可用推断已经通过。

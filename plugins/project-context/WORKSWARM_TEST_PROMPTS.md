# 项目资料导航 1.0.0：WorkSwarm 测试

负责人 Wang Jie；CAND-DSH-196；任务 AH-20261102-project-context。当前为中文测试包，尚未开始用户验收。

## 导入这份包

原生测试 ZIP：[project-context-1.0.0-workswarm.zip](/Users/dashing/Desktop/huaweisg/local-tests/project-context/1.0.0/project-context-1.0.0-workswarm.zip)

SHA-256：`e61a6702ada95ce8f2869d046675442c5ac42c35679df13d51fdd9e75523d195`

仓库规范包：[project-context-1.0.0.zip](/Users/dashing/Desktop/huaweisg/agentic-hub-plugins-project-context/releases/agent-plugin/project-context/1.0.0/project-context-1.0.0.zip)

SHA-256：`6e153ee7694cf04ff6cf8dc5969632fde35928842ae391ec4e104a2e255ed669`

两包共用同一份 22 文件载荷，逐文件与源码、解压副本一致。规范包包含 plugin.yaml 外层；本次 WorkSwarm 使用上面的 **workswarm.zip**。后续改包不能沿用本次哈希与确认。

在 WorkSwarm **扩展 → 我的扩展 → 导入本地插件** 导入原生 ZIP，再点击「使用」，新建选中 **项目资料导航** 的对话。不要仅把 ZIP 附在聊天框。若已有同 id 插件，先核对版本并使用应用支持的更新/移除入口，不手动覆盖安装目录或注册表。模型选你已经配置、可以正常调用工具并输出中文的即可，无需新账号或独立 API key。

macOS/Linux，Python 3.9+、现有 Node 20+。已在你机器的 Python 3.9.6 与 WorkSwarm Node 22.11.0 验证开发功能，**没有 npm/pip 安装步骤，也不需要 Conda**。Linux 和实际 WorkSwarm 导入属于尚待验证范围。模型连接错误与插件错误分别报告；本机运行不代表聊天内容不经过所选模型。

以下逐条发送，不要一次全部发出。若工具连接、版本或预期失败，保留原始输出并发给我，先停下，不修改插件、应用、注册表或安全设置来绕过。第 3 条故意触发旧指纹拒绝，这是预期的负例。

## 1. 接入与中文资料包

```text
请实际使用当前选中的“项目资料导航”1.0.0，中文回复，不要只模拟。
先调用 context_status()，确认实际版本和工具可用；不匹配或连接失败就报告原始错误并停止。
本轮明确允许调用 context_demo 创建新的独立虚构演示项目。保留它实际返回的 root 和 workspace_id，不要猜编号。
再对这个演示项目调用 context_find，query="登录设计 tokenlogin 离线缓存"。
完整展示工具返回的中文 markdown，并列出主要资料的 sha256、命中行、引用关系、扫描数量、omissions 和 complete。
不要替我固定、排除或读取全文，不要执行项目代码、修改原项目或插件源码，不要提交或发布。完成本轮后结束回复，等我下一步。
```

预期：版本 1.0.0；新演示目录；6 个索引文件；主要资料为 `docs/login-design.md`，片段包含令牌登录和七天离线缓存；路径/行号/哈希来自实际工具；读取状态为尚未通过本插件读取。主要/支持/关联不要求填满。

截图：版本和演示编号、资料包主要项及命中行。哈希可复制文本保存，不要求把长哈希挤进一张图。

## 2. 固定、排除与指定行读取

同一对话发送：

```text
继续使用刚才真实返回的演示 workspace_id。
请调用 context_control，将 docs/login-design.md 固定（pin），并将 docs/login-old.md 排除（exclude）。
再调用 context_find，query="登录设计 tokenlogin 离线缓存"，展示资料包、固定项、排除项和索引文件数量。
核对旧版文件不再作为结果项或关系目标；其他文件原文里的旧链接不必删除或篡改。
随后用本次主要资料真实 sha256 作为 expected_sha256 调用 context_read，path="docs/login-design.md"，start_line=1，max_lines=8。
调用 context_status(workspace_id) 展示读取范围、指纹和变化状态。不要说已理解整个项目，不要修改源文件。完成后等我下一步。
```

预期：固定项独立列出、排除项有旧版路径；索引由 6 变为 5；旧版没有被当作结果目标；指定行确实返回；状态显示本插件读取过且内容未变化。截图：固定/排除、指定行、读取状态。

## 3. 只修改虚构演示文本，验证内容变化

同一对话发送：

```text
本轮仅授权你通过普通文件编辑工具，修改 context_demo 刚才实际返回的独立演示 root 中 docs/login-design.md：把“离线缓存保存七天”改成“离线缓存保存五天”。
先核对这个路径确实在该独立演示目录内；不要修改仓库、下载的上游、插件安装目录或其他项目。若文件编辑工具不可用，说明并停止，不假装修改成功。
保留修改前 context_read 返回的旧 sha256。修改后先调用 context_status，核对显示读取后内容已变化。
再把旧 sha256 作为 expected_sha256 调用 context_read，验证它明确拒绝旧版本；这是本轮预期负例，不代表测试失败。核对拒绝没有更新读取记录。
最后不带 expected_sha256 重新调用 context_read 读取当前文件，再查 context_status，核对内容包含五天、指纹已更新、状态回到内容未变化。
只报告真实工具结果，完成后停止，不继续改动任何文件。
```

预期：先变化 → 旧指纹拒绝且读取记录保留 → 返回五天及新指纹 → 状态未变化。截图：前后状态、旧指纹拒绝和新内容。

## 4. 新对话保留设置，并拒绝越界

新建对话，再选中同一插件。不要重新生成演示项目。发送：

```text
请实际使用“项目资料导航”1.0.0。先调用 context_status() 列出缓存中的真实项目，不要创建或重置项目。
找到上一轮演示 root 对应的 workspace_id；如有多个无法确定，先列出让我指出，不要猜。
对该项目调用 context_status(workspace_id)，核对固定的 docs/login-design.md、排除的 docs/login-old.md、指定行读取记录和新内容指纹是否还在。
然后实际调用 context_read，path="../outside.md"，验证路径上跳被拒绝；再调用 path=".env"，验证隐藏文件不可读取。不要在磁盘创建这些文件。
展示真实返回，区分预期拒绝与连接失败；不要编造旧状态，不要修改源码、安装依赖、提交或发布。
```

预期：设置和读取记录跨对话保留；两个越界/保护负例明确失败；失败不损坏先前状态。截图：新对话状态和拒绝结果。

## 5. 真实项目的使用效果

仍在选中插件的对话发送。此处明确授权读取本次已下载的公开上游源码，**不修改它**：

```text
我授权项目资料导航只读检索 /Users/dashing/Desktop/huaweisg/upstream/dsh-knit。
请调用 context_open 登记它，再调用 context_find，query="Context Pack Primary Supporting Related 任务分层"。
展示中文资料包、实际扫描数量和跳过原因。根据真实命中行回答：分层装配主要在哪个文件，哪些测试或实现值得接着看？
对主要文件使用实际 sha256 调用 context_read 读取命中位置附近最多 40 行，再基于这些实际返回的行说明入口、输入和输出，保留相对路径与行号。
不要直接读取整个仓库代替插件，不要执行上游代码、联网补全、修改项目、提交或发布。无法验证的部分说明未知。
```

开发侧对同一固定源码的实际结果：索引 96 个文件，主要定位 `src/host/context.js`；有超限/类型等跳过项，不能宣称覆盖整个仓库。用户端结果以实际工具为准。截图：真实项目的主要文件、命中行和有依据的回答，这比只截“工具已加载”更能说明实际用途。

## 完成后

把上述主要结果的原始截图发给我，并明确说是否已完成 **项目资料导航 1.0.0 / 原生 ZIP 哈希 e61a6702…523d195** 的测试。成功项、失败项、未执行项分别说明；不要用开发自测代替 WorkSwarm 验收。我会核对当前包、结果和截图，再按 AGENTS.md 完成后续 GitHub 交付及表格同步；不上传到 Hub。

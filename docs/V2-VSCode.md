# Current Jira Intake

Jira Intake uses the selected VS Code extension's existing MCP. Run `jira-intake.py --key KEY --agent codex` or `--agent claude`, attach its prompt, review differences and confirm. No standalone MCP configuration. See V2.1-Adapters.md; any previous independent MCP instructions are retired.

# Harness V2：VS Code 扩展协作入口

本版本优先支持在 VS Code 中使用已登录的 Codex / Claude Code 扩展。扩展负责 AI 规划、开发和审查；Harness 生成阶段提示、执行验证并记录人工确认的审查。脚本不会接管扩展会话，不调用模型 API，也不需要在 Harness 中保存会员密码或 API key。CLI 自动适配器留待后续版本。

## 日常操作

1. 打开项目根目录。用 Jira Intake 生成 plans/<KEY>.json；先补上需求描述。
2. Ctrl+Shift+P → Tasks: Run Task → Harness V2: Planner。输入 ticket key、Python 路径和使用的扩展。
3. 打开终端输出的 planner-prompt.md，作为文件上下文交给 Codex 或 Claude Code 扩展：请执行该提示文件中的 Planner 任务。
4. 检查扩展填写的结构化计划。运行 Harness V2: Coder，按相同方式交给扩展执行；必须在同一个业务项目根目录内工作。
5. 运行 Harness V2: Verify。命令配置来自 .harness/config.json；业务项目必须换成真实业务构建/测试。
6. 如果 blocked，运行 Harness V2: Repair，将包含实际失败证据的提示交给扩展，修复后再次 Verify。每个 ticket 最多生成两次修复交接；用尽后停止自动式交接，人工诊断并修复后可直接重跑 Verify。
7. 验证通过进入 awaiting_review 后，运行 Harness V2: Reviewer。将提示交给选定扩展，要求阅读实际代码与证据，输出 approve/reject 和理由。可让另一个扩展审查，但模型不同不等于独立人工审查。
8. 阅读审查结果和实际 diff（包括未跟踪文件），再运行 Harness V2: Approve reviewed changes；填写真实 reviewer 名称和具体结论。任务表示你已检查 diff 和验收条件。Reject changes 用于记录拒绝。批准任务复用 V1.1 的最新快照校验，文件变化后必须重新 Verify。

新建 .vscode/tasks.json 中的 Python 输入默认 python；如果指向 Store 占位程序，可填 C:\Users\ouyti\anaconda3\python.exe。

## 命令入口

```powershell
python tools/editor-workflow.py --ticket PROJ-123 --stage planner --agent codex
python tools/editor-workflow.py --ticket PROJ-123 --stage coder --agent claude
python tools/run-workflow.py --ticket PROJ-123
python tools/editor-workflow.py --ticket PROJ-123 --stage repair --agent codex
python tools/editor-workflow.py --ticket PROJ-123 --stage reviewer --agent claude
python tools/editor-workflow.py --ticket PROJ-123 --review approve --reviewer "实际审查者" --notes "具体审查结论" --diff-checked --criteria-checked
```

提示和交接历史保存到 .harness/runs/<KEY>/，生成提示不代表该阶段已由 AI 执行。所有验证和审查继续保存到 latest.json 及对应 run_id 文件。

## 版本边界

V2 使用 V1.1 的验证配置格式，保留旧入口。Jira 仍可选，需要实时读取或回写时才提示连接。当前没有自动模型调用、自动 Jira 回写、自动提交/PR 或任务恢复器。AI 扩展的文件权限由扩展本身管理；提示里的约束不是操作系统沙箱。Planner、Coder、Reviewer 由用户在扩展中启动，结果必须通过 Harness 的证据关卡。

V2 的扩展交接不依赖 CLI。将来若采用 Codex CLI 自动执行，可参考 [OpenAI 官方修复循环示例](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex)，需单独检查 CLI 登录及执行权限，不能由“扩展已登录”推断。
# V2.1 extension

The extension handoff workflow in this document remains supported. For actual Jira MCP retrieval,
the extension-only V2.1 workflow, and the new VS Code tasks, see `V2.1-Adapters.md`.
AI CLI adapters have been removed. Submit generated prompts manually to your logged-in extension.

把 Harness V1 当成每个项目根目录下的一套“协作约定 + 脚本入口”即可。它不要求项目使用 Python；Java、Node、.NET、Go 等项目都能加入。

已升级 V1.1：请以 docs/V1.1.md 为当前使用指南。以下 V1 介绍保留为历史参考；结构化 ticket 计划、真实 build/test 命令和显式审查是新的完成条件。

V2 VS Code 扩展协作入口已加入，请阅读 docs/V2-VSCode.md，并从 Tasks: Run Task 选择 Harness V2 任务。V1.1 的验证和审查关卡继续适用。
建议每个项目保留自己的 Harness 配置：
你的项目/
├─ src/…
├─ AGENTS.md
├─ .harness/
│  ├─ rules/
│  ├─ skills/
│  ├─ workflows/
│  └─ memory/
└─ tools/
   ├─ build.ps1
   ├─ test.ps1
   └─ git-status.ps1
接入时分两种情况：
1. 项目没有 AGENTS.md、.harness、tools
   将 Harness V1 的这些文件复制到项目根目录。
2. 项目已有同名文件或目录
   不要覆盖。将现有内容合并：
   - AGENTS.md：保留原项目规则，再追加 Harness 的工作方式。
   - .harness/rules/：保留项目已有约束，补充缺失规则。
   - .harness/memory/：为该项目单独记录状态、决策和踩坑。
   - tools/build.ps1、test.ps1：替换“结构检查”或在其后追加项目真实构建/测试命令。
最关键的适配是让两个脚本调用项目自己的验证命令，例如：
# Node.js 项目 tools/test.ps1
npm test
# Python 项目 tools/test.ps1
python -m pytest
# .NET 项目 tools/test.ps1
dotnet test
# Java Maven 项目 tools/build.ps1
mvn clean package
之后，工作流入口保持一致：
python tools/run-workflow.py --workflow feature
V1 的 Tester 目前验证 Harness 自身文件是否齐全。接入真实项目后，建议将 run-workflow.py 扩展为调用 tools/build.ps1 和 tools/test.ps1，让流程的 Tester gate 以项目实际构建与测试结果为准。
一个实用的约定是：规则与工作流可以跨项目基本复用；STATUS.md、DECISIONS.md、MISTAKES.md 必须按项目独立维护；构建和测试脚本必须按项目技术栈定制。
cd D:\1_opensource\HarnessPractice

# 先根据 Jira ticket 信息创建本地计划；不会连接 Jira
python .\tools\jira-intake.py `
  --key PROJ-123 `
  --type feature `
  --summary "支持导出报告"

# 补齐生成的 plans\proj-123-支持导出报告.md 中的验收条件、范围和测试命令

# 启动 Harness 工作流
python .\tools\run-workflow.py --workflow feature --ticket PROJ-123

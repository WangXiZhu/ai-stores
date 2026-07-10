---
name: haixin-openspec-workflow
description: >-
  Haixin OpenSpec workflow orchestrator. Use when the user asks to推进/恢复/查看
  haixin-openspec feature 状态、判断下一步、处理中断重试、串联 workspace/spec/UI/API/E2E/local proxy/deploy/bugfix skills。
---

# Haixin OpenSpec Workflow

你是 `haixin-openspec` 的研发工作流编排者。你的职责不是替代现有技能写代码，而是基于 feature 目录中的机器状态，判断下一步、检查门禁、处理中断恢复，并把执行结果写回状态文件。

## Scope

默认根目录：`/Users/limo/git/gitee.com/haixin-openspec`

每个 feature 目录应包含：

```text
{feature-id}/
  meta.yaml
  contract.yaml
  prd-source.md
  decisions.md
  x-open-questions.md        # 可选
  test-cases.md              # 可选
  execution-state.yaml       # 工作流运行态
  verification.md            # 验证记录
  release-plan.md            # 发布前计划
  deploy-report.md           # 部署记录
```

## Core Rule

永远先读：

1. `README.md`
2. `{feature-id}/meta.yaml`
3. `{feature-id}/execution-state.yaml`（不存在则从 `_template/execution-state.yaml` 初始化）
4. `{feature-id}/contract.yaml`（若存在）
5. `{feature-id}/x-open-questions.md` 与 `decisions.md`（若存在）

再决定下一步。

## Mandatory Workflow Status Block

每次触发本 skill，无论用户是要求查看状态、继续执行、恢复、重跑还是处理异常，都必须先输出一个固定状态块。状态块必须基于刚读取的 `execution-state.yaml`，不得凭聊天记忆推断。

固定格式：

```markdown
## Workflow Status

- Feature: <feature-id>
- Status: <status>
- Current stage: <current_stage>
- Done: <stage1>, <stage2>
- Needs review: <stage1>, <stage2>
- Failed/blocked: <stage1>: <reason>
- Safe to rerun: <stage1>, <stage2>
- Requires confirmation: <stage1>, <stage2>
- Resume required: <stage1>: <external_task_ids/task_ids>
- Next action: <one concrete next action>
```

规则：

- `Done` 只列 `status: done` 的阶段。
- `Needs review` 列 `needs_review` 的阶段。
- `Failed/blocked` 列 `failed`、`blocked`，并带 `last_error.summary` 或 `next_action`。
- `Safe to rerun` 只列 `rerun_policy.mode: safe` 且 `side_effects.safe_to_rerun: true` 的阶段。
- `Requires confirmation` 列 `rerun_policy.mode: confirm` 或 `side_effects.requires_confirmation: true` 的阶段。
- `Resume required` 列 `status: running` 且 `rerun_policy.mode: resume` 的阶段。
- 如果 `execution-state.yaml` 不存在，先说明缺失，并建议从 `_template/execution-state.yaml` 初始化；不要继续假设状态。

## Mandatory Write-back Rule

每次执行完一个阶段，或阶段失败、中断、等待人工确认时，必须写回运行态。除非用户明确要求“只分析不改文件”，否则不能只口头说明状态。

至少更新：

```yaml
stages:
  <stage>:
    status: done | failed | blocked | needs_review | running | skipped
    attempts: <previous + 1 when an execution was attempted>
    last_run_at: "<YYYY-MM-DD>"
    last_error: null | { summary: "...", command: "...", detail: "..." }
    next_action: "..."
history:
  - at: "<YYYY-MM-DD>"
    stage: "<stage>"
    event: "..."
```

报告写回规则：

- 测试、静态检查、E2E、Smoke 相关结果写入 `verification.md`。
- 发布范围、发布顺序、前置条件、验证清单、回滚方案写入 `release-plan.md`。
- Swan 合并、部署、构建、外部任务 ID 写入 `deploy-report.md`。
- 需求确认、阻断解除、关键口径变化写入 `decisions.md` 或 `x-open-questions.md`。
- release 总结写入 `release.md`。

失败写回规则：

- 命令失败或测试失败时，阶段标为 `failed`，写 `last_error`，并写出可执行的 `next_action`。
- 需要人工确认时，阶段标为 `needs_review` 或 `blocked`，并写入 `blockers[]` 或 `next_action`。
- 异步任务已创建但未完成时，阶段标为 `running`，写入 `async.task_ids` 或 `side_effects.external_task_ids`。
- 对于 `rerun_policy.mode: resume` 的阶段，恢复时不得重新创建外部任务。

## Stage Status

阶段状态只使用下列枚举：

```text
pending       未开始
ready         输入满足，可以执行
running       异步执行中
done          完成
blocked       阻断，需要人处理
failed        执行失败，可分析
stale         输入变化，产物过期
skipped       明确跳过
needs_review 需要人工确认
```

## Rerun Policy

每个阶段必须遵守 `rerun_policy.mode`：

```text
safe      可直接重跑：workspace、静态检查、E2E、报告生成
confirm   重跑前必须询问：contract 覆盖、业务代码实现、本地代理配置覆盖
forbidden 禁止自动重跑：已经创建的外部任务、真实数据写入
resume    恢复已有任务：Swan running task、长轮询任务、已启动异步 job
```

当阶段处于 `running` 且 `rerun_policy.mode: resume` 时，禁止重新创建外部任务；应先根据 `side_effects.external_task_ids` 或 `async.task_ids` 轮询/恢复。

## Side-effect Guardrails

以下动作必须人工确认：

- 修改真实业务代码前
- 覆盖已有 `contract.yaml` / `execution-state.yaml` 关键输出前
- 触发 Swan 合并、部署、发布前
- 重跑 `side_effects.safe_to_rerun: false` 的阶段前
- `x-open-questions` 仍有阻断项时继续实现前
- 测试失败但用户要求继续部署前

## Stage Map

| stage | 主要 skill | 说明 |
| --- | --- | --- |
| project_context | 读 `project.md` | 项目地图、COC/SH 分线、仓库定位 |
| workspace | `coc-workspace-from-changes` | 生成/确认多根 workspace |
| contract | `prd-openspec-contract` | PRD/API/Figma -> OpenSpec 契约 |
| figma | `figma-ui` | 设计稿 DSL 与 UI 实现输入 |
| implementation | 现有代码实现能力 | 按 contract/tasks 改业务代码 |
| local_proxy | `local-api-proxy` | 本地 API 分流与联调 |
| e2e | `playwright-harness-e2e` | Harness + Playwright 回归 |
| stability_review | `frontend-stability` | 静态稳定性审查 |
| release_plan | 本 skill | 生成发布计划：范围、顺序、前置条件、验证清单、回滚方案 |
| deploy | `swan-deploy` | Swan 合并与部署 |
| bugfix | `tapd-bug-fix` | TAPD 缺陷回流修复 |
| release | 本 skill | 汇总交付、验证、部署、风险 |

## Commands / Intents

### status

用户要求“看状态 / 当前进度 / 卡在哪”时：

1. 读取 `execution-state.yaml`
2. 输出 `current_stage`、阻断项、失败项、下一步
3. 若输入文件发生变化但状态未更新，标记建议 `stale`

### next

用户要求“继续 / 下一步 / 推进”时：

1. 先输出 `Workflow Status` 固定状态块
2. 检查 `current_stage`
3. 检查该阶段 `status` 与 `rerun_policy`
4. 若 `blocked/needs_review`，先列出需要用户确认的问题
5. 若 `running/resume`，恢复已有异步任务
6. 若 `ready/pending/safe`，调用对应 skill 或给出明确执行步骤
7. 执行后必须按 `Mandatory Write-back Rule` 更新状态文件和对应报告

### rerun

用户要求“重跑某阶段”时：

1. 先输出 `Workflow Status` 固定状态块
2. 读取阶段 `rerun_policy.mode`
3. `safe` 可直接重跑
4. `confirm` 必须先确认覆盖范围
5. `resume` 先恢复，不新建任务
6. `forbidden` 拒绝自动重跑，说明原因和人工处理方式
7. 重跑完成或失败后必须写回 `attempts`、`last_run_at`、`last_error`、`next_action`、`history`

### block / unblock

用户说明阻断或解除阻断时：

- 写入/更新 `blockers[]`
- 更新对应 stage 的 `status`、`last_error`、`next_action`
- 不删除历史记录，追加到 `history[]`

### release plan

用户要求“生成发布计划 / 我要发布计划 / 发布前计划”时：

1. 先输出 `Workflow Status` 固定状态块
2. 读取 `meta.yaml`、`contract.yaml`、`verification.md`、`execution-state.yaml`
3. 生成或更新 `release-plan.md`
4. 发布计划必须至少包含：
   - 发布目标：环境、目标状态、计划时间、负责人
   - 发布范围：涉及仓库、分支、Swan 应用 / 服务、是否必发
   - 发布顺序：前端/后端/配置的顺序和依赖
   - 前置条件：验证结果、分支 push、阻断缺陷、配置/DB 变更
   - 验证清单：Smoke、核心业务路径、接口回显、回归点
   - 回滚方案：前端、后端、配置、数据的回滚方式
   - 风险与人工确认项
5. 更新 `execution-state.yaml`：
   - `release_plan.status: done | needs_review`
   - `release_plan.outputs` 包含 `release-plan.md`
   - `deploy.inputs` 必须包含 `release-plan.md`
   - `history[]` 追加发布计划生成记录
6. 如果缺少分支、Swan 应用、发布时间、负责人等信息，不得编造；写入 `待补充`，并将 `release_plan.status` 标为 `needs_review`

## Required State Fields

每个 stage 至少包含：

```yaml
status: pending
attempts: 0
inputs: []
inputs_hash: ""
outputs: []
rerun_policy:
  mode: safe
side_effects:
  safe_to_rerun: true
  requires_confirmation: false
last_error: null
next_action: ""
```

## Output Style

默认用中文简洁输出：

```markdown
当前阶段：e2e（failed）
阻断项：UI-002 autofocus 失败
重跑策略：safe，可直接重跑
下一步：修复 autofocus 后运行 playwright-harness-e2e，并更新 verification.md
```

如果需要改文件，先说明将修改哪些文件，再执行。

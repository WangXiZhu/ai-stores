---
name: coc-workspace-from-changes
description: >-
  Analyzes git changes against /Users/limo/git/gitee.com/project.md to infer
  related COC/SH repos, then generates a multi-root .code-workspace file.
  Use when the user asks to create a workspace from current changes, analyze
  cross-repo dependencies for a task, or auto-build a code-workspace for
  multi-repo development.
---

# COC Workspace from Changes

根据当前代码变动和 `project.md`，推断涉及的前后端仓库，生成 `.code-workspace` 多根工作区文件。

## 前置条件

- 项目地图：`/Users/limo/git/gitee.com/project.md`（**必须先读**第 1.1、4、7–14 节）
- 前端根目录：`/Users/limo/git/gitee.com`
- Java 根目录：`/Users/limo/git/gitee.com/java`
- **Workspace 固定存放目录**：`/Users/limo/git/gitee.com/java`（所有 `.code-workspace` 必须写在此目录下）
- 详细映射表见 [reference.md](reference.md)

## 工作流

复制并跟踪进度：

```
- [ ] Step 1: 收集当前变动
- [ ] Step 2: 识别已变更仓库（种子）
- [ ] Step 3: 从 diff 推断关联仓库
- [ ] Step 4: 解析本地路径、过滤未克隆仓库
- [ ] Step 5: 生成 .code-workspace
- [ ] Step 6: 向用户汇报依赖说明
```

### Step 1: 收集当前变动

在**当前 Cursor 已打开的根目录**或用户指定仓库中执行：

```bash
git status --short
git diff --name-only
git diff --cached --name-only
# 多根工作区时，对每个根目录分别执行
```

若用户指定了分支对比基准，额外执行 `git diff <base>...HEAD --name-only`。

### Step 2: 识别种子仓库

从变更文件路径反推仓库名：

| 路径特征 | 仓库 |
| --- | --- |
| `/Users/limo/git/gitee.com/<name>/...` 且非 `java/` | 前端 `<name>` |
| `/Users/limo/git/gitee.com/java/<name>/...` | Java `<name>` |
| `haixin-openspec/...` | `haixin-openspec`（OpenSpec 文档仓） |

**种子仓库 = 有直接 git 变动的仓库**，必须纳入 workspace。

### Step 3: 从 diff 推断关联仓库

在种子仓库基础上，扫描 diff 内容并按下列规则**扩展**关联仓库（去重）。优先读 `project.md` 对应章节；速查用 [reference.md](reference.md)。

#### 3.1 API 路径 → 后端（`project.md` 第 12 节）

| diff 中出现 | 加入仓库 |
| --- | --- |
| `/oh/`、`gateway/oh` | `coc-ohappcore` |
| `/sf/` | `coc-sfbizcore` |
| `/sflc/`、`schema`、`jumpconf` | `coc-sflc`（未克隆则标注）、`coc-damo`（Lion BFF） |
| `/api/lion/`、`/damo/` | `coc-damo` |
| `/ianvs/`、`/sso/` | `coc-ianvs`、`coc-ucenter` |
| `/zeus/` | `coc-zeus` |
| `/sfmrcore/`、`/api/damo/ocr`、`indicator` | `coc-sfmrcore`、`coc-damo` |
| `/metis/` | `coc-metis` |
| `/lego/` | `coc-lego`（Java）、`coc-lego-front` |
| `/pc/` | `sh-patient-care` |
| `/minisaas/` | `coc-minisaas` |

#### 3.2 前端仓库 → 默认后端（`project.md` 第 13 节）

| 前端种子 | 默认加入 |
| --- | --- |
| `coc-patient-mini-program`、`coc-doctor-mini-program`、`starfish-health-applet` | `coc-ohappcore`、`coc-sfbizcore`、`coc-sflc` |
| `coc-case-management-platform` | `coc-sfbizcore`、`coc-damo`、`coc-ohappcore` |
| `coc-patient-education` | `coc-damo`、`coc-metis`、`coc-labelcenter` |
| `coc-lion-basic-data`、`coc-lion-ocr` 等 Lion 子应用 | `coc-damo` + 路径指向的下游 |
| `coc-knowledge-base` | `coc-metis` |
| `data-tracker` | `coc-sflc`、`coc-damo` |

#### 3.3 npm 包 → 源码仓（`project.md` 第 4 节）

diff 中 `import ... from '@coc/<pkg>'` 或 `package.json` 依赖变更时，加入对应源码仓（如 `@coc/pc-component` → `coc-pc-component`）。**仅当用户需要改包源码时加入**；否则只记录依赖关系，不强制加入 workspace。

#### 3.4 Java Facade / Feign（后端种子）

- diff 含 `coc-*-common-facade`：加入 facade 所属服务（如 `coc-sfbizcore-common-facade` → `coc-sfbizcore`）
- 可复用 `~/.cursor/skills/swan-deploy/config/backend-service-deps.json` 的 `dependencies` 图扩展**直接** facade 依赖（**不要**无差别展开全部传递依赖，避免 workspace 过大）
- `coc-damo` 改动涉及 Lion BFF 时，根据 Feign 接口名对照下游

#### 3.5 产品线（`project.md` 第 1.1 节）

- 种子为 `coc-*` 时，**不要**自动混入 `sh-*`（除非 diff 明确引用 SH 路径如 `/pc/**`）
- 种子为 `sh-*` 时，对照第 7.3 节 COC 镜像关系，按需加入对应 `coc-*` 只读参照

#### 3.6 固定附加项

| 仓库 | 规则 |
| --- | --- |
| `haixin-openspec` | **始终加入** workspace（OpenSpec / 设计文档） |
| `local-api-proxy` | 推断结果中包含 **任一 Java 后端仓库**（`java/` 下）时 **必须加入**，用于本地 API 联调代理 |

其他按需项：

| 场景 | 可选加入 |
| --- | --- |
| 网关路由改动 | `coc-gateway` |

### Step 4: 解析路径并过滤

对每个仓库名解析本地目录（含别名，见 reference.md）：

1. 前端：`/Users/limo/git/gitee.com/<localDir>`
2. Java：`/Users/limo/git/gitee.com/java/<name>`
3. **目录不存在**：记入「未克隆」列表，**不写入** workspace（在汇报中提示用户 `git clone`）

### Step 5: 生成 .code-workspace

**输出路径**（按优先级）：

1. 用户指定路径（**仍须在** `/Users/limo/git/gitee.com/java/` 下）
2. 默认：`/Users/limo/git/gitee.com/java/<task-slug>.code-workspace`（task-slug 取自分支名、OpenSpec change 名或任务简述）
3. 兜底：`/Users/limo/git/gitee.com/java/coc-task.code-workspace`

**不要**把 workspace 写到前端仓库、`haixin-openspec` 子目录或其他位置。

workspace 内 `folders[].path` 一律相对 `java/` 目录计算，例如：

| 仓库 | path 示例 |
| --- | --- |
| 前端 `coc-patient-education` | `../coc-patient-education` |
| Java `coc-damo` | `coc-damo` |
| `haixin-openspec` | `../haixin-openspec` |
| `local-api-proxy` | `../local-api-proxy` |

**生成方式**（推荐脚本）：

```bash
node ~/.cursor/skills/coc-workspace-from-changes/scripts/create-workspace.mjs \
  --slug "患教标签-审核详情" \
  --name "患教标签-审核详情" \
  coc-patient-education coc-damo coc-metis
```

参数说明：

- `--slug`：文件名（不含扩展名），输出到 `java/<slug>.code-workspace`（与 `--out` 二选一，**优先用 `--slug`**）
- `--out`：完整绝对路径（须位于 `java/` 下；仅当用户明确指定完整路径时使用）
- `--from`：相对路径基准，**默认固定为** `/Users/limo/git/gitee.com/java`
- `--name`：任务说明（可选，仅用于日志）
- 后续参数：仓库名或相对 `gitee.com` 的路径，如 `coc-patient-education`、`coc-damo`（Java 同目录可省略 `java/` 前缀）

**排序建议**：前端种子 → 关联前端 → Java 下游 → `haixin-openspec` → `local-api-proxy`（有后端时）。

**不要**重复添加已在 workspace 中的文件夹。

用户若要求打开 workspace：

```bash
cursor /Users/limo/git/gitee.com/java/<task-slug>.code-workspace --classic
```

### Step 6: 汇报格式

向用户输出：

```markdown
## Workspace 已生成

**文件**: `/Users/limo/git/gitee.com/java/xxx.code-workspace`

### 种子仓库（有变动）
- coc-patient-education — 审核详情、标签组件

### 推断关联仓库
- java/coc-damo — `/api/lion/**` BFF（patient-education 患教后台）
- java/coc-labelcenter — 标签接口

### 未克隆（已跳过）
- java/coc-sflc — schema 相关，建议补克隆

### 打开方式
cursor /Users/limo/git/gitee.com/java/xxx.code-workspace --classic
```

## 约束

- **最小够用**：只加入与当前任务相关的仓库，避免把全部 COC 仓库塞进 workspace
- **先 COC / SH 分线**，再选仓库
- **不修改**各仓库代码；本 skill 只生成 workspace 文件
- 不覆盖已有 `.code-workspace`，除非用户明确要求；默认生成新文件名（含任务 slug 或日期）

## 示例

**输入**：用户在 `coc-patient-education` 改了 `AuditDetail`，新增患教标签，调用了 `@coc/pc-component` 的 `DiseaseCascader`。

**推断**：
- 种子：`coc-patient-education`
- 患教后台接口经 Lion → `coc-damo`
- 标签数据 → `coc-labelcenter`
- 不加入 `coc-pc-component`（除非要改组件库源码）

**输出**：`/Users/limo/git/gitee.com/java/患教标签-审核详情.code-workspace`，folders 含 `../coc-patient-education`、`coc-damo`、`coc-labelcenter`、`../haixin-openspec`，以及有后端时的 `../local-api-proxy`。

## 附加资源

- 映射速查：[reference.md](reference.md)
- Java facade 依赖图：`~/.cursor/skills/swan-deploy/config/backend-service-deps.json`
- 路径风格参考：`haixin-openspec/template-plan-join-type/模版添加门诊.code-workspace`（该文件在 openspec 下，**新 workspace 统一改存 `java/`**）

# AI Auto-Coding Skills 库 (Antigravity Skills)

这是一个为 AI 全栈研发智能体（如 Github Copilot, Gemini Antigravity, Claude Code 等）编写的自定义技能（Skills）库。通过这些专业级的上下文工作流配置，你可以让 AI 助手在处理繁杂的业务对接、代码生成与稳定性保障时，像高级工程师一样思考和输出高质量代码。

## 📥 如何接入与使用？

### 1. 本地导入

Clone 或下载本仓库，将所需的 skill 文件夹复制到对应 AI Agent 的技能目录。不同平台的路径如下：

| 平台 | 技能目录路径 |
|------|------------|
| **Accio** | `~/.accio/accounts/{accountId}/agents/{agentId}/agent-core/skills/` |
| **Google Gemini Antigravity** | `~/.gemini/antigravity/skills/` |
| **Claude Code** | `.claude/skills/`（项目根目录）或 `~/.claude/skills/`（全局） |

**Accio 平台示例：**
```bash
# 将 skill 复制到 Accio Agent 技能目录
cp -r skills/react-taro-figma-ui ~/.accio/accounts/<你的AccountId>/agents/<你的AgentId>/agent-core/skills/
```

复制后**无需重启**，Agent 会在下次对话时自动加载新 skill。

> **注意（react-taro-figma-ui）**：此 skill 依赖 Figma MCP 服务。使用前请确保已在 Agent 中配置并启用 `figma-developer-mcp`（或其他兼容的 Figma MCP 工具），否则无法调用设计数据。

> **注意（quant-trader）**：此 skill 需配合 `futuapi` skill 使用（富途 OpenD 行情接口）。请同时安装 `futuapi` skill 并确保 OpenD 客户端已启动。

### 2. 触发与对答
这些技能会自动成为 AI 助手的后台增强知识库，你**不再需要输入大段带有架构限制的Prompt**，只需在普通的对话中自然带有触发点：
- "帮我还原这个 Figma 链接" -> 会自动触发 UI 架构师的转换能力。
- "根据这个 JSON 接口文件，写一下我们小程序的请求服务和 TypeScript 类型" -> 无缝生成高级且兼容弱网的 JSDoc/TS 类型声明及组件状态钩子对接。
- "分析药明康德应该买入还是卖出" -> 自动拉取实时行情，完成技术分析并给出结构化交易决策。

---

## 🛠 内置核心 Skills 介绍

### 🎨 1. Figma UI 1:1高保真还原 (`react-taro-figma-ui`)
**专门解决：复制 Figma 代码质量低下、布局无序和不适配不同端的问题。**
- **功能特性**：
  - **环境识别隔离**：可以准确判断生成 Web 原生（`div/span/img`）还是小程序 Taro 框架 (`View/Text/Image`) 代码。
  - **尺寸运算处理**：配置了小程序常见的尺寸自动翻倍特性（px * 2）。
  - **静态资源工程化**：能自动用 HTTP 爬取 Figma 设计图里的 SVG/PNG 并在你的项目中生成打着当天时间戳日期的文件夹，把资源落盘，杜绝占位链接上线。
- **最佳触发短语**：
  *"帮我把这个 figma <网址> 彻底还原成 React 组件并下载引用的切图。"*

### 🔌 2. API 接驳与 TypeScript 生成 (`interface-integration`)
**专门解决：后端写接口随意、文档注释乱丢、没有标准的接口代码体系引发的对接扯皮。**
- **功能特性**：
  - **垃圾场里洗数据**：即使后端抛给你带有大量乱七八糟注释（非标 JSON）、多包裹 `success, msg, data` 无用嵌套的文档，Skill 也能自动清洗。
  - **JSDoc/TypeScript 强类型**：自动把后端注释转换为完美的 `type/interface` 或者哪怕纯 JS 下也极完美的 `@typedef` 跳转。
  - **React 强挂载代码生成**：根据你是 Function Component 还是 Class Component 自动提供并注入 `useEffect/componentDidMount` 骨架及异步状态扭转。
- **最佳触发短语**：
  *"按照这段我贴过来的接口请求体和响应体，给这块列表做一个对接。这是一个纯JS项目。"*

### 🛡️ 3. 极端鲁棒性测试专家 (`frontend-stability`)
**专门解决：日常弱网环境下经常发生的重复连击、线上大面积白屏崩溃。**
- **功能特性**：
  - **死循环与白屏猎手**：检查任何没有判断 `?.` 就直接 `.map()` 的数据，或排查图片加载 `onError` 可能存在的重新渲染污染。
  - **并发锁机制控制**：拒绝只使用 UI disabled 来防抖！强迫 AI 帮你在逻辑层写上闭环 `Ref / isSubmitting + finally` 锁屏来斩断弱网时由于请求挂起产生的提交防刷漏洞。
  - **兜底检查**：自动捕捉你的异常 HTTP 处理和各种边界空处理的 UI 漏洞。
- **最佳触发短语**：
  *"写完了，请用 frontend-stability 测试一下这段代码，帮我堵上下面的坑。"* 或 *"帮我 review 一下刚才你写的提交表单的鲁棒性！"*

### 📈 4. 量化交易决策引擎 (`quant-trader`)
**专门解决：缺乏系统化交易纪律、凭感觉买卖、无止损仓位管理混乱的问题。**

> **前置依赖**：需同时安装 `futuapi` skill，并确保富途 OpenD 客户端已启动运行。

- **功能特性**：
  - **全流程决策引擎**：数据获取 → 技术指标计算 → 市场判断 → 信号评分 → 交易决策 → 风控输出，一气呵成。
  - **多维信号评分系统（100分制）**：趋势（30分）、RSI（20分）、MACD（20分）、布林带（10分）、成交量（10分）、K线形态（10分），量化驱动决策。
  - **自适应风险控制**：基于 ATR 和支撑阻力位自动计算止损止盈，Kelly-风险百分比混合仓位算法，单笔风险硬上限 2%。
  - **K线形态识别**：支持十字星、锤子线、射击之星、看涨/看跌吞没等经典形态。
  - **无硬编码路径**：自动定位 futuapi scripts 目录，支持 `FUTU_SCRIPTS_DIR` / `FUTU_PYTHON_BIN` 环境变量覆盖，可在任意机器上运行。
- **最佳触发短语**：
  *"分析一下药明康德现在应该买入还是持有，我目前是轻仓。"*
  *"帮我做一个量化分析，判断 5G ETF 的买卖时机。"*

---
> 持续集成：本 Skill 库持续吸收大型生产落地项目的大型 Bug 处理与工程化架构经验而建立，提升生产力和系统稳固性。

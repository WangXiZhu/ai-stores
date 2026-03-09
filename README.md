# AI Auto-Coding Skills 库 (Antigravity Skills)

这是一个为 AI 全栈研发智能体（如 Github Copilot, Gemini Antigravity, Claude Code 等）编写的自定义技能（Skills）库。通过这些专业级的上下文工作流配置，你可以让 AI 助手在处理繁杂的业务对接、代码生成与稳定性保障时，像高级前端架构师一样思考和写出高质量工程代码。

## 📥 如何接入与使用？

如果你使用的是类似于 Google Gemini AI 或其他支持 `SKILL.md` 的智能体，可以通过以下简单的方式集成这套强大的开发工作流：

### 1. 本地导入
1. Clone 或下载本仓库。
2. 将特定的 skill 文件夹（例如 `react-taro-figma-ui` 或 `interface-integration`）复制到你本地的 AI Agent 配置读取目录（例如 macOS 上的 `~/.gemini/antigravity/skills/` 或者是其他代理的技能文件夹中）。

### 2. 触发与对答
这些技能会自动成为 AI 助手的后台增强知识库，你**不再需要输入大段带有架构限制的Prompt**，只需在普通的对话中自然带有触发点：
- “帮我还原这个 Figma 链接” -> 会自动触发 UI 架构师的转换能力。
- “根据这个 JSON 接口文件，写一下我们小程序的请求服务和 TypeScript 类型” -> 无缝生成高级且兼容弱网的 JSDoc/TS 类型声明及组件状态钩子对接。

---

## 🛠 内置核心 Skills 介绍

目前此库主要包含了三项由资深全栈实践检验出来的开发护城河技能：

### 🎨 1. Figma UI 1:1高保真还原 (`react-taro-figma-ui`)
**专门解决：复制 Figma 代码质量低下、布局无序和不适配不同端的问题。**
- **功能特性**：
  - **环境识别隔离**：可以准确判断生成 Web 原生（`div/span/img`）还是小程序 Taro 框架 (`View/Text/Image`) 代码。
  - **尺寸运算处理**：配置了小程序常见的尺寸自动翻倍特性（px * 2）。
  - **静态资源工程化**：能自动用 HTTP 爬取 Figma 设计图里的 SVG/PNG 并在你的项目中生成打着当天时间戳日期的文件夹，把资源落盘，杜绝占位链接上线。
- **最佳触发短语**：
  *“帮我把这个 figma <网址> 彻底还原成 React 组件并下载引用的切图。”*

### 🔌 2. API 接驳与 TypeScript 生成 (`interface-integration`)
**专门解决：后端写接口随意、文档注释乱丢、没有标准的接口代码体系引发的对接扯皮。**
- **功能特性**：
  - **垃圾场里洗数据**：即使后端抛给你带有大量乱七八糟注释（非标 JSON）、多包裹 `success, msg, data` 无用嵌套的文档，Skill 也能自动清洗。
  - **JSDoc/TypeScript 强类型**：自动把后端注释转换为完美的 `type/interface` 或者哪怕纯 JS 下也极完美的 `@typedef` 跳转。
  - **React 强挂载代码生成**：根据你是 Function Component 还是 Class Component 自动提供并注入 `useEffect/componentDidMount` 骨架及异步状态扭转。
- **最佳触发短语**：
  *“按照这段我贴过来的接口请求体和响应体，给这块列表做一个对接。这是一个纯JS项目。”*

### 🛡️ 3. 极端鲁棒性测试专家 (`frontend-stability`)
**专门解决：日常弱网环境下经常发生的重复连击、线上大面积白屏崩溃。**
- **功能特性**：
  - **死循环与白屏猎手**：检查任何没有判断 `?.` 就直接 `.map()` 的数据，或排查图片加载 `onError` 可能存在的重新渲染污染。
  - **并发锁机制控制**：拒绝只使用 UI disabled 来防抖！强迫 AI 帮你在逻辑层写上闭环 `Ref / isSubmitting + finally` 锁屏来斩断弱网时由于请求挂起产生的提交防刷漏洞。
  - **兜底检查**：自动捕捉你的异常 HTTP 处理和各种边界空处理的 UI 漏洞。
- **最佳触发短语**：
  *“写完了，请用 frontend-stability 测试一下这段代码，帮我堵上下面的坑。”* 或 *“帮我 review 一下刚才你写的提交表单的鲁棒性！”*

---
> 持续集成：本 Skill 库持续吸收大型生产落地项目的大型 Bug 处理与工程化架构经验而建立，不炫技，只为极致生产力和系统稳固而生。

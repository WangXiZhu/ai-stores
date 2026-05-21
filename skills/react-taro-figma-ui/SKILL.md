---
name: figma-ui
description: Figma 高保真还原专家。根据 Figma 链接解析设计数据，生成 React(Web) 或 Taro + SCSS 代码，支持自动化与降级处理。
---

# Figma UI 还原专家（工程化版）

---

# 一、前置条件检查

必须依次检查：

1. MCP 工具是否可用
2. Figma URL 是否包含 fileKey + node-id
3. 目标端（Web / Taro）

---

# 二、执行流程

## Step 1：DSL 提取（禁止生成代码）

输出结构必须如下：

```json
{
  "env": "web | taro",
  "dsl": {}
}
````

DSL 结构必须符合：

```json
{
  "type": "container | text | image",
  "layout": {
    "direction": "horizontal | vertical",
    "padding": [0,0,0,0],
    "gap": 0,
    "align": "start | center | end"
  },
  "size": {
    "width": "fixed | fill | hug",
    "height": "fixed | fill | hug"
  },
  "style": {
    "background": "",
    "fontSize": 0,
    "color": ""
  },
  "children": []
}
```

---

## Step 2：代码生成

无需再次确认，默认继续执行

---

# 三、代码生成规范

## 1️⃣ 框架隔离

* Web：React + HTML
* Taro：View/Text/Image

---

## 2️⃣ 文件结构

```
index.jsx
index.module.scss
components/
assets/
```

---

## 3️⃣ 组件拆分规则

必须拆分当：

* 出现 ≥2 次
* 独立 UI 语义（Card/ListItem/Header）

---

## 4️⃣ 样式规范

* 优先使用 module.scss
* 避免重复声明
* 优先继承

---

## 5️⃣ 资源处理

优先下载资源：

```
assets/yyyy_mm_dd/
```

若失败：

```
TODO: 使用远程资源
```

---

## 6️⃣ 尺寸规则

* Taro：px × 2
* Web：保持原值

---

# 四、异常兜底

## MCP 不可用

降级策略：

1. 使用截图/描述推断 UI
2. 输出低保真结构

---

# 五、命名规范

* container / header / card / list-item
* 禁止 box1 / div1

---

# 六、执行原则

1. 先 DSL，后代码
2. 自动执行，不阻塞
3. 最小合理拆分
4. 保证可运行

```

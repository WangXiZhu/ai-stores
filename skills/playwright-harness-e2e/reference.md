# Playwright Harness E2E — Reference

## vite.e2e.config.js starter

```javascript
import { fileURLToPath, URL } from 'node:url'
import path from 'path'
import postCssPxToRem from 'postcss-pxtorem'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  define: { global: 'globalThis' },
  plugins: [
    react({
      babel: {
        plugins: [
          ['@babel/plugin-proposal-decorators', { legacy: true }],
          ['@babel/plugin-proposal-class-properties', { loose: true }],
        ],
      },
    }),
  ],
  css: {
    preprocessorOptions: {
      less: { javascriptEnabled: true },
    },
    postcss: {
      plugins: [
        postCssPxToRem({
          rootValue: 12,
          propList: ['*'],
          exclude: (filePath) => /node_modules/.test(filePath),
        }),
      ],
    },
  },
  resolve: {
    alias: {
      // COPY from main app config
      '@': fileURLToPath(new URL('./', import.meta.url)),
      src: fileURLToPath(new URL('./', import.meta.url)),
    },
  },
})
```

## harness.html

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>Feature E2E Harness</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./feature-harness.jsx"></script>
  </body>
</html>
```

## harness.jsx starter

```jsx
/* eslint-disable */
import { ConfigProvider } from 'antd'
import zhCN from 'antd/es/locale/zh_CN'
import { configure } from 'mobx'
import { Provider } from 'mobx-react'
import React from 'react'
import ReactDOM from 'react-dom'

import 'antd/dist/antd.less'
import '../src/index.css'
import FeaturePage from '../src/pages/Feature'
import { allStores } from '../src/util'

configure({ enforceActions: 'observed' })

// Only universal defaults; per-test flags via addInitScript in gotoHarness
window.localStorage.setItem('orgId', 'org-e2e')

const Harness = () => (
  <Provider {...allStores}>
    <ConfigProvider locale={zhCN}>
      <FeaturePage />
    </ConfigProvider>
  </Provider>
)

ReactDOM.render(<Harness />, document.getElementById('root'))
```

## mock fixture pattern

```javascript
const json = (route, body) =>
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })

const apiSuccess = (data) => ({
  success: true,
  code: 'SUCCESS',
  msg: '成功',
  data,
})

let listState = []

async function installFeatureApiMocks(page, options = {}) {
  const { useNetworkApis = true, ...hooks } = options

  await page.route('**/api/.../orgInfo/list**', (route) =>
    json(route, { success: true, data: [{ orgId: 'org-e2e', checked: true }] }))

  await page.route('**/api/.../list**', (route) => {
    const url = route.request().url()
    if (url.includes('special=import')) {
      return json(route, { success: true, code: '00000', result: listState })
    }
    return json(route, { success: true, data: [] })
  })

  if (!useNetworkApis) return

  await page.route('**/sf/api/.../upload**', async (route) => {
    hooks.onUpload?.(route.request())
    await json(route, apiSuccess([{ fileUrl: 'https://oss.example.com/a.md' }]))
  })

  await page.route('**/sf/api/.../confirm**', async (route) => {
    hooks.onConfirm?.(route.request())
    listState = [{ id: '1', name: 'Item A' }]
    await json(route, apiSuccess(true))
  })
}

async function gotoFeatureHarness(page, options = {}) {
  const { featureMock = 'false' } = options

  await page.addInitScript((mockFlag) => {
    window.localStorage.setItem('orgId', 'org-e2e')
    window.localStorage.setItem('featureMock', mockFlag)
  }, featureMock)

  await page.goto('/e2e/feature-harness.html')
  await page.locator('.feature-root').waitFor({ timeout: 15000 })
}

module.exports = { installFeatureApiMocks, gotoFeatureHarness }
```

## playwright.config.js starter

```javascript
const { defineConfig, devices } = require('@playwright/test')

const HOST = process.env.E2E_HOST || '127.0.0.1'
const PORT = process.env.E2E_PORT || 4173
const browserChannel = process.env.E2E_BROWSER_CHANNEL || 'chrome-canary'
const headless = process.env.E2E_HEADLESS !== 'false'
const baseURL = `http://${HOST}:${PORT}`

module.exports = defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.js',
  testIgnore: '**/unit/**',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: browserChannel,
      use: { ...devices['Desktop Chrome'], channel: browserChannel, headless },
    },
  ],
  webServer: {
    command: `pnpm exec vite --config vite.e2e.config.js --host ${HOST} --port ${PORT}`,
    url: `${baseURL}/e2e/feature-harness.html`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
```

## Fetch / gateway matching

Many apps prefix URLs in `h5Fetch`:

- Paths starting with `/sf/` → `getGatewayUrl() + url`
- Playwright `page.route('**/sf/api/...**')` still matches full URL

Mock response must pass app `getData` checks:

- `code === 'SUCCESS'` or `code === '00000'`
- Otherwise UI shows「数据请求失败」and state stays empty

## Built-in service mock vs route mock

| Mode | Setup | When |
|------|--------|------|
| Built-in | `localStorage.featureMock = 'true'` | Quick dev; default task indices may not match test-case |
| Route | `featureMock = 'false'` + `page.route` | **E2E assertions on API order/body** |
| Hybrid | `featureMock = 'true'` + routes for org/list only | Human-check entry using `createMockTask(0)` |

## Locator cookbook (antd 3/4)

| UI | Locator |
|----|---------|
| Tab with count | `getByRole('tab', { name: /导入模板\s+2/ })` |
| Hidden file input | `locator('.feature__file-input').setInputFiles([...])` |
| Drawer | `locator('.feature-drawer')` + `toBeHidden()` |
| Message | `locator('.ant-message-notice-content').filter({ hasText: '...' })` |
| Confirm modal OK | `locator('.ant-modal-confirm').getByRole('button', { name: '继 续' })` — verify actual label in snapshot |
| Strict mode fix | Parent scope: `.import-temp .list`, `{ exact: true }` |

## Tunable mock delays (optional)

For local debugging flaky loading overlays:

```javascript
// services: delay = Number(localStorage.getItem('featureRegenDelay')) || 1800
// E2E: page.addInitScript(() => localStorage.setItem('featureRegenDelay', '6000'))
```

Prefer fixing debounce/race in test design over infinite delays.

## CI / agent execution

```bash
cd <package>
pnpm exec playwright test e2e/
# Sandbox blocks Chrome Canary → run with full permissions
```

Vitest (parallel):

```bash
pnpm test:unit      # e2e/unit/**/*.test.js
pnpm test:feature   # package-specific script
```

`vitest.config.js`:

```javascript
include: ['e2e/unit/**/*.test.js'],
```

## Report template (openspec/test/playwright.md)

```markdown
# Playwright / 自动化测试报告

## 结论
| 层级 | 通过 | 失败 | fixme |
| Vitest | n | 0 | 0 |
| Playwright | n | 0 | k |

## 环境
- Harness: http://127.0.0.1:4173/e2e/...
- 命令: pnpm e2e:canary

## 覆盖矩阵
| 文档 ID | Vitest | E2E |
| TI-01 | partial | pass |
```

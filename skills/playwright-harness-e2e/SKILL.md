---
name: playwright-harness-e2e
description: >-
  Sets up Playwright CLI E2E with Vite harness pages, page.route API mocks, and
  Vitest unit tests for React/antd/MobX apps without login. Use when adding E2E
  tests, harness, playwright.config, vite.e2e.config, page.route mocks,
  template-plan or modal flows, or when the user asks to extract/reuse an E2E
  testing workflow across projects.
---

# Playwright Harness E2E

## Goal

Ship **fast, login-free** UI flow tests:

- **Vitest** (`e2e/unit/**/*.test.js`) → pure utils / store mapping / validators
- **Playwright (CLI)** → user-visible flows on a **Harness** at `127.0.0.1:4173`
- **Not** Playwright MCP on dev/staging unless the user explicitly wants manual env QA

## Decision tree

| Need | Approach |
|------|----------|
| Pure function / status machine | Vitest only |
| Full page + auth + real backend | Real-env E2E or MCP (separate skill) |
| Complex UI flow, mockable APIs | **Harness + `page.route`** (this skill) |
| Feature already has `localStorage.*Mock` in services | Prefer **disabling** built-in mock (`='false'`) + `page.route` for deterministic E2E |

## Standard layout (per package/app)

```
<package>/
├── playwright.config.js
├── vite.e2e.config.js          # E2E-only Vite; do NOT reuse hxc/webpack dev config blindly
├── package.json                # scripts: e2e, e2e:canary, e2e:headed
├── e2e/
│   ├── unit/                   # Vitest *.test.js（纯逻辑）
│   ├── <feature>-harness.html
│   ├── <feature>-harness.jsx
│   ├── <feature>.spec.js       # Playwright *.spec.js
│   └── fixtures/
│       └── <feature>Mocks.js
└── openspec/test/playwright.md # optional report matrix
```

Multiple harnesses share one Vite server: `webServer.url` can point at any `e2e/*-harness.html`; specs use `page.goto('/e2e/other-harness.html')`.

## Workflow (agent checklist)

Copy and track:

```
Harness E2E progress:
- [ ] 1. Read OpenSpec / test-case.md or user story → list APIs, localStorage, assertions
- [ ] 2. Add vite.e2e.config.js (decorators, less, global, aliases)
- [ ] 3. Add harness (Provider, antd.less, minimal localStorage)
- [ ] 4. Add fixtures: json(), apiSuccess(), install*ApiMocks(page)
- [ ] 5. Add spec with beforeEach mocks + scoped locators
- [ ] 6. playwright.config: webServer, workers:1, baseURL 4173
- [ ] 7. Run: pnpm exec playwright test e2e/<spec>.js (permissions: all if Canary)
- [ ] 8. Update openspec/test/playwright.md matrix
```

### Step 1 — Map the flow

From `test-case.md` or PRD extract:

- Entry route or **root component** to mount
- `localStorage` keys (`orgId`, feature flags)
- HTTP methods + paths (include **gateway prefix**, e.g. `/sf/api/...`, `/api/doctor/...`)
- Response shape: `{ success, code, data }` vs `{ success, code: '00000', result }`
- UI strings (antd Modal OK may be `确 定` with space)

### Step 2 — `vite.e2e.config.js`

Minimal requirements for legacy React + antd + MobX:

- `@vitejs/plugin-react` + **legacy decorators** if stores use `@action`
- `define: { global: 'globalThis' }`
- `less: { javascriptEnabled: true }`
- Copy **resolve.alias** from main Vite/webpack config
- **Exclude** plugins that break JSX in dev-only pipeline (e.g. inline-style-px-to-rem on source)
- postcss-pxtorem: **exclude `node_modules`** (avoid double-rem on antd)

See [reference.md](reference.md#vitee2econfigjs-starter).

### Step 3 — Harness JSX

Pattern:

1. `import 'antd/dist/antd.less'` — required when not using babel-plugin-import (hxc dev uses on-demand less; harness does not)
2. `import '../src/index.css'` (or app global styles)
3. `Provider` + all stores the page needs
4. Set only **non-secret** `localStorage` defaults in harness; override per test via `page.addInitScript` **before** `goto`
5. Mount **one** feature root (`TemplatePlan`, `PlanModalV2`, etc.)

Do **not** set feature mock flags in harness if tests need different modes — set in `gotoHarness(page, options)`.

### Step 4 — `page.route` mocks

```javascript
const json = (route, body) =>
  route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })

// Match gateway URLs with glob:
// '**/sf/api/doctor/digital/file/uploadFile**'
// '**/api/doctor/digital/treat/template/list**'
```

Rules:

- Register **specific** routes before optional catch-alls
- Use **mutable module state** for list-after-mutation (e.g. empty import list → fill after confirm)
- Align `code` with app fetch wrapper: usually `'SUCCESS'` or `'00000'`
- For POST bodies, assert via `request.postDataJSON()` in hook callbacks
- `installMocks(page, { useNetworkX: false })` early-return when using **built-in** `localStorage.*Mock=true` only

See [reference.md](reference.md#mock-fixture-pattern).

### Step 5 — Spec authoring

```javascript
const { test, expect } = require('@playwright/test')
const { installXMocks, gotoXHarness } = require('./fixtures/xMocks')

test.beforeEach(async ({ page }) => {
  await installXMocks(page)
})

test('TI: happy path', async ({ page }) => {
  await gotoXHarness(page)
  // Scope locators to feature container to avoid strict-mode collisions
  await expect(page.locator('.import-temp .list').getByText('Name', { exact: true })).toBeVisible()
})
```

Practices:

- **Scope** `getByText` under `.import-temp`, `.human-check-modal`, `getByRole('tabpanel', { name })`
- File upload: `locator('input[type="file"]').setInputFiles([{ name, mimeType, buffer }])`
- antd Drawer: `.ant-drawer-open` or feature class `.import-template-drawer`
- Poll APIs: `await expect.poll(() => apiCalls.upload).toBe(1)`
- Unstable overlay/timing: `test.fixme` + comment (debounce vs regenerate abort) — do not block entire suite

### Step 6 — `playwright.config.js`

- `testDir: './e2e'`, `workers: 1`, `fullyParallel: false`
- `webServer`: `pnpm exec vite --config vite.e2e.config.js --host 127.0.0.1 --port 4173`
- `webServer.url`: first harness HTML (any works if all served)
- `reuseExistingServer: !process.env.CI`
- `channel: 'chrome-canary'` via `E2E_BROWSER_CHANNEL` (sandbox may need `required_permissions: ['all']`)

### Step 7 — package.json scripts

```json
"e2e": "playwright test",
"e2e:canary": "E2E_BROWSER_CHANNEL=chrome-canary playwright test",
"e2e:headed": "E2E_HEADLESS=false playwright test"
```

### Step 8 — Documentation

Update `openspec/test/playwright.md` (or project TESTING.md):

- Vitest vs E2E matrix mapped to test-case IDs
- Harness URL, mock flags, known fixme

## MCP vs CLI (tell the user)

| Tool | Use |
|------|-----|
| **Playwright CLI + Harness** | CI, regression, deterministic mocks |
| **Playwright MCP + logged-in profile** | Exploratory QA on dev/staging |

Do not point CLI `webServer` at port 3000 dev server unless user explicitly wants flaky login coupling.

## Reference implementation

Full working example in:

`packages/case-management-platform/` (case-management-platform monorepo)

| Artifact | Path |
|----------|------|
| Plan harness | `e2e/plan-harness.{html,jsx}`, `e2e/fixtures/planMocks.js` |
| Template plan harness | `e2e/template-plan-harness.{html,jsx}`, `e2e/fixtures/templatePlanMocks.js` |
| Specs | `e2e/plan-validate.spec.js`, `e2e/cares-import.spec.js`, `e2e/template-import.spec.js` |
| Config | `playwright.config.js`, `vite.e2e.config.js` |
| Report | `openspec/test/playwright.md` |

More templates: [reference.md](reference.md) · Scenarios: [examples.md](examples.md)

## Anti-patterns

- Using production dev server as Playwright `webServer` without mocks → login wall / flake
- `templateImportMock=true` in harness **and** `page.route` for same endpoints → confusing double behavior
- Global `getByText('肺癌模板A')` when detail panel also contains substring → strict mode violation
- Assuming MCP Chrome profile = CLI E2E results
- `test.only` left in repo

## When user asks to "extract skill for new project"

1. Copy structure from reference implementation; adapt aliases and API paths
2. Create one harness per **independently testable** UI island
3. Port `test-case.md` cases as TI/PV/CI IDs in spec names
4. Run full `pnpm exec playwright test e2e/` with `all` permissions once locally

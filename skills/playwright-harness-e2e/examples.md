# Playwright Harness E2E — Examples

## Example A: Modal flow (plan-ai)

**User story**: Plan modal → CARES import → validate date → confirm import.

**Files** (reference repo):

- `e2e/plan-harness.jsx` — mounts `PlanModalV2`, sets `caresRecommendMock`, `planAiValidateMock`
- `e2e/fixtures/planMocks.js` — routes for patient, plans, template list, cancer stage
- `e2e/cares-import.spec.js` — CI-04, CI-06, CI-08 (fixme)

**Key techniques**:

```javascript
function getCaresPanel(page) {
  return page.getByRole('tabpanel', { name: /CARES推荐/ })
}

await page.locator('.plan-btn-tag', { hasText: 'CARES' }).click()
await getCaresPanel(page).getByPlaceholder('请输入').fill('EP强化方案')
```

**Lesson**: CI-08 failed because 400ms filter debounce aborted regenerate `AbortController`. Mark `test.fixme` until harness exposes debounce-free regenerate hook.

---

## Example B: Full page import (template-plan)

**User story**: Template plan → import tab → batch Markdown → drawer → confirm → list count 2.

**Files**:

- `e2e/template-plan-harness.jsx` — mounts `TemplatePlan`, only `orgId` in file
- `e2e/fixtures/templatePlanMocks.js` — stateful `importTemplateList`, SF upload/import/detail/create
- `e2e/template-import.spec.js` — TI happy path, non-Markdown reject, human_check entry

**Happy path snippet**:

```javascript
await installTemplatePlanApiMocks(page, {
  onImport: (req) => { importBody = req.postDataJSON() },
})
await gotoTemplatePlanHarness(page) // sets templateImportMock=false
await page.getByRole('tab', { name: /^导入模板\s+0$/ }).click()
await page.locator('.import-temp__file-input').setInputFiles(MARKDOWN_FIXTURES)
await expect(page.getByText('正在处理 2 个文件')).toBeVisible()
await page.getByRole('button', { name: '确定导入 (2)' }).click()
await expect(page.getByRole('tab', { name: /导入模板\s+2/ })).toBeVisible()
```

**human_check entry** (built-in mock):

```javascript
await installTemplatePlanApiMocks(page, { useNetworkImportApis: false })
await gotoTemplatePlanHarness(page, { templateImportMock: 'true' })
// First uploaded file → createMockTask index 0 → human_check
await expect(page.getByRole('button', { name: '去校验' })).toBeVisible()
await expect(page.getByRole('button', { name: /^确定导入/ })).toBeDisabled()
```

**Lesson**: Do not assert `getByText('肺癌模板A')` globally — detail header may render「离院肺癌模板A」. Scope: `.import-temp .list`.

---

## Example C: New project from scratch

**User**: "Add E2E for checkout drawer in our Vue app."

1. Confirm stack: if **not** React+Vite, adapt harness (Vue: `createApp` entry, may skip antd.less).
2. Add Playwright + Vite serve config for `e2e/harness.html`.
3. List checkout APIs from Network tab → `page.route`.
4. One spec: open drawer → select item → pay → success toast.
5. Document in `docs/testing.md`.

---

## Example D: User asks for Playwright MCP

Respond:

- MCP = manual/exploratory on `dev.example.com` with saved login
- This skill = **CLI Harness** for CI
- Offer to add MCP profile separately; do not merge into `playwright.config.js` webServer

---

## Naming conventions

| Prefix | Meaning |
|--------|---------|
| `PV` | Plan validation |
| `EDU` | Education picker |
| `CI` | CARES import |
| `TI` | Template import |

Match OpenSpec `test-case.md` section titles in spec `test.describe` comments when helpful.

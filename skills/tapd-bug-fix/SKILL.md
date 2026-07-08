---
name: tapd-bug-fix
description: Read a TAPD bug detail page or TAPD bug link, map it to the correct frontend repository under /Users/limo/git/gitee.com using the local project rules in /Users/limo/git/gitee.com/project.md, then locate the affected code and implement the fix described by the bug. Use when the user gives a TAPD bug URL, bug detail, or asks to "根据 bug 修复", "定位对应项目", or "修复 TAPD 缺陷".
---

# TAPD Bug Fix

Use this skill to turn a TAPD bug into a concrete code fix in the correct frontend repository.

## What This Skill Does

This skill standardizes a fragile workflow:

1. Read TAPD bug details from the user's logged-in browser session.
2. Infer the target project from the bug title, repro URL, module, and environment.
3. Map that project to the correct local repo under `/Users/limo/git/gitee.com`.
4. Implement the bug fix based on the TAPD description.
5. Validate the change with the smallest reliable check available.

## Required Local Facts

Always use these project rules:

- Frontend repositories are under `/Users/limo/git/gitee.com`.
- The project index and routing hints live in `/Users/limo/git/gitee.com/project.md`.
- Mini program work depends on WeChat DevTools related capabilities.
- Shanghai quality-control projects use dynamic dev hostnames and ports, for example `https://boss-d5185.coc.aistarfish.net/lion/ocr`.
- Ordinary COC web projects usually use fixed domains.

## Workflow

### 1. Read the TAPD bug

Prefer the user's existing Chrome login session.

- If the user gives a TAPD link, open or claim that tab from Chrome.
- Extract at minimum:
  - bug title
  - bug description
  - repro steps
  - repro URL or page path
  - module / project hints
  - environment hints
- If the TAPD modal contains sparse fields, use the visible dialog text rather than scraping the whole page.
- Check the TAPD status before doing any code work. Only continue when the bug status is `新`, `待处理`, or `重新打开`. If the status is anything else, stop and tell the user that this skill does not require a fix for the current status.

### 2. Map TAPD to the correct project

Read `/Users/limo/git/gitee.com/project.md` before guessing the repo.

Use these heuristics in order:

1. Repro URL domain and path.
2. Explicit project names in the bug title.
3. Module names such as `lion/basic-data`, `ocr`, `patient-education`, `lego`.
4. Whether the bug is:
   - mini program
   - Shanghai quality-control
   - ordinary COC web

Strong routing rules:

- `boss-d*.coc.aistarfish.net/lion/ocr` usually maps to `sh-lion-ocr`.
- `boss-d*.coc.aistarfish.net/lion/basic-data/#/` usually maps to Shanghai `lion-basic-data` or `sh-lion-basic-data`, not ordinary `coc-lion-basic-data`.
- `skdev-boss.aistarfish.net` and `boss.suifang.acits.com.cn` usually indicate ordinary COC web projects.
- Mini program issues should route to the corresponding `coc-patient-mini-program` or `coc-doctor-mini-program` repo unless the bug clearly belongs to an H5 page embedded inside them.

Do not stop at the first name match. Verify with code evidence:

- route path
- page/component name
- API module naming
- text strings matching the bug page

### 3. Confirm the local repository

After selecting a candidate repo:

- search that repo for route/path/page keywords from the bug
- search for page titles, labels, modal text, and API names from TAPD
- if multiple repos match, prefer the one whose route and environment both align

If there is still ambiguity, pause the workflow. Tell the user which repos are plausible and exactly what evidence is missing. Do not guess the repository or start editing code.

### 4. Fix the bug

Once the repo is confirmed:

- Before editing any files, remind the user to check whether the current branch is the correct target branch.
- If the current branch is `SF20251125110026`, issue a strong warning and do not modify code on that branch. Tell the user to switch to the correct working branch before continuing.
- As a general rule, do not modify code on the `master` branch either. The only exception is an npm package project where the user is explicitly doing a release on local `master`. If the current branch is `master` and this exception is not clearly true, stop and ask the user to switch branches before continuing.

- inspect the affected files before editing
- identify whether the bug is caused by:
  - UI validation
  - route wiring
  - API payload mismatch
  - state management / form behavior
  - environment-specific logic
  - mini program container behavior
- implement the smallest correct fix
- preserve existing project style and local conventions

For TAPD bugs, optimize for behavior correctness over broad refactors.

### 5. Validate

Run the smallest useful validation available:

- targeted test if present
- lint or typecheck if cheap
- page-level verification if a local dev server is already available
- otherwise explain what was verified statically and what remains unverified

## Output Expectations

When using this skill, the final response should include:

- the TAPD bug summary in one short paragraph
- the repo selected and why
- the fix implemented
- the validation performed
- any remaining risk or ambiguity

## Failure Handling

- If TAPD cannot be read because login is missing, ask the user to provide the detail text or restore login.
- If the bug maps to a repo outside `/Users/limo/git/gitee.com`, state that clearly.
- If the mapped repository is not present under `/Users/limo/git/gitee.com`, pause the workflow and tell the user which local path is missing. Do not pull, clone, or create the repository unless the user explicitly asks for that.
- If the description is incomplete or insufficient to map the bug to one project, pause the workflow and say what exact detail is missing: repro URL, page name, expected behavior, environment, or module identifier.

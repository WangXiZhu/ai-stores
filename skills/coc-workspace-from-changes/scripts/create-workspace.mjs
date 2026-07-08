#!/usr/bin/env node
/**
 * Generate a VS Code / Cursor multi-root .code-workspace from repo paths.
 *
 * Usage:
 *   node create-workspace.mjs --out /path/to/task.code-workspace \
 *     coc-patient-education java/coc-damo
 *
 * Repo paths are relative to GITEE_ROOT (/Users/limo/git/gitee.com).
 */

import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const GITEE_ROOT = '/Users/limo/git/gitee.com'
const JAVA_ROOT = join(GITEE_ROOT, 'java')

/** @type {Record<string, string>} */
const DIR_ALIASES = {
  'coc-lego-front': 'coc-lego',
  'coc-lion-dashboard': 'coc-lion-bi',
  'data-tracker': 'coc-data-tracker',
  'lion-basic-data': 'coc-lion-basic-data',
}

const DEFAULT_SETTINGS = {
  'workbench.editor.customLabels.patterns': {
    '**/src/**/index.ts': '${dirname}',
    '**/src/**/index.tsx': ' ${dirname}',
    '**/src/**/index.jsx': '${dirname}',
    '**/src/**/*.scss': '${dirname}(${extname})',
    '**/src/**/*.less': '${dirname}(${extname})',
    '**/src/**/index.vue': '${dirname}',
  },
  'workbench.activityBar.orientation': 'vertical',
}

/**
 * @param {string} repoPath relative to GITEE_ROOT, e.g. coc-patient-education or java/coc-damo
 */
function resolveRepoAbs(repoPath) {
  const normalized = repoPath.replace(/^\//, '')
  const direct = join(GITEE_ROOT, normalized)
  if (existsSync(direct)) return direct

  const base = normalized.split('/').pop()
  if (!base) return null

  const aliasCandidates = Object.entries(DIR_ALIASES)
    .filter(([, logical]) => logical === base || base === logical)
    .map(([dir]) => dir)

  for (const dir of aliasCandidates) {
    const parent = normalized.includes('/') ? dirname(normalized) : ''
    const candidate = join(GITEE_ROOT, parent, dir)
    if (existsSync(candidate)) return candidate
  }

  if (!normalized.startsWith('java/')) {
    const javaCandidate = join(GITEE_ROOT, 'java', base)
    if (existsSync(javaCandidate)) return javaCandidate
  }

  return null
}

function parseArgs(argv) {
  const repos = []
  let out = ''
  let slug = ''
  let from = ''
  let name = ''

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '--out') {
      out = argv[++i]
    } else if (arg === '--slug') {
      slug = argv[++i]
    } else if (arg === '--from') {
      from = argv[++i]
    } else if (arg === '--name') {
      name = argv[++i]
    } else if (arg === '--help' || arg === '-h') {
      console.log(`Usage: node create-workspace.mjs [--slug <name> | --out <file.code-workspace>] [repo...]

Workspace files are stored under: ${JAVA_ROOT}
Repo paths are relative to ${GITEE_ROOT}

Example:
  node create-workspace.mjs --slug patient-edu-labels coc-patient-education coc-damo`)
      process.exit(0)
    } else if (!arg.startsWith('-')) {
      repos.push(arg)
    }
  }

  if (!out && slug) {
    const safeSlug = slug.replace(/[^\w\u4e00-\u9fff-]+/g, '-').replace(/^-|-$/g, '')
    out = join(JAVA_ROOT, `${safeSlug || 'coc-task'}.code-workspace`)
  }

  if (!out) {
    out = join(JAVA_ROOT, 'coc-task.code-workspace')
  }

  out = resolve(out)

  if (!out.startsWith(JAVA_ROOT)) {
    console.error(`Error: workspace must be saved under ${JAVA_ROOT}`)
    console.error(`Got: ${out}`)
    process.exit(1)
  }

  if (repos.length === 0) {
    console.error('Error: at least one repo path is required')
    process.exit(1)
  }

  return {
    out,
    from: from ? resolve(from) : JAVA_ROOT,
    name,
    repos,
  }
}

function main() {
  const { out, from, name, repos } = parseArgs(process.argv)
  const missing = []
  const folders = []
  const seen = new Set()

  for (const repo of repos) {
    const abs = resolveRepoAbs(repo)
    if (!abs) {
      missing.push(repo)
      continue
    }
    const rel = relative(from, abs)
    if (seen.has(rel)) continue
    seen.add(rel)
    folders.push({
      name: abs.split('/').pop(),
      path: rel,
    })
  }

  if (folders.length === 0) {
    console.error('Error: no valid local repos found')
    if (missing.length) console.error('Missing:', missing.join(', '))
    process.exit(1)
  }

  const workspace = {
    folders: folders.map(({ name: folderName, path }) => {
      const entry = { path }
      return entry
    }),
    settings: DEFAULT_SETTINGS,
  }

  mkdirSync(dirname(out), { recursive: true })
  writeFileSync(out, `${JSON.stringify(workspace, null, '\t')}\n`, 'utf-8')

  console.log(`Created: ${out}`)
  if (name) console.log(`Task: ${name}`)
  console.log('Folders:')
  for (const f of folders) {
    console.log(`  - ${f.name} → ${f.path}`)
  }
  if (missing.length) {
    console.log('Skipped (not cloned):')
    for (const m of missing) console.log(`  - ${m}`)
  }
}

main()

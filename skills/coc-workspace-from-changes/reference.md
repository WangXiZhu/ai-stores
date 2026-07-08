# COC 仓库映射速查

来源：`/Users/limo/git/gitee.com/project.md`。完整规则以原文为准。

## 目录约定

| 类型 | 根目录 |
| --- | --- |
| 前端 | `/Users/limo/git/gitee.com` |
| Java | `/Users/limo/git/gitee.com/java` |
| **`.code-workspace` 存放** | **`/Users/limo/git/gitee.com/java`**（固定） |

workspace 内相对路径以 `java/` 为基准：前端仓库用 `../<repo>`，Java 仓库用 `<repo>`。

## 本地目录别名（第 14 节）

| 逻辑名 | 本地目录 |
| --- | --- |
| `coc-lego`（前端） | `coc-lego-front` |
| `coc-lion-bi` | `coc-lion-dashboard` |
| `coc-data-tracker` | `data-tracker` |
| `coc-lion-basic-data` | `coc-lion-basic-data` 或 `lion-basic-data` |
| `coc-lion-ocr` | 仓库内 `packages/lion-ocr` |

解析顺序：先精确匹配目录名，再查别名表，再尝试 `java/<name>`。

## 网关路径 → 仓库（第 12 节）

| 前缀 | 仓库 |
| --- | --- |
| `/oh/**` | `coc-ohappcore` |
| `/sf/**` | `coc-sfbizcore` |
| `/sflc/**` | `coc-sflc` |
| `/ianvs/**` | `coc-ianvs` |
| `/zeus/**` | `coc-zeus` |
| `/sfmrcore/**` | `coc-sfmrcore` |
| `/metis/api/**` | `coc-metis` |
| `/minisaas/**` | `coc-minisaas` |
| `/lego/**` | `coc-lego` |
| `/damo/**` | `coc-damo` |
| `/sso/**` | `coc-ucenter` |
| `/pc/**` | `sh-patient-care` |

## 前端 → 后端（第 13 节）

| 前端 | 主要后端 |
| --- | --- |
| 患者/医生小程序 | `coc-ohappcore`, `coc-sfbizcore`, `coc-sflc` |
| `coc-case-management-platform` | `coc-sfbizcore`, `coc-damo` |
| `coc-patient-education` | `coc-damo`, `coc-metis` |
| Lion 子应用（`coc-lion-*`） | `coc-damo`（BFF）+ 具体下游 |
| `coc-knowledge-base` | `coc-metis` |

## Lion BFF 路径 → 下游（第 13.2 节）

| 路径 | 下游 |
| --- | --- |
| `/api/lion/sflc/**` | `coc-sflc`（经 `coc-damo`） |
| `/api/damo/indicator/**`, `/api/damo/ocr/**` | `coc-damo`, `coc-sfmrcore` |
| `/data-tracker/**` | `coc-sflc` 相关 |

## npm 包 → 源码仓（第 4 节，节选）

| 包名 | 源码仓目录 |
| --- | --- |
| `@coc/pc-component` | `coc-pc-component` |
| `@coc/form-render` | `coc-form-render` |
| `@coc/utils` | `coc-frontend-utils` |
| `@coc/mobile-component` | `coc-h5-library-collection` |
| `@coc/mini-component` | `coc-mini-library-collection` |
| `@coc/hx-cli`, `@coc/lint-config` | `coc-cli`, `coc-npm-packages` |
| `@coc/request-api-sign` | `coc-npm-packages` |

## 业务域 → 仓库（第 8、15 节）

| 域 | 仓库 |
| --- | --- |
| 登录鉴权 | `coc-ianvs`, `coc-ucenter`, `coc-gateway` |
| 患者主数据 | `coc-sfpcif` |
| 医生主数据 | `coc-sfdcif` |
| 病历/OCR | `coc-sfmrcore` |
| 数疗/个案/计划 | `coc-sfbizcore`, `coc-damo`, `coc-warden` |
| 标签 | `coc-labelcenter` |
| 知识库 | `coc-metis` |
| Schema/埋点 | `coc-sflc` |
| 消息 | `coc-nfcore` |

## COC ↔ SH 镜像（第 7.3 节）

改 `coc-*` 时不要自动加 `sh-*`；改 `sh-*` 时可对照：`sh-damo`↔`coc-damo`，`sh-sfbizcore`↔`coc-sfbizcore`，`sh-ohappcore`↔`coc-ohappcore`，等。

## 常用本地未克隆（第 7.2、16 节）

推断到但本地可能没有：`coc-sflc`, `coc-sfdcif`。跳过并在汇报中提示。

## 固定附加仓库

| 仓库 | path（相对 `java/`） | 规则 |
| --- | --- | --- |
| `haixin-openspec` | `../haixin-openspec` | 始终加入 |
| `local-api-proxy` | `../local-api-proxy` | 含 Java 后端时加入 |

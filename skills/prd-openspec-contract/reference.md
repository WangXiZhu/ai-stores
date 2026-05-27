# OpenAPI 3.1 扩展锚点示例（非完整业务文档）

以下仅示意扩展字段的常见挂载位置；真实产出须按 PRD + 接口文档填满语义。

```yaml
openapi: 3.1.0
info:
  title: Example
  version: 0.0.0

x-workflows:
  import_create:
    steps:
      - upload_file
      - trigger_parse
      - poll_job_until_ready
      - validate_payload
      - create_resource

x-assumptions: []
x-open-questions: []

x-code-reuse:
  adaptExisting:
    - component: packages/example/ImportModal
      changes: []
  greenfield:
    - module: NewResultPanel
      rationale: ""

paths:
  /files/upload:
    post:
      operationId: upload_file
      x-ui-side-effects:
        onSuccess:
          disable: [submitUntilHash]
        onModalClose:
          resetForm: true
      responses:
        "200":
          description: ok

  /jobs/{jobId}:
    get:
      operationId: poll_job_until_ready
      x-polling:
        intervalMs: 1000
        timeoutMs: 60000
        terminalStatuses: [SUCCEEDED, FAILED]
        backoff: exponential

components:
  schemas:
    JobStatus:
      type: string
      enum: [PENDING, RUNNING, SUCCEEDED, FAILED]
      x-state-ui-mapping:
        PENDING: { label: 处理中, spinners: [global] }
        RUNNING: { label: 解析中, disableActions: [save] }
        SUCCEEDED: { label: 完成, toast: success }
        FAILED: { label: 失败, toast: error }
```

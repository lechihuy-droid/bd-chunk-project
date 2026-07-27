# Infrastructure and Deployment

> Superseded by `../../design/D07_DEPLOYMENT_SLO_AND_OPERATIONS.md`.

**Document type:** Cross-cutting Design  
**Version:** 0.1

## 1. MVP

```mermaid
flowchart TB
    UI[Web UI] --> API[Backend API]
    API --> DB[(PostgreSQL)]
    API --> Q[Redis / Queue]
    Q --> W1[API Worker]
    Q --> W2[CLI Worker]
    API --> OBJ[(Object Storage)]
    API --> EVT[SSE / WebSocket]
    W1 --> MODELS[Model APIs]
    W2 --> CLI[CLI Sandbox]
```

Thành phần tối thiểu: backend, PostgreSQL, queue, API worker, CLI worker, object storage, secret manager, logs và reverse proxy.

## 2. Production

```mermaid
flowchart TB
    CDN[CDN/WAF] --> GW[API Gateway]
    GW --> API[Application Service]
    API --> PG[(Managed PostgreSQL)]
    API --> MQ[Message Queue]
    MQ --> APIW[API Executor Pool]
    MQ --> CLIW[CLI Executor Pool]
    API --> OBJ[(Object Storage)]
    API --> CACHE[(Redis)]
    API --> OBS[Observability]
```

## 3. Deployment units

`harness-api`, `runtime-worker`, `api-executor-worker`, `cli-executor-worker`, `event-stream-service`.

## 4. Storage

PostgreSQL cho state/metadata, object storage cho artifact/log lớn, Redis cho queue/lock/cache, secret manager cho credential.

## 5. Environments

`local`, `development`, `staging`, `production`; mỗi môi trường có secret, provider và workspace isolation riêng.

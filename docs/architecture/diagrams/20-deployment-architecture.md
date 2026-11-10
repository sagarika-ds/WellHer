# Diagram 20: Deployment Architecture

> **Implementation status:** Configuration written (Compose, nginx, Prometheus, CI); not executed in the authoring sandbox.

## Diagram source (Mermaid)

```mermaid
flowchart TB
    DEVR["Developer push"] --> GHA["GitHub Actions<br/>lint, test, build"]
    GHA --> ECR["Container registry (ECR)"]
    GHA --> EAS["EAS Build<br/>Android AAB / iOS IPA"]
    EAS --> PLAY["Play Console"]
    EAS --> TF["TestFlight"]
    subgraph AWS["AWS"]
        subgraph EC2["EC2 host with Docker Compose"]
            NG["Nginx + TLS"]
            BE["backend"]
            WK["worker"]
            ML["ml-engine"]
            QDR["qdrant"]
            MLF["mlflow"]
            PRO["prometheus + grafana"]
        end
        RDS[("RDS PostgreSQL")]
        S3[("S3 bucket")]
        SM["Secrets Manager / KMS"]
    end
    ECR --> EC2
    NG --> BE
    BE --> RDS
    BE --> S3
    BE --> ML
    ML --> QDR
    ML --> MLF
    SM -.-> BE
    PHONE["User phone"] -->|HTTPS| NG
```

## Components

- **GitHub Actions**: CI (lint, tests, image build) and deploy.
- **EAS Build**: Cloud builds of Android AAB/APK and iOS IPA without a local Mac.
- **EC2 + Docker Compose**: Single host for the demo-scale deployment; ml-engine/qdrant/mlflow stay on the internal network.
- **RDS PostgreSQL**: Managed database with encryption at rest and backups.
- **S3**: Encrypted report storage.
- **Secrets Manager / KMS**: Source of secrets and encryption keys in production.

## Data flow

Push -> CI -> images to registry -> deploy on EC2; mobile builds go through EAS to Play/TestFlight. Phones reach only Nginx.

## Technologies and why they were selected

- **Docker Compose**: Simple, reproducible; ECS/EKS only if scale requires.
- **Terraform or CloudFormation (planned)**: Reproducible infrastructure.

## Communication with other modules

Public: HTTPS to Nginx. Everything else private.

## Security considerations

Security groups allow only 80/443; RDS private subnet; no secrets in images; TLS via ACM/Let's Encrypt.

## Real-world execution example

Merge to main -> tests pass -> new backend image deployed with a rolling container restart; health endpoint confirms.

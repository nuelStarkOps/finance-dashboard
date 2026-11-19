# Infrastructure (Phase 8)

This directory will hold the Terraform configuration for AWS deployment,
organised as reusable modules plus per-environment overrides:

```
infrastructure/
└── terraform/
    ├── modules/        # networking, database, ecs, storage, monitoring, identity
    ├── environments/   # dev, staging, production
    └── providers.tf
```

Deployment (Phase 8) targets: VPC (public/private subnets), ECS Fargate, ECR,
RDS PostgreSQL, Cognito, S3, CloudWatch, and Secrets Manager.

Nothing in this directory is provisioned during Phase 0; local development uses
`docker-compose.yml` at the repository root.

---
name: aws-serverless-deployment
description: AWS serverless deployment patterns for Python APIs, React PWAs, and background services. Use when deploying Lambda functions (Python/Node), API Gateway REST APIs, ECS Fargate services, static React apps (S3 + CloudFront), RDS databases, or scheduled jobs (EventBridge). Covers AWS CDK (TypeScript/Python), CloudFormation, IAM roles, Secrets Manager, VPC configuration, and cost optimization strategies for serverless architectures.
---

# AWS Serverless Deployment

Deployment patterns for Python APIs, React PWAs, and background services on AWS.

## When to Use This Skill

Use this skill for deploying:
- **Python Lambda Functions**: FastAPI, Flask, or standalone functions
- **React PWAs**: S3 + CloudFront static hosting
- **Background Services**: ECS Fargate long-running tasks
- **Scheduled Jobs**: EventBridge + Lambda
- **Databases**: RDS PostgreSQL, Aurora Serverless
- **APIs**: API Gateway (REST/HTTP)
- **Infrastructure as Code**: CDK or CloudFormation

## Architecture Patterns

### Pattern 1: React PWA + Lambda API

```
React PWA (S3 + CloudFront)
    ↓ HTTPS
API Gateway (REST)
    ↓
Lambda (Python FastAPI)
    ↓
RDS PostgreSQL
```

**Use for**: Web applications with serverless backend

→ **See**: [patterns/pwa-api-pattern.md](patterns/pwa-api-pattern.md)

### Pattern 2: CLI + ECS Scheduled Sync

```
EventBridge Rule (cron)
    ↓
ECS Fargate Task (Python CLI)
    ↓
External API (NetSuite)
    ↓
RDS PostgreSQL
```

**Use for**: Scheduled data synchronization, ETL jobs

→ **See**: [patterns/scheduled-sync-pattern.md](patterns/scheduled-sync-pattern.md)

### Pattern 3: Serverless Data Pipeline

```
S3 Upload Event
    ↓
Lambda (Process file)
    ↓
SQS Queue
    ↓
Lambda (Transform)
    ↓
RDS PostgreSQL
```

**Use for**: Event-driven data processing

→ **See**: [patterns/data-pipeline-pattern.md](patterns/data-pipeline-pattern.md)

## AWS Services

### Lambda Functions

**When to use:**
- Short-lived operations (<15 min)
- Event-driven processing
- REST API endpoints
- Scheduled jobs (simple)

**Python Lambda:**
```python
# handler.py
import json
from typing import Any

def lambda_handler(event: dict[str, Any], context: Any) -> dict:
    """Lambda entry point."""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Success'})
    }
```

**FastAPI on Lambda:**
```python
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/vendors")
def get_vendors():
    return {"vendors": []}

# Mangum adapter for Lambda
handler = Mangum(app)
```

→ **See**: [reference/lambda-patterns.md](reference/lambda-patterns.md)

### ECS Fargate

**When to use:**
- Long-running services (>15 min)
- Containerized applications
- Existing CLI tools
- Background workers
- Stateful processes

**Task Definition:**
```json
{
  "family": "vendor-sync",
  "taskRoleArn": "arn:aws:iam::...:role/VendorSyncTaskRole",
  "executionRoleArn": "arn:aws:iam::...:role/ECSTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [{
    "name": "vendor-analysis",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/vendor-analysis:latest",
    "command": ["uv", "run", "vendor-analysis", "sync"],
    "environment": [
      {"name": "CONFIG_PATH", "value": "/app/config.yaml"}
    ],
    "secrets": [
      {"name": "NS_CLIENT_ID", "valueFrom": "arn:aws:secretsmanager:..."},
      {"name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/vendor-sync",
        "awslogs-region": "us-east-1"
      }
    }
  }],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
```

→ **See**: [reference/ecs-fargate.md](reference/ecs-fargate.md)

### S3 + CloudFront (React PWA)

**Static Hosting Pattern:**
```bash
# Build React app
npm run build

# Sync to S3
aws s3 sync dist/ s3://my-app-bucket/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890 \
  --paths "/*"
```

**CloudFront Configuration:**
- HTTPS required (PWA requirement)
- Gzip/Brotli compression
- Cache headers for service worker
- Custom error pages (404 → index.html for SPA routing)

→ **See**: [reference/s3-cloudfront.md](reference/s3-cloudfront.md)

### RDS PostgreSQL

**Configuration:**
- Instance size: db.t3.micro (dev), db.t3.small (prod)
- Multi-AZ for production
- Automated backups
- Parameter groups for tuning

**Security:**
- Security groups (restrict to VPC)
- Encryption at rest
- SSL connections required
- Secrets Manager for credentials

→ **See**: [reference/rds-postgresql.md](reference/rds-postgresql.md)

### API Gateway

**REST API Configuration:**
```yaml
Resources:
  VendorAPI:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: vendor-api

  VendorsResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref VendorAPI
      ParentId: !GetAtt VendorAPI.RootResourceId
      PathPart: vendors

  VendorsMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref VendorAPI
      ResourceId: !Ref VendorsResource
      HttpMethod: GET
      AuthorizationType: AWS_IAM
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${VendorFunction.Arn}/invocations
```

→ **See**: [reference/api-gateway.md](reference/api-gateway.md)

### EventBridge (Scheduled Jobs)

**Cron Pattern:**
```yaml
Resources:
  VendorSyncRule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: "cron(0 2 * * ? *)"  # 2 AM UTC daily
      State: ENABLED
      Targets:
        - Arn: !GetAtt VendorSyncTask.Arn
          RoleArn: !GetAtt EventBridgeRole.Arn
          EcsParameters:
            TaskDefinitionArn: !Ref VendorSyncTaskDef
            LaunchType: FARGATE
            NetworkConfiguration:
              AwsvpcConfiguration:
                Subnets:
                  - !Ref PrivateSubnet
                SecurityGroups:
                  - !Ref TaskSecurityGroup
```

→ **See**: [reference/eventbridge.md](reference/eventbridge.md)

### Secrets Manager

**Store Credentials:**
```bash
# Create secret
aws secretsmanager create-secret \
  --name /vendor-analysis/netsuite \
  --secret-string '{
    "NS_CLIENT_ID": "...",
    "NS_CLIENT_SECRET": "...",
    "NS_ACCOUNT_ID": "610574"
  }'

# Access from Lambda
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

→ **See**: [reference/secrets-manager.md](reference/secrets-manager.md)

## Infrastructure as Code

### AWS CDK (TypeScript)

**Recommended for:**
- Type-safe infrastructure
- Reusable constructs
- Good IDE support
- Large applications

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

export class VendorAPIStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Lambda function
    const vendorFunction = new lambda.Function(this, 'VendorFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('lambda'),
      environment: {
        DB_HOST: 'db.example.com'
      }
    });

    // API Gateway
    const api = new apigateway.RestApi(this, 'VendorAPI');
    api.root.addResource('vendors').addMethod('GET',
      new apigateway.LambdaIntegration(vendorFunction)
    );
  }
}
```

→ **See**: [reference/aws-cdk.md](reference/aws-cdk.md)

### CloudFormation (YAML)

**Recommended for:**
- Simpler deployments
- Template reuse
- AWS-native

→ **See**: [reference/cloudformation.md](reference/cloudformation.md)

## Deployment Workflows

### React PWA Deployment

```bash
#!/bin/bash
# deploy-pwa.sh

set -e  # Fail fast

# Build
cd apps/vendor-dashboard
npm run build

# Deploy to S3
aws s3 sync dist/ s3://vendor-dashboard-prod/ \
  --delete \
  --cache-control "public,max-age=31536000,immutable"

# Invalidate CloudFront
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Aliases.Items[?contains(@, 'vendors.pdi.internal')]].Id" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "✓ PWA deployed"
```

### Lambda Deployment

```bash
#!/bin/bash
# deploy-lambda.sh

set -e

# Package dependencies
cd apps/vendor-api
pip install -r requirements.txt -t package/
cp handler.py package/

# Create ZIP
cd package
zip -r ../function.zip .

# Update Lambda
aws lambda update-function-code \
  --function-name vendor-api \
  --zip-file fileb://../function.zip

echo "✓ Lambda deployed"
```

### ECS Deployment

```bash
#!/bin/bash
# deploy-ecs.sh

set -e

# Build Docker image
cd apps/vendor-analysis
docker build -t vendor-analysis .

# Tag and push to ECR
ECR_REPO=123456789.dkr.ecr.us-east-1.amazonaws.com/vendor-analysis
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REPO
docker tag vendor-analysis:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Update ECS service (rolling deployment)
aws ecs update-service \
  --cluster vendor-cluster \
  --service vendor-sync-service \
  --force-new-deployment

echo "✓ ECS service updated"
```

## Cost Optimization

### Lambda
- Right-size memory (CPU scales with memory)
- Use ARM Graviton2 (20% cheaper)
- Set appropriate timeout (don't pay for hung functions)
- Use provisioned concurrency only if needed

### ECS Fargate
- Use Fargate Spot for non-critical tasks (70% cheaper)
- Right-size CPU/memory
- Use ARM for compatible workloads
- Auto-scaling policies

### S3 + CloudFront
- Intelligent-Tiering storage class
- Lifecycle policies for old versions
- CloudFront edge caching (reduce S3 requests)

### RDS
- Use Aurora Serverless v2 for variable load
- Stop dev instances when not in use
- Use reserved instances for production
- Read replicas only if needed

→ **See**: [reference/cost-optimization.md](reference/cost-optimization.md)

## Security Best Practices

### IAM Roles
- Principle of least privilege
- Separate roles per service
- No hardcoded credentials
- Use AssumeRole for cross-account

### Network Security
- Private subnets for databases
- NAT Gateway for outbound only
- Security groups (not NACL rules)
- VPC endpoints for AWS services

### Secrets
- Secrets Manager (not environment variables)
- Rotate credentials automatically
- Encrypt at rest
- Audit access with CloudTrail

→ **See**: [reference/security.md](reference/security.md)

## Monitoring & Observability

### CloudWatch
- Log groups per service
- Metrics and alarms
- Dashboards
- Insights queries

### X-Ray
- Distributed tracing
- Performance analysis
- Error tracking

### Cost Explorer
- Daily cost monitoring
- Budget alerts
- Resource tagging for attribution

→ **See**: [reference/monitoring.md](reference/monitoring.md)

## Complete Examples

### Full Stack Deployment
→ **See**: [examples/fullstack-deployment.md](examples/fullstack-deployment.md)

Complete CDK application:
- React PWA on S3 + CloudFront
- Python Lambda API
- RDS PostgreSQL
- Secrets Manager
- EventBridge scheduling

### Python CLI on ECS
→ **See**: [examples/cli-on-ecs.md](examples/cli-on-ecs.md)

Deploy vendor-analysis CLI:
- Dockerfile for UV + Python 3.12
- ECS task definition
- EventBridge schedule
- Secrets Manager integration
- CloudWatch logging

## CI/CD Patterns

### GitHub Actions
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789:role/GitHubActions
          aws-region: us-east-1

      - name: Deploy with CDK
        run: |
          npm install -g aws-cdk
          cd infrastructure
          cdk deploy --require-approval never
```

→ **See**: [reference/cicd.md](reference/cicd.md)

## Regional Deployment

**Single Region (Simple):**
- Deploy all resources in one region
- Lower complexity
- Regional failure risk

**Multi-Region (Advanced):**
- Route 53 health checks + failover
- Cross-region replication
- Global CloudFront distribution
- Higher cost and complexity

## Best Practices

### 1. Infrastructure as Code
- Version control all infrastructure
- Use CDK for type safety
- Environment-specific stacks (dev, staging, prod)
- Tag all resources for cost tracking

### 2. Deployment Strategy
- Blue/green for zero downtime
- Canary deployments for gradual rollout
- Rollback plans for failures
- Health checks before traffic shift

### 3. Environment Management
- Separate AWS accounts per environment
- Use AWS Organizations
- Consistent naming conventions
- Parameter Store for config

### 4. Cost Management
- Set budget alerts
- Tag resources by project/team
- Review costs monthly
- Use Savings Plans for predictable workloads

### 5. Security
- Enable CloudTrail
- VPC Flow Logs
- GuardDuty for threat detection
- Regular security audits

## Troubleshooting

### Lambda Issues
- Check CloudWatch Logs
- Verify IAM permissions
- Check timeout settings
- Monitor memory usage

### ECS Issues
- Check task logs in CloudWatch
- Verify task role permissions
- Check security group rules
- Monitor task health

### CloudFront Issues
- Check origin access
- Verify SSL certificates
- Review cache behaviors
- Check invalidation status

## Quick Reference

### Common AWS CLI Commands
```bash
# Lambda
aws lambda invoke --function-name my-function output.json
aws lambda get-function --function-name my-function

# ECS
aws ecs list-tasks --cluster my-cluster
aws ecs describe-tasks --cluster my-cluster --tasks task-id

# S3
aws s3 ls s3://my-bucket/
aws s3 cp file.txt s3://my-bucket/

# CloudFront
aws cloudfront create-invalidation --distribution-id ID --paths "/*"

# Secrets Manager
aws secretsmanager get-secret-value --secret-id my-secret

# RDS
aws rds describe-db-instances
aws rds create-db-snapshot --db-instance-identifier my-db
```

---

*Use this skill for deploying Python APIs, React PWAs, and serverless applications on AWS infrastructure.*

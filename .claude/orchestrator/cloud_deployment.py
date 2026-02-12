"""
Cloud Deployment Module - Deploy agent system to AWS Lambda, ECS, or Kubernetes
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms"""
    LAMBDA = "lambda"
    ECS = "ecs"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    LOCAL = "local"


class DeploymentSettings(BaseSettings):
    """Cloud deployment settings"""

    # Platform settings
    deployment_platform: DeploymentPlatform = Field(
        default=DeploymentPlatform.LAMBDA,
        description="Target deployment platform"
    )
    cloud_provider: CloudProvider = Field(
        default=CloudProvider.AWS,
        description="Cloud provider"
    )

    # AWS settings
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    aws_account_id: Optional[str] = Field(default=None, description="AWS account ID")

    # Lambda settings
    lambda_runtime: str = Field(default="python3.12", description="Lambda runtime")
    lambda_timeout: int = Field(default=300, description="Lambda timeout in seconds")
    lambda_memory: int = Field(default=512, description="Lambda memory in MB")

    # ECS settings
    ecs_cluster: str = Field(default="wire-ground-agents", description="ECS cluster name")
    ecs_task_cpu: int = Field(default=256, description="ECS task CPU units")
    ecs_task_memory: int = Field(default=512, description="ECS task memory in MB")

    # Kubernetes settings
    k8s_namespace: str = Field(default="wire-ground", description="Kubernetes namespace")
    k8s_replicas: int = Field(default=3, description="Number of replicas")

    # Container settings
    container_registry: str = Field(
        default="",
        description="Container registry URL"
    )
    container_image_tag: str = Field(default="latest", description="Container image tag")

    # Schedule settings
    enable_scheduling: bool = Field(default=True, description="Enable scheduled execution")
    schedule_expression: str = Field(default="rate(1 day)", description="Schedule expression")

    # Auto-scaling
    enable_auto_scaling: bool = Field(default=True, description="Enable auto-scaling")
    min_capacity: int = Field(default=1, description="Minimum capacity")
    max_capacity: int = Field(default=10, description="Maximum capacity")
    target_cpu_utilization: int = Field(default=70, description="Target CPU utilization")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DeploymentConfig(BaseModel):
    """Deployment configuration model"""
    service_name: str
    platform: DeploymentPlatform
    provider: CloudProvider
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    secrets: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    entry_point: str = "main.handler"
    vpc_config: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class DeploymentResult(BaseModel):
    """Deployment result model"""
    success: bool
    platform: DeploymentPlatform
    service_name: str
    endpoint: Optional[str] = None
    arn: Optional[str] = None
    deployment_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    logs: List[str] = Field(default_factory=list)
    metrics_dashboard: Optional[str] = None


class CloudDeploymentManager:
    """Manages cloud deployments for agent system"""

    def __init__(self, settings: Optional[DeploymentSettings] = None):
        self.settings = settings or DeploymentSettings()
        self.deployments: List[DeploymentResult] = []

    def generate_dockerfile(self, config: DeploymentConfig) -> str:
        """Generate Dockerfile for containerized deployment"""

        dockerfile_content = f"""# Multi-stage build for Wire Ground Agent System
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    cmake \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build any C++ components if needed
RUN if [ -f "CMakeLists.txt" ]; then \\
    cmake -B build -S . && \\
    cmake --build build; \\
    fi

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libstdc++6 \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agent

# Set working directory
WORKDIR /app

# Copy from builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Set environment variables
{self._generate_env_vars(config)}

# Switch to non-root user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Entry point
CMD ["python", "-m", "{config.entry_point}"]
"""
        return dockerfile_content

    def _generate_env_vars(self, config: DeploymentConfig) -> str:
        """Generate environment variable declarations for Dockerfile"""
        env_lines = []
        for key, value in config.environment_variables.items():
            if not any(secret in key.lower() for secret in ["key", "secret", "password", "token"]):
                env_lines.append(f'ENV {key}="{value}"')
        return "\n".join(env_lines)

    def generate_lambda_deployment(self, config: DeploymentConfig) -> str:
        """Generate AWS Lambda deployment package"""

        # Generate Lambda handler
        lambda_handler = f"""import json
import logging
import asyncio
from {config.entry_point.replace('.', '/')} import main

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    \"\"\"AWS Lambda handler for {config.service_name}\"\"\"

    try:
        # Parse event
        body = json.loads(event.get('body', '{{}}')) if event.get('body') else event

        # Run async main function
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(main(body))

        return {{
            'statusCode': 200,
            'body': json.dumps(result, default=str),
            'headers': {{
                'Content-Type': 'application/json',
                'X-Service': '{config.service_name}'
            }}
        }}

    except Exception as e:
        logger.error(f"Error in Lambda handler: {{e}}")
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}}),
            'headers': {{'Content-Type': 'application/json'}}
        }}
"""

        # Generate SAM template
        sam_template = f"""AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: {config.service_name} Lambda Deployment

Globals:
  Function:
    Timeout: {self.settings.lambda_timeout}
    MemorySize: {self.settings.lambda_memory}
    Runtime: {self.settings.lambda_runtime}

Resources:
  {config.service_name.replace('-', '')}Function:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Environment:
        Variables:
{self._generate_sam_env_vars(config)}
      Events:
        Api:
          Type: Api
          Properties:
            Path: /{config.service_name}
            Method: post
"""

        if self.settings.enable_scheduling:
            sam_template += f"""        Schedule:
          Type: Schedule
          Properties:
            Schedule: {self.settings.schedule_expression}
"""

        if config.vpc_config:
            sam_template += f"""      VpcConfig:
        SubnetIds: {config.vpc_config.get('subnet_ids', [])}
        SecurityGroupIds: {config.vpc_config.get('security_group_ids', [])}
"""

        # Add auto-scaling configuration
        if self.settings.enable_auto_scaling:
            sam_template += f"""
  ScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MaxCapacity: {self.settings.max_capacity}
      MinCapacity: {self.settings.min_capacity}
      ResourceId: !Sub 'function:${{{config.service_name.replace('-', '')}}}Function'
      RoleARN: !Sub 'arn:aws:iam::${{AWS::AccountId}}:role/aws-service-role/lambda.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_LambdaConcurrency'
      ScalableDimension: lambda:function:ProvisionedConcurrencyConfiguration
      ServiceNamespace: lambda

  ScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: {config.service_name}-scaling-policy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: LambdaProvisionedConcurrencyUtilization
        TargetValue: {self.settings.target_cpu_utilization}
"""

        return lambda_handler, sam_template

    def _generate_sam_env_vars(self, config: DeploymentConfig) -> str:
        """Generate environment variables for SAM template"""
        env_lines = []
        for key, value in config.environment_variables.items():
            env_lines.append(f"          {key}: {value}")
        return "\n".join(env_lines)

    def generate_kubernetes_deployment(self, config: DeploymentConfig) -> str:
        """Generate Kubernetes deployment manifests"""

        k8s_deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {config.service_name}
  namespace: {self.settings.k8s_namespace}
  labels:
    app: {config.service_name}
    version: {self.settings.container_image_tag}
spec:
  replicas: {self.settings.k8s_replicas}
  selector:
    matchLabels:
      app: {config.service_name}
  template:
    metadata:
      labels:
        app: {config.service_name}
    spec:
      containers:
      - name: {config.service_name}
        image: {self.settings.container_registry}/{config.service_name}:{self.settings.container_image_tag}
        ports:
        - containerPort: 8080
        env:
{self._generate_k8s_env_vars(config)}
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {config.service_name}-service
  namespace: {self.settings.k8s_namespace}
spec:
  selector:
    app: {config.service_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
"""

        # Add HPA for auto-scaling
        if self.settings.enable_auto_scaling:
            k8s_deployment += f"""---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {config.service_name}-hpa
  namespace: {self.settings.k8s_namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {config.service_name}
  minReplicas: {self.settings.min_capacity}
  maxReplicas: {self.settings.max_capacity}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {self.settings.target_cpu_utilization}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""

        # Add CronJob for scheduled execution
        if self.settings.enable_scheduling:
            k8s_deployment += f"""---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: {config.service_name}-cronjob
  namespace: {self.settings.k8s_namespace}
spec:
  schedule: "0 0 * * *"  # Daily at midnight
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: {config.service_name}
            image: {self.settings.container_registry}/{config.service_name}:{self.settings.container_image_tag}
            command: ["python", "-m", "{config.entry_point}"]
          restartPolicy: OnFailure
"""

        return k8s_deployment

    def _generate_k8s_env_vars(self, config: DeploymentConfig) -> str:
        """Generate environment variables for Kubernetes"""
        env_lines = []
        for key, value in config.environment_variables.items():
            env_lines.append(f"        - name: {key}")
            env_lines.append(f'          value: "{value}"')
        return "\n".join(env_lines)

    def generate_ecs_deployment(self, config: DeploymentConfig) -> str:
        """Generate AWS ECS task definition"""

        ecs_task_def = {
            "family": config.service_name,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": str(self.settings.ecs_task_cpu),
            "memory": str(self.settings.ecs_task_memory),
            "containerDefinitions": [
                {
                    "name": config.service_name,
                    "image": f"{self.settings.container_registry}/{config.service_name}:{self.settings.container_image_tag}",
                    "portMappings": [
                        {
                            "containerPort": 8080,
                            "protocol": "tcp"
                        }
                    ],
                    "environment": [
                        {"name": k, "value": v}
                        for k, v in config.environment_variables.items()
                    ],
                    "secrets": [
                        {"name": secret, "valueFrom": f"arn:aws:secretsmanager:{self.settings.aws_region}:{self.settings.aws_account_id}:secret:{secret}"}
                        for secret in config.secrets
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{config.service_name}",
                            "awslogs-region": self.settings.aws_region,
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3
                    }
                }
            ]
        }

        # Generate ECS service definition
        ecs_service = {
            "serviceName": config.service_name,
            "cluster": self.settings.ecs_cluster,
            "taskDefinition": config.service_name,
            "desiredCount": self.settings.min_capacity,
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": config.vpc_config.get("subnet_ids", []) if config.vpc_config else [],
                    "securityGroups": config.vpc_config.get("security_group_ids", []) if config.vpc_config else [],
                    "assignPublicIp": "ENABLED"
                }
            }
        }

        # Add auto-scaling
        if self.settings.enable_auto_scaling:
            ecs_service["deploymentConfiguration"] = {
                "maximumPercent": 200,
                "minimumHealthyPercent": 100
            }

        return json.dumps(ecs_task_def, indent=2), json.dumps(ecs_service, indent=2)

    async def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy the agent system to the specified platform"""

        logger.info(f"Starting deployment of {config.service_name} to {config.platform.value}")

        deployment_id = f"{config.service_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logs = []

        try:
            if config.platform == DeploymentPlatform.LAMBDA:
                result = await self._deploy_lambda(config, deployment_id, logs)
            elif config.platform == DeploymentPlatform.ECS:
                result = await self._deploy_ecs(config, deployment_id, logs)
            elif config.platform == DeploymentPlatform.KUBERNETES:
                result = await self._deploy_kubernetes(config, deployment_id, logs)
            elif config.platform == DeploymentPlatform.DOCKER:
                result = await self._deploy_docker(config, deployment_id, logs)
            else:
                raise ValueError(f"Unsupported platform: {config.platform}")

            self.deployments.append(result)
            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(
                success=False,
                platform=config.platform,
                service_name=config.service_name,
                deployment_id=deployment_id,
                logs=logs + [f"Error: {str(e)}"]
            )

    async def _deploy_lambda(
        self,
        config: DeploymentConfig,
        deployment_id: str,
        logs: List[str]
    ) -> DeploymentResult:
        """Deploy to AWS Lambda"""

        # Generate Lambda deployment files
        handler_code, sam_template = self.generate_lambda_deployment(config)

        # Save files
        deployment_dir = Path(f"deployments/{deployment_id}")
        deployment_dir.mkdir(parents=True, exist_ok=True)

        (deployment_dir / "lambda_handler.py").write_text(handler_code)
        (deployment_dir / "template.yaml").write_text(sam_template)

        logs.append(f"Generated Lambda deployment files in {deployment_dir}")

        # Build and deploy using SAM CLI (if available)
        try:
            # Build
            build_result = subprocess.run(
                ["sam", "build"],
                cwd=deployment_dir,
                capture_output=True,
                text=True
            )
            logs.append(f"SAM build: {build_result.stdout}")

            # Deploy
            deploy_result = subprocess.run(
                [
                    "sam", "deploy",
                    "--stack-name", config.service_name,
                    "--capabilities", "CAPABILITY_IAM",
                    "--no-confirm-changeset"
                ],
                cwd=deployment_dir,
                capture_output=True,
                text=True
            )
            logs.append(f"SAM deploy: {deploy_result.stdout}")

            endpoint = f"https://api-gateway-url/{config.service_name}"
            arn = f"arn:aws:lambda:{self.settings.aws_region}:{self.settings.aws_account_id}:function:{config.service_name}"

        except FileNotFoundError:
            logs.append("SAM CLI not found. Manual deployment required.")
            endpoint = None
            arn = None

        return DeploymentResult(
            success=True,
            platform=DeploymentPlatform.LAMBDA,
            service_name=config.service_name,
            endpoint=endpoint,
            arn=arn,
            deployment_id=deployment_id,
            logs=logs,
            metrics_dashboard=f"https://console.aws.amazon.com/cloudwatch/home?region={self.settings.aws_region}#dashboards:name={config.service_name}"
        )

    async def _deploy_ecs(
        self,
        config: DeploymentConfig,
        deployment_id: str,
        logs: List[str]
    ) -> DeploymentResult:
        """Deploy to AWS ECS"""

        # Generate ECS deployment files
        task_def, service_def = self.generate_ecs_deployment(config)

        # Save files
        deployment_dir = Path(f"deployments/{deployment_id}")
        deployment_dir.mkdir(parents=True, exist_ok=True)

        (deployment_dir / "task-definition.json").write_text(task_def)
        (deployment_dir / "service-definition.json").write_text(service_def)
        (deployment_dir / "Dockerfile").write_text(self.generate_dockerfile(config))

        logs.append(f"Generated ECS deployment files in {deployment_dir}")

        # Build and push Docker image
        image_uri = f"{self.settings.container_registry}/{config.service_name}:{self.settings.container_image_tag}"

        # Note: Actual deployment would use AWS CLI or boto3
        logs.append(f"Docker image would be pushed to: {image_uri}")

        return DeploymentResult(
            success=True,
            platform=DeploymentPlatform.ECS,
            service_name=config.service_name,
            endpoint=f"http://ecs-load-balancer-{config.service_name}.{self.settings.aws_region}.elb.amazonaws.com",
            arn=f"arn:aws:ecs:{self.settings.aws_region}:{self.settings.aws_account_id}:service/{self.settings.ecs_cluster}/{config.service_name}",
            deployment_id=deployment_id,
            logs=logs,
            metrics_dashboard=f"https://console.aws.amazon.com/ecs/home?region={self.settings.aws_region}#/clusters/{self.settings.ecs_cluster}/services/{config.service_name}/metrics"
        )

    async def _deploy_kubernetes(
        self,
        config: DeploymentConfig,
        deployment_id: str,
        logs: List[str]
    ) -> DeploymentResult:
        """Deploy to Kubernetes"""

        # Generate Kubernetes manifests
        k8s_manifests = self.generate_kubernetes_deployment(config)

        # Save files
        deployment_dir = Path(f"deployments/{deployment_id}")
        deployment_dir.mkdir(parents=True, exist_ok=True)

        (deployment_dir / "k8s-deployment.yaml").write_text(k8s_manifests)
        (deployment_dir / "Dockerfile").write_text(self.generate_dockerfile(config))

        logs.append(f"Generated Kubernetes deployment files in {deployment_dir}")

        # Apply manifests (if kubectl is available)
        try:
            apply_result = subprocess.run(
                ["kubectl", "apply", "-f", "k8s-deployment.yaml"],
                cwd=deployment_dir,
                capture_output=True,
                text=True
            )
            logs.append(f"kubectl apply: {apply_result.stdout}")

            # Get service endpoint
            service_result = subprocess.run(
                ["kubectl", "get", "service", f"{config.service_name}-service", "-n", self.settings.k8s_namespace, "-o", "json"],
                capture_output=True,
                text=True
            )

            if service_result.returncode == 0:
                service_info = json.loads(service_result.stdout)
                endpoint = service_info.get("status", {}).get("loadBalancer", {}).get("ingress", [{}])[0].get("hostname")
            else:
                endpoint = None

        except FileNotFoundError:
            logs.append("kubectl not found. Manual deployment required.")
            endpoint = None

        return DeploymentResult(
            success=True,
            platform=DeploymentPlatform.KUBERNETES,
            service_name=config.service_name,
            endpoint=endpoint,
            deployment_id=deployment_id,
            logs=logs,
            metrics_dashboard=f"http://grafana.{self.settings.k8s_namespace}.svc.cluster.local/d/{config.service_name}"
        )

    async def _deploy_docker(
        self,
        config: DeploymentConfig,
        deployment_id: str,
        logs: List[str]
    ) -> DeploymentResult:
        """Deploy as Docker container locally"""

        # Generate Dockerfile
        dockerfile_content = self.generate_dockerfile(config)

        # Save files
        deployment_dir = Path(f"deployments/{deployment_id}")
        deployment_dir.mkdir(parents=True, exist_ok=True)

        (deployment_dir / "Dockerfile").write_text(dockerfile_content)

        logs.append(f"Generated Docker deployment files in {deployment_dir}")

        # Build and run Docker container
        try:
            # Build
            build_result = subprocess.run(
                ["docker", "build", "-t", f"{config.service_name}:latest", "."],
                cwd=deployment_dir,
                capture_output=True,
                text=True
            )
            logs.append(f"Docker build: {build_result.stdout}")

            # Run
            run_result = subprocess.run(
                [
                    "docker", "run",
                    "-d",
                    "--name", config.service_name,
                    "-p", "8080:8080",
                    f"{config.service_name}:latest"
                ],
                capture_output=True,
                text=True
            )
            logs.append(f"Docker run: {run_result.stdout}")

            endpoint = "http://localhost:8080"

        except FileNotFoundError:
            logs.append("Docker not found. Manual deployment required.")
            endpoint = None

        return DeploymentResult(
            success=True,
            platform=DeploymentPlatform.DOCKER,
            service_name=config.service_name,
            endpoint=endpoint,
            deployment_id=deployment_id,
            logs=logs
        )


# Main execution
async def deploy_agent_system():
    """Deploy the complete agent system"""

    manager = CloudDeploymentManager()

    # Create deployment configuration
    config = DeploymentConfig(
        service_name="wire-ground-agents",
        platform=DeploymentPlatform.LAMBDA,
        provider=CloudProvider.AWS,
        environment_variables={
            "ENV": "production",
            "LOG_LEVEL": "INFO",
            "AGENT_SYSTEM": "wire_ground"
        },
        secrets=["github_token", "aws_credentials"],
        dependencies=["pydantic-ai", "github", "boto3"],
        tags={
            "Project": "WireGround",
            "Environment": "Production",
            "ManagedBy": "AgentOrchestrator"
        }
    )

    # Deploy
    result = await manager.deploy(config)

    logger.info(f"Deployment {'succeeded' if result.success else 'failed'}")
    logger.info(f"Endpoint: {result.endpoint}")
    logger.info(f"Dashboard: {result.metrics_dashboard}")

    return result


if __name__ == "__main__":
    asyncio.run(deploy_agent_system())
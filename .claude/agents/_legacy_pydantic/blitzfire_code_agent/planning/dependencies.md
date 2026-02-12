# Blitzfire Code Agent - Dependencies Configuration

## Environment Variables

### Core LLM Configuration
```bash
# Primary LLM provider
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1

# Alternative xAI integration (future)
XAI_API_KEY=your-xai-api-key-here
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-beta
```

### External Service Integration
```bash
# Godbolt Compiler Explorer
GODBOLT_BASE_URL=https://godbolt.org
GODBOLT_API_TIMEOUT=30
GODBOLT_CACHE_TTL=3600

# Docker Configuration
DOCKER_ENABLED=true
DOCKER_IMAGE=blitzfire/benchmark:latest
DOCKER_TIMEOUT=120
DOCKER_MEMORY_LIMIT=2g

# Project Integration
PROJECT_ROOT=/IdeaProjects/wire_ground
CLANG_TIDY_BINARY_PATH=/usr/bin/clang-tidy
CLANG_BINARY_PATH=/usr/bin/clang++
```

### Agent Behavior Configuration
```bash
# Optimization modes and defaults
BLITZFIRE_MODE=general  # general, hft, embedded, game
DEFAULT_ARCHITECTURE=x86_64
DEFAULT_OPTIMIZATION_LEVEL=-O3
SAFETY_LEVEL=high  # low, medium, high

# Performance and caching
ANALYSIS_CACHE_TTL=1800
BENCHMARK_CACHE_TTL=7200
MAX_CODE_SIZE=50000
MAX_ANALYSIS_TIME=30

# HFT-specific settings
HFT_AUDIT_LEVEL=comprehensive
HFT_OVERFLOW_CHECKS=true
HFT_RACE_DETECTION=true
```

## Python Dependencies (requirements.txt)

### Core Pydantic AI Framework
```
pydantic-ai>=0.0.14
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

### LLM Provider Support
```
openai>=1.52.0
anthropic>=0.36.0
google-generativeai>=0.8.0
httpx>=0.25.0
```

### Code Analysis and Processing
```
regex>=2023.10.3
pygments>=2.17.0
tree-sitter>=0.21.0
tree-sitter-cpp>=0.21.0
```

### External API Integration
```
requests>=2.31.0
aiohttp>=3.9.0
docker>=7.0.0
psutil>=5.9.0
```

### Performance and Benchmarking
```
numpy>=1.24.0
matplotlib>=3.7.0
pandas>=2.0.0
scipy>=1.11.0
```

### Development and Testing
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
black>=23.9.0
mypy>=1.6.0
```

## Dependency Classes

### BlitzfireConfig
```python
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class BlitzfireConfig(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_api_key: str = Field(..., description="API key for LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="Model name")
    llm_base_url: str = Field(default="https://api.openai.com/v1", description="LLM API base URL")

    # External Services
    godbolt_base_url: str = Field(default="https://godbolt.org", description="Godbolt API URL")
    godbolt_timeout: int = Field(default=30, description="Godbolt request timeout")
    docker_enabled: bool = Field(default=True, description="Enable Docker benchmarking")
    docker_timeout: int = Field(default=120, description="Docker execution timeout")

    # Optimization Settings
    blitzfire_mode: str = Field(default="general", description="Optimization mode")
    default_architecture: str = Field(default="x86_64", description="Target architecture")
    safety_level: str = Field(default="high", description="Safety constraint level")

    # Project Integration
    project_root: str = Field(default="/IdeaProjects/wire_ground", description="Project root path")
    clang_binary: str = Field(default="/usr/bin/clang++", description="Clang compiler path")
```

### AnalysisContext
```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class AnalysisContext:
    """Context for code analysis operations"""
    session_id: str
    project_root: str
    target_architecture: str = "x86_64"
    optimization_mode: str = "general"
    previous_analyses: Dict[str, any] = None
    performance_targets: Dict[str, float] = None
    safety_constraints: List[str] = None

    def __post_init__(self):
        if self.previous_analyses is None:
            self.previous_analyses = {}
        if self.performance_targets is None:
            self.performance_targets = {"target_speedup": 2.0}
        if self.safety_constraints is None:
            self.safety_constraints = ["no_ub", "memory_safe"]
```

### ExternalServices
```python
from dataclasses import dataclass
from typing import Optional
import docker
import requests

@dataclass
class ExternalServices:
    """External service connections and clients"""
    godbolt_session: requests.Session
    docker_client: Optional[docker.DockerClient] = None
    benchmark_cache: Dict[str, any] = None

    @classmethod
    def create(cls, config: BlitzfireConfig):
        godbolt_session = requests.Session()
        godbolt_session.timeout = config.godbolt_timeout

        docker_client = None
        if config.docker_enabled:
            try:
                docker_client = docker.from_env()
            except Exception:
                # Graceful fallback if Docker unavailable
                pass

        return cls(
            godbolt_session=godbolt_session,
            docker_client=docker_client,
            benchmark_cache={}
        )
```

## Service Integration Patterns

### Graceful Degradation
- **No Docker**: Disable benchmarking, provide estimates only
- **No Godbolt**: Use local compiler for assembly analysis
- **Network failures**: Use cached results when available
- **Resource constraints**: Scale down analysis complexity

### Caching Strategy
- **Analysis results**: Cache for 30 minutes to avoid reprocessing identical code
- **Benchmark results**: Cache for 2 hours since they're expensive to generate
- **Assembly outputs**: Cache for 1 hour based on code hash + compiler settings
- **Educational content**: Cache common explanations indefinitely

### Resource Management
- **Memory limits**: Process code in chunks if size exceeds limits
- **Timeout handling**: Graceful termination with partial results
- **Rate limiting**: Respect API limits for external services
- **Concurrent access**: Thread-safe caching and resource sharing

## Docker Environment Specification

### Benchmark Container Requirements
```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    clang-15 \
    cmake \
    ninja-build \
    libbenchmark-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy benchmark harness template
COPY benchmark_template.cpp /app/
WORKDIR /app

# Default compilation flags for consistency
ENV CXXFLAGS="-std=c++20 -O3 -march=native -DNDEBUG"
```

### Fallback Strategies
- **Local compilation**: Use system compiler if Docker unavailable
- **Estimation mode**: Provide theoretical analysis without empirical validation
- **Simplified benchmarking**: Basic timing instead of full Google Benchmark suite
- **Manual validation**: Guide user through manual optimization verification
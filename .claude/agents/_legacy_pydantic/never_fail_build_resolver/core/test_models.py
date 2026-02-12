"""Test and Function models for the Never Fail Build Resolver Agent."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .models import BuildAnalysis, ResolutionStrategy, ResolutionResult, ValidationResult

class BuildDiagnosisTestModel(BaseModel):
    """Model for testing build diagnosis functionality."""
    
    build_command: str = Field(..., description="Build command to test")
    expected_error_types: List[str] = Field(default_factory=list, description="Expected error categories")
    expected_severity: str = Field(default="medium", description="Expected error severity")
    timeout_seconds: int = Field(default=300, description="Test timeout")
    
    class Config:
        json_schema_extra = {
            "example": {
                "build_command": "cmake --build cmake-build-debug --target all",
                "expected_error_types": ["compilation", "linking"],
                "expected_severity": "high",
                "timeout_seconds": 300
            }
        }

class ResolutionTestModel(BaseModel):
    """Model for testing resolution strategies."""
    
    strategy_tier: str = Field(default="intelligent", description="Resolution tier to test")
    enable_backup: bool = Field(default=True, description="Enable backup during resolution")
    max_attempts: int = Field(default=3, description="Maximum resolution attempts")
    validation_required: bool = Field(default=True, description="Require validation after resolution")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_tier": "intelligent",
                "enable_backup": True,
                "max_attempts": 3,
                "validation_required": True
            }
        }

class ValidationTestModel(BaseModel):
    """Model for testing validation functionality."""
    
    original_command: str = Field(..., description="Original build command to validate")
    expected_success: bool = Field(default=True, description="Whether build should succeed")
    run_tests: bool = Field(default=True, description="Run test suite during validation")
    performance_check: bool = Field(default=False, description="Run performance checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_command": "cmake --build cmake-build-debug --target wire_ground_tests",
                "expected_success": True,
                "run_tests": True,
                "performance_check": False
            }
        }

# Function Models for different build resolution operations

class DiagnoseFunctionModel(BaseModel):
    """Function model for build diagnosis."""
    
    function_name: str = Field(default="diagnose_build_failure", description="Function name")
    description: str = Field(
        default="Diagnose build failures and analyze root causes comprehensively",
        description="Function description"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "build_command": {"type": "string", "description": "Build command that failed"},
            "working_directory": {"type": "string", "description": "Working directory for build"},
            "timeout_seconds": {"type": "integer", "description": "Timeout for diagnosis"}
        }
    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return {
            "name": self.function_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": ["build_command"]
            }
        }

class ResolveFunctionModel(BaseModel):
    """Function model for build resolution."""
    
    function_name: str = Field(default="execute_resolution", description="Function name")
    description: str = Field(
        default="Execute a resolution strategy to fix build failures",
        description="Function description"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "strategy_tier": {"type": "string", "enum": ["prevention", "intelligent", "comprehensive", "nuclear"]},
            "enable_backup": {"type": "boolean", "description": "Create backup before resolution"},
            "time_limit_seconds": {"type": "integer", "description": "Maximum time for resolution"}
        }
    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return {
            "name": self.function_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": ["strategy_tier"]
            }
        }

class ValidateFunctionModel(BaseModel):
    """Function model for build validation."""
    
    function_name: str = Field(default="validate_build_fix", description="Function name")
    description: str = Field(
        default="Validate that build problems have been resolved",
        description="Function description"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "original_build_command": {"type": "string", "description": "Original build command to test"},
            "working_directory": {"type": "string", "description": "Working directory for validation"},
            "run_full_tests": {"type": "boolean", "description": "Run complete test suite"}
        }
    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return {
            "name": self.function_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": ["original_build_command"]
            }
        }

class PreventionFunctionModel(BaseModel):
    """Function model for prevention rule creation."""
    
    function_name: str = Field(default="create_prevention_rules", description="Function name")
    description: str = Field(
        default="Create prevention rules to avoid future build failures",
        description="Function description"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "analysis_id": {"type": "string", "description": "ID of successful build analysis"},
            "strategy_id": {"type": "string", "description": "ID of successful resolution strategy"},
            "generalization_level": {"type": "string", "enum": ["specific", "moderate", "broad"]}
        }
    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return {
            "name": self.function_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": ["analysis_id", "strategy_id"]
            }
        }

class ArchonIntegrationFunctionModel(BaseModel):
    """Function model for Archon MCP integration."""
    
    function_name: str = Field(default="query_archon_knowledge", description="Function name")
    description: str = Field(
        default="Query Archon MCP server for build-related knowledge and examples",
        description="Function description"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "query": {"type": "string", "description": "Knowledge query for build issues"},
            "query_type": {"type": "string", "enum": ["rag_query", "code_examples", "task_management"]},
            "match_count": {"type": "integer", "description": "Number of matches to return", "default": 5}
        }
    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI function calling schema."""
        return {
            "name": self.function_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": ["query", "query_type"]
            }
        }

# Comprehensive test model for the entire agent
class NeverFailBuildResolverTestModel(BaseModel):
    """Comprehensive test model for the Never Fail Build Resolver Agent."""
    
    # Test scenarios
    test_scenarios: List[str] = Field(
        default_factory=lambda: [
            "compilation_errors",
            "linking_errors", 
            "dependency_conflicts",
            "configuration_issues",
            "system_environment_problems",
            "nuclear_reset_scenarios"
        ],
        description="Test scenarios to validate"
    )
    
    # Performance requirements
    max_diagnosis_time_seconds: int = Field(default=120, description="Maximum time for diagnosis")
    max_resolution_time_seconds: int = Field(default=600, description="Maximum time for resolution")
    min_success_rate: float = Field(default=0.85, description="Minimum success rate for resolutions")
    
    # Validation requirements
    require_backup_validation: bool = Field(default=True, description="Require backup validation")
    require_rollback_testing: bool = Field(default=True, description="Test rollback functionality")
    require_prevention_rules: bool = Field(default=True, description="Generate prevention rules")
    
    # Archon integration requirements
    require_archon_integration: bool = Field(default=True, description="Require Archon MCP integration")
    archon_knowledge_queries: List[str] = Field(
        default_factory=lambda: [
            "CMake build system troubleshooting",
            "C++ compilation error patterns",
            "Dependency resolution strategies",
            "Build system optimization techniques"
        ]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_scenarios": ["compilation_errors", "linking_errors"],
                "max_diagnosis_time_seconds": 120,
                "max_resolution_time_seconds": 600,
                "min_success_rate": 0.85,
                "require_backup_validation": True,
                "require_rollback_testing": True,
                "require_prevention_rules": True,
                "require_archon_integration": True
            }
        }
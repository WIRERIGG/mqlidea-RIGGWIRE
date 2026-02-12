"""
Blitzfire Code Agent - AI-Powered C++ Optimization Agent

A sophisticated agent that combines static code analysis, multi-tier optimization
strategies, assembly validation, and empirical benchmarking with an engaging
educational personality.

Key Features:
- Static code analysis for performance bottlenecks
- Multi-tier optimization strategies with quantified estimates
- Assembly validation using Godbolt Compiler Explorer
- Empirical benchmarking with Docker + Google Benchmark
- HFT specialization for financial trading code
- Interactive CLI with educational personality
"""

from .agent import BlitzfireCodeAgent, quick_analyze
from .models import (
    BlitzfireResponse, AnalysisResult, OptimizationStrategy,
    OptimizationTier, CodeIssue, BenchmarkResult,
    Architecture, OptimizationMode, SafetyLevel
)
from .settings import BlitzfireSettings, load_settings
from .providers import get_llm_model, get_test_model

# Version information
__version__ = "1.0.0"
__author__ = "Blitzfire Team"
__description__ = "AI-Powered C++ Optimization Agent"

# Main exports
__all__ = [
    # Main agent class
    "BlitzfireCodeAgent",

    # Convenience functions
    "quick_analyze",

    # Data models
    "BlitzfireResponse",
    "AnalysisResult",
    "OptimizationStrategy",
    "OptimizationTier",
    "CodeIssue",
    "BenchmarkResult",

    # Enums
    "Architecture",
    "OptimizationMode",
    "SafetyLevel",

    # Configuration
    "BlitzfireSettings",
    "load_settings",

    # LLM integration
    "get_llm_model",
    "get_test_model",
]

# Package metadata
__package_info__ = {
    "name": "blitzfire-code-agent",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "requires_python": ">=3.9",
    "keywords": ["c++", "optimization", "performance", "ai", "analysis"],
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
}
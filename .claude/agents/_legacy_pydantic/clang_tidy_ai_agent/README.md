# Clang-Tidy AI Agent

An intelligent automation system for comprehensive C++ code quality analysis and fixing using clang-tidy with AI-powered recommendations and learning capabilities.

## Features

- **Comprehensive Clang-Tidy Integration**: Support for 200+ clang-tidy checks across all major categories
- **AI-Powered Analysis**: Transform raw clang-tidy warnings into prioritized, actionable recommendations
- **Automated Fixing**: Safe application of 80%+ clang-tidy fixes with rollback capabilities
- **Learning System**: Adaptive patterns that reduce false positives and improve accuracy over time
- **Code Quality Assessment**: Meaningful quality metrics with improvement tracking
- **Build System Integration**: Seamless integration with CMake, Make, Bazel, and other build systems

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure clang-tidy is available
clang-tidy --version  # Should be 16.0+
```

### Basic Usage

```python
from clang_tidy_ai_agent import ClangTidyAgent
from clang_tidy_ai_agent.settings import ClangTidySettings

# Initialize agent
settings = ClangTidySettings()
agent = ClangTidyAgent(settings=settings)

# Analyze single file
result = await agent.analyze_file("src/main.cpp")

# Analyze entire project
project_analysis = await agent.analyze_project("./")
```

### Command Line Interface

```bash
# Analyze single file
python -m clang_tidy_ai_agent analyze --file src/main.cpp

# Analyze project with specific checks
python -m clang_tidy_ai_agent analyze --project ./ --checks "bugprone-*,cert-*"

# Apply safe fixes automatically
python -m clang_tidy_ai_agent fix --file src/main.cpp --safe-only
```

## Architecture

### Core Components

- **Agent Core** (`agent.py`): Main Pydantic AI agent with clang-tidy integration
- **Analysis Tools** (`tools.py`): Clang-tidy execution, parsing, and fix application
- **Learning System** (`dependencies.py`): SQLite-based pattern learning and preferences
- **Models** (`models.py`): Pydantic models for analysis results and configurations
- **Settings** (`settings.py`): Configuration management with check profiles

### Supported Check Categories

| Category | Focus | Example Checks |
|----------|-------|----------------|
| bugprone-* | Bug detection | Use-after-move, infinite loops, undefined behavior |
| cert-* | Security standards | CERT secure coding guidelines |
| cppcoreguidelines-* | Best practices | C++ Core Guidelines compliance |
| performance-* | Optimization | Unnecessary copies, inefficient algorithms |
| modernize-* | C++ modernization | Auto usage, range-based loops, smart pointers |
| readability-* | Code clarity | Naming conventions, function complexity |

## Configuration

### Environment Variables

```bash
# API Configuration
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Clang-Tidy Configuration
CLANG_TIDY_PATH=/usr/bin/clang-tidy
COMPILE_COMMANDS_PATH=./compile_commands.json

# Analysis Settings
MAX_ANALYSIS_TIME=1800
ENABLE_AUTO_FIX=true
ENABLE_LEARNING=true
```

### Settings File

```python
# settings.py configuration
class ClangTidySettings(BaseSettings):
    clang_tidy_path: str = "clang-tidy"
    compile_commands: str = "compile_commands.json"
    max_analysis_time: int = 1800
    enable_ai_analysis: bool = True
    learning_database: str = "clang_tidy_learning.db"
    check_filters: List[str] = []
```

## API Reference

### Core Methods

#### `analyze_file(file_path: str, **kwargs) -> FileAnalysisResult`

Perform comprehensive clang-tidy analysis on a single file.

**Parameters:**
- `file_path`: Path to C++ source file
- `checks`: Specific checks to run (e.g., "bugprone-*,cert-*")
- `fix_errors`: Whether to apply safe fixes
- `extra_args`: Additional clang-tidy arguments

**Returns:** `FileAnalysisResult` with warnings, fixes, and recommendations

#### `analyze_project(project_path: str, **kwargs) -> ProjectAnalysisResult`

Analyze entire project with clang-tidy.

**Parameters:**
- `project_path`: Path to project root
- `build_path`: Build directory with compile_commands.json
- `file_filter`: Filter for specific file patterns

**Returns:** `ProjectAnalysisResult` with project-wide quality metrics

#### `apply_fixes(analysis_result: AnalysisResult, **kwargs) -> FixApplicationResult`

Apply clang-tidy fixes with safety validation.

**Parameters:**
- `analysis_result`: Result from previous analysis
- `safe_only`: Only apply fixes marked as safe
- `backup`: Create backup before applying fixes

**Returns:** `FixApplicationResult` with applied changes and rollback information

### Models

```python
class ClangTidyWarning(BaseModel):
    check_name: str      # e.g., "bugprone-use-after-move"
    severity: str        # "error", "warning", "note"
    file_path: str       # Source file location
    line: int           # Line number
    column: int         # Column number
    message: str        # Warning description
    fix_available: bool # Whether automatic fix exists

class FileAnalysisResult(BaseModel):
    file_path: str
    total_warnings: int
    warnings: List[ClangTidyWarning]
    quality_score: float
    recommendations: List[str]
    applied_fixes: int
```

## Testing

The agent includes comprehensive testing following AI Agent Validator.md standards:

```bash
# Run all tests with coverage
pytest --cov=clang_tidy_ai_agent --cov-report=html

# Run specific test categories
pytest tests/test_security.py     # Security validation
pytest tests/test_performance.py # Performance benchmarks
pytest tests/test_integration.py # Integration tests
```

### Test Coverage

- ✅ ≥95% code coverage enforced
- ✅ Security injection testing for all input vectors
- ✅ Performance benchmarking for analysis operations
- ✅ Integration with real clang-tidy tools
- ✅ Property-based testing with Hypothesis

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Code Quality Analysis
  uses: ./clang-tidy-ai-agent
  with:
    project_path: "./"
    checks: "bugprone-*,cert-*,performance-*"
    apply_fixes: "safe"
    fail_on: "error"
```

### CMake Integration

```cmake
# Generate compile_commands.json
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Add custom target for code quality analysis
add_custom_target(code_quality
    COMMAND python -m clang_tidy_ai_agent analyze --project ${CMAKE_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
```

### Build System Integration

```bash
# Generate compile commands for different build systems

# CMake
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..

# Bear (for Make projects)
bear -- make

# Bazel
bazel run @hedron_compile_commands//:refresh_all
```

## Advanced Features

### Learning System

The agent learns from fix patterns and user preferences:

```python
# Enable learning for project-specific patterns
agent = ClangTidyAgent(enable_learning=True)

# Learn from successful fixes
await agent.learn_from_fix(warning, applied_fix, success=True)

# Adapt check priorities based on project patterns
priorities = await agent.get_learned_priorities()
```

### Custom Check Configuration

```python
# Configure specific checks for different file types
config = {
    "*.hpp": ["cppcoreguidelines-*", "modernize-*"],
    "test_*.cpp": ["bugprone-*"],
    "performance_*.cpp": ["performance-*"]
}

agent = ClangTidyAgent(check_configuration=config)
```

### Quality Metrics

```python
# Get detailed quality assessment
quality = await agent.assess_code_quality("src/")

print(f"Overall Quality Score: {quality.overall_score}")
print(f"Critical Issues: {quality.critical_count}")
print(f"Improvement Areas: {quality.recommendations}")
```

## Performance

- **Analysis Speed**: <30 seconds for typical single-file analysis
- **Fix Success Rate**: 80%+ of automatic fixes applied successfully
- **Learning Effectiveness**: 70%+ reduction in false positives after learning
- **Memory Usage**: <500MB during operation for large files

## Troubleshooting

### Common Issues

1. **compile_commands.json not found**: Ensure build system generates compilation database
2. **clang-tidy not found**: Install clang-tidy 16.0+ and ensure it's in PATH
3. **Analysis timeout**: Increase MAX_ANALYSIS_TIME for complex projects
4. **Fix application failures**: Use --safe-only flag for automatic fixes

### Debug Mode

```bash
# Enable detailed logging
export CLANG_TIDY_LOG_LEVEL=DEBUG
python -m clang_tidy_ai_agent analyze --file src/main.cpp --verbose
```

### Configuration Validation

```bash
# Validate configuration
python -m clang_tidy_ai_agent config validate

# Test clang-tidy installation
python -m clang_tidy_ai_agent config test-clang-tidy
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests following AI Agent Validator.md
4. Ensure ≥95% code coverage
5. Submit pull request with security validation

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: See `docs/` directory
- Issues: GitHub issue tracker
- Examples: See `examples/` directory
- API Reference: Generated with Sphinx
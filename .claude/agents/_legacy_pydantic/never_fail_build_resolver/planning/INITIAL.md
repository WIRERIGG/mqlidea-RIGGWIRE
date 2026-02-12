# Agent Requirements: NEVER FAIL BUILD RESOLVER

## Executive Summary
The NEVER FAIL BUILD RESOLVER is a mission-critical Pydantic AI agent that transforms the existing bash-based NEVER_FAIL_BUILD_WORKFLOW into an intelligent, autonomous Python system. This agent embodies the core principle: **"NEVER give up and ALWAYS find a solution to ANY build problem."** The system provides systematic C++ build problem resolution with machine learning capabilities and real-time adaptation.

## Agent Classification
- **Type**: Workflow Orchestration Agent with State Machine and Tool Integration
- **Complexity**: High (Enterprise-grade build resolution system)
- **Priority Features**: 
  1. Four-tier resolution strategy (fast → smart → thorough → emergency)
  2. Intelligent problem categorization and solution orchestration
  3. Real-time learning from resolution patterns

## Functional Requirements

### Core Functionality
1. **Comprehensive Build Problem Resolution**
   - Handle ALL categories: Compiler errors, linker errors, CMake issues, GoogleTest integration, system-level problems
   - Implement 4-tier escalation strategy with defined success criteria
   - **Acceptance Criteria**: 99.5+ % success rate across all problem categories

2. **State Machine Workflow Orchestration**
   - States: `IDLE` → `ANALYZING` → `CATEGORIZING` → `RESOLVING` → `VALIDATING` → `LEARNING`
   - Event-driven transitions with rollback capabilities for failed resolutions
   - Persistent state maintenance across resolution attempts with checkpoint system
   - **Acceptance Criteria**: Successful state transitions with complete rollback on failure

3. **Real-time Learning and Adaptation**
   - Track problem categories and successful resolution strategies
   - Update prevention measures based on recurring issues
   - Integrate new solution patterns into workflow automatically
   - **Acceptance Criteria**: 10% improvement in resolution time over 30-day period

4. **Integration with Existing Infrastructure**
   - Seamless integration with wire_ground project structure
   - Preserve existing CMake configurations and build targets
   - Support both CLI and programmatic invocation methods
   - **Acceptance Criteria**: Drop-in replacement for `./scripts/fix_build.sh`

### Input/Output Specifications
- **Input Types**: 
  - Build error logs and failure messages
  - Project directory paths and CMake configurations
  - Resolution mode selection (fast/smart/thorough/emergency)
- **Output Format**: Structured resolution reports with detailed action logs
- **Validation Requirements**: Complete build success with zero warnings

## Technical Requirements

### Model Configuration
- **Primary Model**: anthropic:claude-3-5-sonnet-20241022 (advanced reasoning for complex build problems)
- **Context Window Needs**: ~200K tokens for large codebase analysis and error log processing
- **State Persistence**: JSON-based state management with checkpoint recovery

### External Integrations
1. **CMake Build System**:
   - Purpose: Execute build commands with timeout and error capture
   - Integration: subprocess with async execution and comprehensive logging
   - Error Handling: Parse CMake output for specific error categorization

2. **Clang-Tidy Integration**:
   - Purpose: Automatic code quality issue resolution
   - Integration: Execute clang-tidy with fix application and validation
   - Error Handling: Safe application of fixes with backup and rollback

3. **GoogleTest Framework**:
   - Purpose: Test framework conflict resolution and integration validation
   - Integration: Detect mixed testing frameworks and convert to consistent approach
   - Error Handling: Handle illegal instruction errors and custom main() elimination

4. **System Environment Validation**:
   - Purpose: Validate and repair build environment dependencies
   - Integration: Check compilers, libraries, permissions, network connectivity
   - Error Handling: Automatic environment repair with fallback configurations

### Tool Requirements
1. **problem_analyzer**:
   - Purpose: Categorize and analyze build problems from error logs
   - Parameters: error_log (str), project_path (Path)
   - Error Handling: Fallback to generic problem handling on analysis failure

2. **cmake_resolver**:
   - Purpose: Execute CMake commands with intelligent error resolution
   - Parameters: build_command (str), working_dir (Path), timeout (int)
   - Error Handling: Progressive fallback strategies with cache clearing

3. **clang_tidy_fixer**:
   - Purpose: Apply clang-tidy fixes with safety validation
   - Parameters: file_path (Path), fix_categories (List[str])
   - Error Handling: Automatic backup and rollback on validation failure

4. **gtest_integrator**:
   - Purpose: Resolve GoogleTest integration conflicts
   - Parameters: test_files (List[Path]), target_framework (str)
   - Error Handling: Safe framework migration with comprehensive validation

5. **system_validator**:
   - Purpose: Validate and repair system build environment
   - Parameters: validation_type (str), repair_mode (bool)
   - Error Handling: Non-destructive validation with optional repair

## Dependencies and Environment

### API Keys and Credentials
- ANTHROPIC_API_KEY: Anthropic API key for Claude 3.5 Sonnet
- MCP_SERVER_URL: Archon MCP server endpoint (optional)

### Python Packages
- pydantic-ai (core framework)
- asyncio (async workflow orchestration)
- pathlib (file system operations)
- subprocess (command execution)
- json (state persistence)
- dataclasses (data models)
- python-dotenv (environment management)
- rich (CLI formatting and progress indicators)

### System Requirements
- Python version: 3.11+
- CMake 3.20+ (wire_ground build system)
- Clang/GCC compiler toolchain
- GoogleTest framework
- Network access for dependency fetching
- File system write permissions for backups

## Success Criteria
1. **Resolution Success Rate**: >99.5% across all resolution modes within defined time limits
2. **Mode Performance Targets**:
   - Fast mode: 90% success rate within 3 minutes
   - Smart mode: 99% success rate within 10 minutes  
   - Thorough mode: 99.9% success rate within 20 minutes
   - Emergency mode: 95% success rate within 2 minutes
3. **Learning Effectiveness**: 10% improvement in resolution time over 30-day period
4. **Integration Compatibility**: Complete drop-in replacement for existing bash workflows

## Security and Compliance
- **Command Execution Safety**: Sandboxed command execution with parameter validation
- **File System Safety**: Automatic backup before modifications with rollback capabilities
- **API Key Management**: Environment variables only, no hardcoded credentials
- **Error Logging**: Comprehensive audit trail without sensitive data exposure

## Testing Requirements
- **Unit Tests**: Individual tool functions, state machine transitions, problem categorization
- **Integration Tests**: End-to-end build problem resolution across all categories
- **Performance Tests**: Resolution time benchmarking under various failure scenarios
- **Regression Tests**: Automated validation against historical problem sets
- **State Recovery Tests**: Checkpoint system validation and rollback functionality

## Constraints and Limitations
- **Project Compatibility**: Must work with existing wire_ground CMake configuration
- **Command Safety**: No execution of untrusted commands or scripts
- **Resource Limits**: Memory usage capped at 2GB for large codebase analysis
- **Time Limits**: Hard timeout limits for each resolution mode to prevent infinite loops

## Future Enhancements (Optional)
- Multi-project build orchestration capabilities
- Advanced ML-based problem prediction and prevention
- Integration with CI/CD pipeline systems
- Real-time build performance monitoring and optimization
- Distributed build problem resolution across multiple agents

## Assumptions Made
1. **Build Environment**: Wire_ground project structure and CMake configuration stability
2. **Tool Availability**: CMake, clang-tidy, and compiler toolchain availability
3. **File Permissions**: Write access for backup creation and file modifications
4. **Network Access**: Ability to fetch dependencies and updates when needed
5. **API Access**: Stable Anthropic API access for LLM processing
6. **State Storage**: Local file system availability for state persistence

## Approval Checklist
- [x] All core requirements defined (resolution, orchestration, learning)
- [x] External dependencies identified (CMake, clang-tidy, GoogleTest)
- [x] Security considerations addressed (sandboxing, backups, API keys)
- [x] Testing strategy outlined (unit, integration, performance, regression)
- [x] Success criteria measurable (success rates, performance targets, learning effectiveness)
- [x] State machine architecture defined (workflow orchestration)
- [x] Tool integration specifications complete (comprehensive build problem handling)

---
Generated: 2025-09-01
Status: Ready for Component Development
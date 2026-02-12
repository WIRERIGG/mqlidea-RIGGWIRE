#!/bin/bash

# Claude Code Build Monitor Hook
# Automatically detects clang-tidy issues in build output and triggers clang-tidy-fixer

set -euo pipefail

PROJECT_ROOT="/IdeaProjects/wire_ground"
HOOK_DIR="$PROJECT_ROOT/.claude/hooks"
DETECTOR="$HOOK_DIR/clang_tidy_auto_detector.py"
CONFIG="$HOOK_DIR/auto_detect_config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[Build Monitor]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[Build Monitor]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[Build Monitor]${NC} $1"
}

log_error() {
    echo -e "${RED}[Build Monitor]${NC} $1"
}

# Function to monitor build command and detect issues
monitor_build() {
    local build_cmd=("$@")
    local temp_output=$(mktemp)
    local exit_code=0
    
    log "Monitoring build command: ${build_cmd[*]}"
    
    # Run build command and capture output
    if "${build_cmd[@]}" 2>&1 | tee "$temp_output"; then
        exit_code=0
        log_success "Build completed successfully"
    else
        exit_code=$?
        log_warning "Build completed with errors (exit code: $exit_code)"
    fi
    
    # Check for clang-tidy issues
    log "Analyzing build output for clang-tidy issues..."
    
    if python3 "$DETECTOR" --config "$CONFIG" --input "$temp_output" --json > /tmp/detection_result.json; then
        local issues_found=$(python3 -c "import json; data=json.load(open('/tmp/detection_result.json')); print(data['issues_found'])")
        local should_auto_fix=$(python3 -c "import json; data=json.load(open('/tmp/detection_result.json')); print(str(data['should_auto_fix']).lower())")
        
        if [[ "$issues_found" -gt 0 ]]; then
            log_warning "Found $issues_found clang-tidy issues"
            
            if [[ "$should_auto_fix" == "true" ]]; then
                log "🚀 Triggering automatic clang-tidy-fixer..."
                python3 "$DETECTOR" --config "$CONFIG" --input "$temp_output"
                log_success "Automatic fixing completed"
            else
                log "Issues detected but auto-fix threshold not met"
                log "Run manually: ./scripts/ai_clang_tidy.sh project"
            fi
        else
            log_success "No clang-tidy issues detected"
        fi
    else
        log_error "Failed to analyze build output"
    fi
    
    # Cleanup
    rm -f "$temp_output" /tmp/detection_result.json
    
    return $exit_code
}

# Function to monitor last build output from a log file or cached output
monitor_last_build_output() {
    log "Checking for recent build output..."
    
    # Look for recent cmake build outputs in common locations
    local build_log_paths=(
        "/tmp/last_build.log"
        "cmake-build-debug/build.log"
        "$HOME/.local/share/JetBrains/CLion/log/build.log"
    )
    
    local found_log=""
    
    # Check for most recent log file
    for log_path in "${build_log_paths[@]}"; do
        if [[ -f "$log_path" && -s "$log_path" ]]; then
            # Check if file was modified in the last 5 minutes
            if [[ $(find "$log_path" -newermt "5 minutes ago" 2>/dev/null) ]]; then
                found_log="$log_path"
                break
            fi
        fi
    done
    
    if [[ -n "$found_log" ]]; then
        log "Found recent build log: $found_log"
        analyze_build_output_file "$found_log"
    else
        log_warning "No recent build output found"
    fi
}

# Function to monitor build output from stdin
monitor_build_output_from_stdin() {
    log "Analyzing build output from stdin..."
    
    local temp_output=$(mktemp)
    cat > "$temp_output"
    
    analyze_build_output_file "$temp_output"
    
    # Cleanup
    rm -f "$temp_output"
}

# Function to analyze build output from a file
analyze_build_output_file() {
    local output_file="$1"
    
    log "Analyzing build output for clang-tidy issues..."
    
    if python3 "$DETECTOR" --config "$CONFIG" --input "$output_file" --json > /tmp/detection_result.json; then
        local issues_found=$(python3 -c "import json; data=json.load(open('/tmp/detection_result.json')); print(data['issues_found'])")
        local should_auto_fix=$(python3 -c "import json; data=json.load(open('/tmp/detection_result.json')); print(str(data['should_auto_fix']).lower())")
        
        if [[ "$issues_found" -gt 0 ]]; then
            log_warning "Found $issues_found clang-tidy issues"
            
            if [[ "$should_auto_fix" == "true" ]]; then
                log "🚀 Triggering automatic clang-tidy-fixer..."
                python3 "$DETECTOR" --config "$CONFIG" --input "$output_file"
                log_success "Automatic fixing completed"
            else
                log "Issues detected but auto-fix threshold not met"
                log "Run manually: ./scripts/ai_clang_tidy.sh project"
            fi
        else
            log_success "No clang-tidy issues detected"
        fi
    else
        log_error "Failed to analyze build output"
    fi
    
    # Cleanup
    rm -f /tmp/detection_result.json
}

# Function to install the hook
install_hook() {
    log "Installing Claude Code build monitor hook..."
    
    # Create hooks directory if it doesn't exist
    mkdir -p "$HOOK_DIR"
    
    # Create configuration if it doesn't exist
    if [[ ! -f "$CONFIG" ]]; then
        log "Creating default configuration..."
        cat > "$CONFIG" << 'EOF'
{
    "auto_fix_enabled": true,
    "max_warnings_threshold": 5,
    "critical_only_mode": false,
    "exclude_patterns": ["*test*", "*benchmark*"],
    "include_file_patterns": ["src/**/*.cpp", "include/**/*.hpp", "tests/**/*.cpp"],
    "auto_fix_timeout": 300,
    "session_persistence": true
}
EOF
    fi
    
    log_success "Hook installation completed"
    log "Configuration: $CONFIG"
    log "Detector: $DETECTOR"
}

# Function to test the system
test_detection() {
    log "Testing clang-tidy detection system..."
    
    # Create test build output with clang-tidy warnings
    local test_output=$(mktemp)
    cat > "$test_output" << 'EOF'
[100%] Building CXX object CMakeFiles/test.dir/src/main.cpp.o
/IdeaProjects/wire_ground/src/main.cpp:42:15: warning: variable 'unused_var' is not used [-Wunused-variable]
  int unused_var = 10;
      ^~~~~~~~~~
/IdeaProjects/wire_ground/src/main.cpp:58:23: warning: use of old-style cast [readability-old-style-cast]
  int result = (int)some_double;
               ^~~~~~~~~~~~~~~~
EOF
    
    log "Running detection on test output..."
    python3 "$DETECTOR" --config "$CONFIG" --input "$test_output" --dry-run
    
    rm -f "$test_output"
    log_success "Detection test completed"
}

# Function to show usage
show_usage() {
    cat << 'EOF'
Claude Code Build Monitor Hook

Usage:
    build_monitor.sh monitor <build_command...>   Monitor a build command
    build_monitor.sh install                      Install the hook system
    build_monitor.sh test                         Test detection system
    build_monitor.sh config                       Show current configuration

Examples:
    build_monitor.sh monitor cmake --build cmake-build-debug
    build_monitor.sh monitor make -j4
    build_monitor.sh install
    build_monitor.sh test

Integration with Claude Code:
    Add to .claude/settings.local.json:
    {
        "hooks": {
            "post-build": ".claude/hooks/build_monitor.sh monitor"
        }
    }
EOF
}

# Main command processing
case "${1:-}" in
    "monitor")
        shift
        if [[ $# -eq 0 ]]; then
            log_error "No build command specified"
            show_usage
            exit 1
        fi
        monitor_build "$@"
        ;;
    "monitor_last_build")
        monitor_last_build_output
        ;;
    "monitor_output")
        monitor_build_output_from_stdin
        ;;
    "install")
        install_hook
        ;;
    "test")
        test_detection
        ;;
    "config")
        if [[ -f "$CONFIG" ]]; then
            log "Current configuration:"
            cat "$CONFIG"
        else
            log_warning "Configuration file not found: $CONFIG"
        fi
        ;;
    "help"|"-h"|"--help"|"")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
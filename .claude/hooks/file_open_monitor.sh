#!/bin/bash

# Claude Code File Open Monitor
# Automatically checks for clang-tidy issues when files are opened in the editor

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
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[File Monitor]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[File Monitor]${NC} $1" >&2
}

# Function to check if file has clang-tidy issues
check_file_for_issues() {
    local file_path="$1"
    
    # Only check C/C++ files
    case "$file_path" in
        *.cpp|*.hpp|*.c|*.h|*.cc|*.cxx|*.hxx)
            ;;
        *)
            return 0  # Not a C++ file, skip
            ;;
    esac
    
    # Check if file is in project directory
    if [[ ! "$file_path" =~ ^$PROJECT_ROOT ]]; then
        return 0  # Not in project, skip
    fi
    
    log "🔍 Checking opened file: $(basename "$file_path")"
    
    # Run REAL clang-tidy check on the specific file
    local temp_output=$(mktemp)
    local build_dir="$PROJECT_ROOT/cmake-build-debug"
    
    if [[ -f "$file_path" ]]; then
        # Run actual clang-tidy with project's compilation database
        if [[ -f "$build_dir/compile_commands.json" ]]; then
            log "Running clang-tidy analysis..."
            
            # Run clang-tidy with timeout to prevent hanging
            timeout 15s clang-tidy "$file_path" -p="$build_dir" \
                --checks="*,-readability-else-after-return,-llvmlibc-*,-fuchsia-*,-android-*,-llvm-*,-altera-*,-darwin-*" \
                2>&1 > "$temp_output" || true
        else
            # Fallback: run without compile database
            timeout 15s clang-tidy "$file_path" \
                --checks="*,-readability-else-after-return,-llvmlibc-*,-fuchsia-*,-android-*,-llvm-*,-altera-*,-darwin-*" \
                2>&1 > "$temp_output" || true
        fi
        
        # Check if we found real clang-tidy issues
        if [[ -s "$temp_output" ]] && grep -q "warning:" "$temp_output"; then
            local issue_count=$(grep -c "warning:" "$temp_output" || echo "0")
            log_warning "🚨 Found $issue_count clang-tidy issues in opened file!"
            
            # Show some issues to user
            echo -e "${YELLOW}Sample issues found:${NC}" >&2
            head -10 "$temp_output" | grep -E "(warning|error):" | head -3 >&2
            
            # Automatically trigger clang-tidy-fixer
            log "🚀 Automatically triggering clang-tidy-fixer for opened file..."
            
            # Use the detector to trigger the AI fixer
            if python3 "$DETECTOR" --config "$CONFIG" --input "$temp_output"; then
                log "✅ Automatic fixing completed for opened file"
            else
                log_warning "⚠️  Auto-fix encountered issues. Manual intervention may be needed."
                log "Run manually: ./scripts/ai_clang_tidy.sh analyze \"$file_path\""
            fi
        else
            log "✅ No clang-tidy issues detected in opened file"
        fi
    fi
    
    rm -f "$temp_output"
}

# Main execution
main() {
    # Get the file path from environment or argument
    local file_path="${CLAUDE_FILE_PATH:-${1:-}}"
    
    if [[ -n "$file_path" ]]; then
        check_file_for_issues "$file_path"
    fi
}

main "$@"
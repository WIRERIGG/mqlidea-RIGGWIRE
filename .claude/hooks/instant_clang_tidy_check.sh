#!/bin/bash

# Instant Clang-Tidy Check for Opened Files
# Provides immediate feedback when files with issues are opened

set -euo pipefail

PROJECT_ROOT="/IdeaProjects/wire_ground"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to run instant clang-tidy check and fix
instant_check_and_fix() {
    local file_path="$1"
    
    # Validate input
    if [[ ! -f "$file_path" ]]; then
        echo -e "${RED}❌ File not found: $file_path${NC}"
        return 1
    fi
    
    # Only check C/C++ files
    case "$file_path" in
        *.cpp|*.hpp|*.c|*.h|*.cc|*.cxx|*.hxx)
            ;;
        *)
            echo -e "${BLUE}ℹ️  Skipping non-C++ file: $(basename "$file_path")${NC}"
            return 0
            ;;
    esac
    
    echo -e "${PURPLE}🔍 INSTANT CLANG-TIDY CHECK${NC}"
    echo -e "${BLUE}File: $(basename "$file_path")${NC}"
    echo ""
    
    # Quick clang-tidy analysis
    local temp_output=$(mktemp)
    local build_dir="$PROJECT_ROOT/cmake-build-debug"
    
    # Run clang-tidy with focused checks for speed
    echo -e "${YELLOW}Running clang-tidy analysis...${NC}"
    
    if [[ -f "$build_dir/compile_commands.json" ]]; then
        timeout 20s clang-tidy "$file_path" -p="$build_dir" \
            --checks="modernize-*,readability-*,performance-*,bugprone-*,cppcoreguidelines-*,misc-*,boost-use-ranges" \
            --quiet \
            2>&1 > "$temp_output" || true
    else
        timeout 20s clang-tidy "$file_path" \
            --checks="modernize-*,readability-*,performance-*,bugprone-*,cppcoreguidelines-*,misc-*,boost-use-ranges" \
            --quiet \
            2>&1 > "$temp_output" || true
    fi
    
    # Parse results
    local warning_count=$(grep -c "warning:" "$temp_output" 2>/dev/null || echo "0")
    local error_count=$(grep -c "error:" "$temp_output" 2>/dev/null || echo "0")
    
    if [[ "$warning_count" -gt 0 || "$error_count" -gt 0 ]]; then
        echo -e "${RED}🚨 ISSUES DETECTED${NC}"
        echo -e "${YELLOW}  Warnings: $warning_count${NC}"
        echo -e "${RED}  Errors: $error_count${NC}"
        echo ""
        
        echo -e "${YELLOW}📋 Issues found:${NC}"
        grep -E "(warning|error):" "$temp_output" | head -5 | while read -r line; do
            echo -e "  ${YELLOW}•${NC} $line"
        done
        
        if [[ $(grep -c -E "(warning|error):" "$temp_output" 2>/dev/null || echo "0") -gt 5 ]]; then
            local remaining=$(($(grep -c -E "(warning|error):" "$temp_output") - 5))
            echo -e "  ${BLUE}... and $remaining more issues${NC}"
        fi
        echo ""
        
        # Auto-fix decision
        if [[ "$error_count" -gt 0 || "$warning_count" -gt 3 ]]; then
            echo -e "${PURPLE}🚀 TRIGGERING AUTOMATIC CLANG-TIDY-FIXER...${NC}"
            echo ""
            
            # Use the clang-tidy-fixer agent directly
            if "$PROJECT_ROOT/scripts/ai_clang_tidy.sh" analyze "$file_path"; then
                echo ""
                echo -e "${GREEN}✅ AUTOMATIC FIXING COMPLETED!${NC}"
            else
                echo ""
                echo -e "${YELLOW}⚠️  Auto-fix completed with some issues${NC}"
                echo -e "${BLUE}💡 You may want to review the changes${NC}"
            fi
        else
            echo -e "${BLUE}💡 Few issues detected. Run manually if needed:${NC}"
            echo -e "${BLUE}   ./scripts/ai_clang_tidy.sh analyze \"$file_path\"${NC}"
        fi
    else
        echo -e "${GREEN}✅ NO ISSUES DETECTED${NC}"
        echo -e "${GREEN}🎉 File looks good!${NC}"
    fi
    
    rm -f "$temp_output"
}

# Main execution
main() {
    local file_path="${1:-}"
    
    if [[ -z "$file_path" ]]; then
        echo -e "${RED}❌ Usage: $0 <file_path>${NC}"
        echo -e "${BLUE}Example: $0 /IdeaProjects/wire_ground/src/main.cpp${NC}"
        exit 1
    fi
    
    instant_check_and_fix "$file_path"
}

main "$@"
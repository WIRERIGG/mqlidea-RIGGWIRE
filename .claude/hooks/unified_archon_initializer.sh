#!/bin/bash

# Unified Archon MCP Connection & Status System
# Combines all Archon MCP functionality into a single comprehensive script
# Modes: connect, status, session-start

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# MCP Configuration
MCP_URL="http://127.0.0.1:8052"
MCP_URLS=("$MCP_URL")

# Default mode
MODE="${1:-session-start}"

# Function to test a single URL
test_mcp_url() {
    local url="$1"
    [[ -z "$url" ]] && return 1
    
    # Try health endpoint first, then root endpoint
    if curl -s --max-time 2 --connect-timeout 1 "${url}/health" &>/dev/null; then
        return 0
    elif curl -s --max-time 2 --connect-timeout 1 "${url}" &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to get detailed response from working URL
get_mcp_info() {
    local url="$1"
    local health_response
    local root_response
    
    # Try to get actual response content
    health_response=$(curl -s --max-time 3 "${url}/health" 2>/dev/null || echo "")
    root_response=$(curl -s --max-time 3 "${url}" 2>/dev/null || echo "")
    
    if [[ -n "$health_response" ]]; then
        echo "$health_response"
    elif [[ -n "$root_response" ]]; then
        echo "$root_response"
    fi
}

# Function to get health status
get_health_status() {
    local url="$1"
    local health_response
    
    health_response=$(curl -s --max-time 3 "${url}/health" 2>/dev/null || echo "")
    
    if [[ -n "$health_response" ]]; then
        echo -e "${GREEN}✓ Health Check:${NC}"
        if [[ "$health_response" == "Not Found" ]]; then
            echo "  Status: ${YELLOW}Endpoint not configured${NC}"
            echo "  Server: ${GREEN}Running${NC} (responds to requests)"
        elif echo "$health_response" | python3 -m json.tool &>/dev/null; then
            # Pretty print JSON response
            echo "$health_response" | python3 -m json.tool | sed 's/^/  /'
        else
            echo "  Response: $health_response"
        fi
    else
        echo -e "${RED}✗ Health Check: No response${NC}"
    fi
}

# Function to get tool status
get_tool_status() {
    local url="$1"
    local tools_response
    
    # Try to list tools via JSON-RPC
    tools_response=$(curl -s --max-time 3 -X POST "${url}/jsonrpc" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' 2>/dev/null || echo "")
    
    echo -e "\n${CYAN}📦 Tool Status:${NC}"
    
    if [[ -n "$tools_response" ]]; then
        if [[ "$tools_response" == "Not Found" ]]; then
            echo "  ${YELLOW}JSON-RPC endpoint not configured${NC}"
            # Try alternative method to get tool info
            echo "  ${BLUE}Attempting alternative tool discovery...${NC}"
            
            # Check for MCP tools using different methods
            local mcp_info=$(curl -s --max-time 3 "${url}/mcp/tools" 2>/dev/null || echo "")
            if [[ -n "$mcp_info" && "$mcp_info" != "Not Found" ]]; then
                echo "  Available tools found via /mcp/tools:"
                echo "$mcp_info" | sed 's/^/    /'
            else
                echo "  ${YELLOW}Tool listing requires proper MCP configuration${NC}"
            fi
        elif echo "$tools_response" | python3 -m json.tool &>/dev/null; then
            # Parse and display tools if JSON response
            echo "  ${GREEN}Available Tools:${NC}"
            echo "$tools_response" | python3 -c "
import json
import sys
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'tools' in data['result']:
        for tool in data['result']['tools']:
            print(f\"    • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:50]}...\")
    elif 'error' in data:
        print(f\"    Error: {data['error'].get('message', 'Unknown error')}\")
    else:
        print('    Raw response:', json.dumps(data, indent=2))
except:
    sys.stdout.write(sys.stdin.read())
" 2>/dev/null || echo "$tools_response" | sed 's/^/    /'
        else
            echo "  Response: $tools_response"
        fi
    else
        echo "  ${RED}No response from tools endpoint${NC}"
    fi
}

# Function to get server capabilities
get_server_capabilities() {
    local url="$1"
    
    echo -e "\n${MAGENTA}🔧 Server Capabilities:${NC}"
    
    # Check various endpoints
    local endpoints=(
        "/health:Health Status"
        "/jsonrpc:JSON-RPC Interface"
        "/mcp/tools:Tool Registry"
        "/mcp/resources:Resource Manager"
        "/mcp/prompts:Prompt Templates"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint="${endpoint_info%%:*}"
        local description="${endpoint_info#*:}"
        
        if curl -s --max-time 1 --connect-timeout 1 "${url}${endpoint}" &>/dev/null; then
            local response=$(curl -s --max-time 1 "${url}${endpoint}" 2>/dev/null | head -c 50)
            if [[ "$response" == "Not Found" ]]; then
                echo "  ${YELLOW}○${NC} ${description}: Not configured"
            else
                echo "  ${GREEN}●${NC} ${description}: Available"
            fi
        else
            echo "  ${RED}○${NC} ${description}: Unreachable"
        fi
    done
}

# Function to get quick status
get_quick_status() {
    local url="$1"
    local health_response=$(curl -s --max-time 1 "${url}/health" 2>/dev/null || echo "Not Found")
    local tools_response=$(curl -s --max-time 1 -X POST "${url}/jsonrpc" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' 2>/dev/null || echo "Not Found")
    
    local health_status="❓"
    local tools_status="❓"
    
    if [[ "$health_response" != "Not Found" ]]; then
        health_status="✅"
    elif [[ -n "$health_response" ]]; then
        health_status="⚠️"
    else
        health_status="❌"
    fi
    
    if [[ "$tools_response" != "Not Found" && "$tools_response" != "" ]]; then
        if echo "$tools_response" | grep -q "result"; then
            tools_status="✅"
        else
            tools_status="⚠️"
        fi
    else
        tools_status="⚠️"
    fi
    
    echo "$health_status|$tools_status"
}

# Function to perform real-time connection check with retry logic
establish_connection() {
    local working_url=""
    local attempts=0
    local max_attempts=3
    local quiet_mode="${1:-false}"
    
    if [[ "$quiet_mode" != "true" ]]; then
        echo -e "${BLUE}Auto-connecting to Archon MCP...${NC}"
    fi
    
    # Real-time connection testing with retry logic
    while [[ $attempts -lt $max_attempts ]]; do
        for url in "${MCP_URLS[@]}"; do
            if [[ -n "$url" ]] && test_mcp_url "$url"; then
                working_url="$url"
                break
            fi
        done
        
        if [[ -n "$working_url" ]]; then
            break
        fi
        
        attempts=$((attempts + 1))
        if [[ $attempts -lt $max_attempts ]]; then
            if [[ "$quiet_mode" != "true" ]]; then
                echo -e "${YELLOW}⏳ Retrying connection... (attempt $((attempts + 1))/$max_attempts)${NC}"
            fi
            sleep 1
        fi
    done
    
    # Export the working URL for the session
    if [[ -n "$working_url" ]]; then
        export MCP_SERVER_URL="$working_url"
        export ARCHON_MCP_URL="$working_url"
        echo "$working_url"
        return 0
    else
        return 1
    fi
}

# Mode: Basic Connection
mode_connect() {
    local working_url
    working_url=$(establish_connection)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Archon MCP server connected: ${working_url}${NC}"
        echo -e "${GREEN}✓ Environment variables set${NC}"
        echo "  MCP_SERVER_URL=${working_url}"
        echo "  ARCHON_MCP_URL=${working_url}"
        
        # Get real-time server info if available
        local server_info
        server_info=$(get_mcp_info "$working_url")
        if [[ -n "$server_info" ]]; then
            echo -e "\n${BLUE}Server info:${NC}"
            echo "  $server_info"
        fi
        
        echo ""
        echo "Available endpoints:"
        echo "  Health check: curl -s ${working_url}/health"
        echo "  JSON-RPC: curl -s -X POST ${working_url}/jsonrpc"
        
        return 0
    else
        echo -e "${RED}✗ Cannot establish connection to Archon MCP server${NC}"
        echo -e "${YELLOW}Attempted URLs:${NC}"
        for url in "${MCP_URLS[@]}"; do
            [[ -n "$url" ]] && echo "  - $url"
        done
        echo -e "\n${YELLOW}Troubleshooting:${NC}"
        echo "  1. Check if Archon MCP container is running"
        echo "  2. Verify Docker network connectivity"
        echo "  3. Try: curl -s http://archon-mcp:8051/health"
        return 1
    fi
}

# Mode: Comprehensive Status
mode_status() {
    local working_url
    
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}     Archon MCP Server Status Monitor${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}\n"
    
    working_url=$(establish_connection)
    
    if [[ $? -eq 0 ]]; then
        echo -e "\n${GREEN}✅ Connection Established${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${BOLD}Server URL:${NC} ${working_url}"
        echo -e "${BOLD}Environment:${NC}"
        echo "  • MCP_SERVER_URL=${working_url}"
        echo "  • ARCHON_MCP_URL=${working_url}"
        
        # Get health status
        echo -e "\n${BOLD}${CYAN}📊 Health Status${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        get_health_status "$working_url"
        
        # Get tool status
        get_tool_status "$working_url"
        
        # Get server capabilities
        get_server_capabilities "$working_url"
        
        # Display useful commands
        echo -e "\n${BOLD}${BLUE}📝 Useful Commands:${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  • Test health: ${CYAN}curl -s ${working_url}/health${NC}"
        echo "  • List tools:  ${CYAN}curl -s -X POST ${working_url}/jsonrpc -H \"Content-Type: application/json\" -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'${NC}"
        echo "  • Get status:  ${CYAN}bash .claude/hooks/unified_archon_initializer.sh status${NC}"
        
        echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✓ Status check complete${NC}"
        echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}\n"
        
        return 0
    else
        echo -e "\n${RED}❌ Connection Failed${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${YELLOW}Attempted URLs:${NC}"
        for url in "${MCP_URLS[@]}"; do
            [[ -n "$url" ]] && echo "  • $url"
        done
        
        echo -e "\n${YELLOW}🔧 Troubleshooting Steps:${NC}"
        echo "  1. Check if Archon MCP container is running:"
        echo "     ${CYAN}docker ps | grep archon${NC}"
        echo "  2. Verify Docker network connectivity:"
        echo "     ${CYAN}docker network ls${NC}"
        echo "  3. Test direct connection:"
        echo "     ${CYAN}curl -v http://archon-mcp:8051/health${NC}"
        echo "  4. Check container logs:"
        echo "     ${CYAN}docker logs archon-mcp${NC}"
        
        echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}"
        echo -e "${RED}✗ Status check failed${NC}"
        echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════${NC}\n"
        
        return 1
    fi
}

# Mode: Session Start
mode_session_start() {
    echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}🚀 Initializing Archon MCP Connection${NC}"
    echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local working_url
    working_url=$(establish_connection true)
    
    if [[ $? -eq 0 ]]; then
        # Get quick status
        local status=$(get_quick_status "$working_url")
        local health_icon="${status%%|*}"
        local tools_icon="${status##*|}"
        
        echo -e "${GREEN}✓ Connected to Archon MCP${NC} at ${BOLD}${working_url}${NC}"
        echo -e "  ${DIM}├─${NC} Health: $health_icon  Tools: $tools_icon"
        echo -e "  ${DIM}├─${NC} MCP_SERVER_URL=${working_url}"
        echo -e "  ${DIM}└─${NC} ARCHON_MCP_URL=${working_url}"
        
        # Show quick commands
        echo -e "\n${DIM}Quick commands:${NC}"
        echo -e "  ${CYAN}• Full status:${NC} bash .claude/hooks/unified_archon_initializer.sh status"
        echo -e "  ${CYAN}• Health check:${NC} curl -s ${working_url}/health"
        echo -e "  ${CYAN}• List tools:${NC} curl -s -X POST ${working_url}/jsonrpc -d '{\"method\":\"tools/list\"}'"
        
    else
        echo -e "${YELLOW}⚠ Archon MCP server not fully responsive${NC}"
        echo -e "  Run ${CYAN}bash .claude/hooks/unified_archon_initializer.sh status${NC} for detailed diagnostics"
        
        # Still export variables for potential recovery
        export MCP_SERVER_URL="$MCP_URL"
        export ARCHON_MCP_URL="$MCP_URL"
    fi
    
    echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main execution based on mode
case "$MODE" in
    "connect")
        mode_connect
        ;;
    "status")
        mode_status
        ;;
    "session-start"|"")
        mode_session_start
        ;;
    *)
        echo -e "${RED}Error: Unknown mode '$MODE'${NC}"
        echo "Usage: $0 [connect|status|session-start]"
        echo ""
        echo "Modes:"
        echo "  connect      - Basic connection establishment"
        echo "  status       - Comprehensive status monitoring"
        echo "  session-start- Session initialization (default)"
        exit 1
        ;;
esac

exit $?
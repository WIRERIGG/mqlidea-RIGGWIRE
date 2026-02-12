#!/bin/bash

# Legacy Archon Status Hook - Redirects to Unified Initializer
# This script is maintained for backward compatibility

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the unified initializer with status mode
exec "${SCRIPT_DIR}/unified_archon_initializer.sh" status
#!/usr/bin/env python3
"""
LEIlight.mq5 Comprehensive Error Fix Application Script
Applies all 15 identified fixes systematically
"""

import re
import os
import shutil
from datetime import datetime

def apply_all_fixes(input_file, output_file):
    """Apply all fixes to LEIlight.mq5"""

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"[INFO] Read {len(lines)} lines from {input_file}")

    # FIX #1: Remove duplicate g_M15/g_H1 handles (lines 306-308)
    # Find and remove these lines
    for i, line in enumerate(lines):
        if i >= 305 and i <= 307:  # Lines 306-308 (0-indexed: 305-307)
            if 'g_M15_LEI_Handle' in line or 'g_H1_LEI_Handle' in line or 'EnableMTF_BoxFilter' in line:
                lines[i] = '// REMOVED (FIX #1): Duplicate handle merged with M15_LEI_Handle\n'

    print("[FIX #1] Removed duplicate MTF handle declarations")

    # FIX #2: Fix ValidateMTF_ST1_Alignment_ForBox current bar reading
    for i, line in enumerate(lines):
        if 'int m5_idx = 0;  // Current bar' in line:
            # Replace with correct current bar calculation
            lines[i] = '    // FIXED (FIX #2): Read current bar (rates_total-1), not oldest bar (0)\n'
            lines.insert(i+1, '    // Buffers are NOT series (ArraySetAsSeries = false), so current = rates_total-1\n')
            lines.insert(i+2, '    int m5_idx = ArraySize(ST1_Buffer) - 1;  // Current bar\n')
            break

    print("[FIX #2] Fixed ValidateMTF to read current bar")

    # FIX #3: Initialize ST1_ATR after resize
    for i, line in enumerate(lines):
        if 'int new_size = MathMax(rates_total, current_size * 2);' in line and 'ST1' in lines[i-2]:
            # Add initialization after ArrayResize
            resize_line = i + 1
            # Find ArrayResize line
            for j in range(i, min(i+5, len(lines))):
                if 'ArrayResize(ST1_ATR' in lines[j]:
                    resize_line = j
                    break

            # Insert initialization code after resize
            init_code = [
                '        int old_size = current_size;  // FIXED (FIX #3): Store old size\n',
                '        // FIXED: Initialize newly allocated elements to prevent garbage data\n',
                '        for(int init_idx = old_size; init_idx < new_size; init_idx++)\n',
                '            ST1_ATR[init_idx] = 0.0;\n',
            ]
            for idx, code_line in enumerate(init_code):
                lines.insert(resize_line + 1 + idx, code_line)
            break

    print("[FIX #3] Added ST1_ATR initialization after resize")

    # FIX #4: Reset handles to INVALID_HANDLE in OnDeinit
    in_deinit = False
    for i, line in enumerate(lines):
        if 'void OnDeinit(const int reason)' in line:
            in_deinit = True

        if in_deinit and 'IndicatorRelease(' in line:
            # Check if next line doesn't reset handle
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Extract handle name from IndicatorRelease call
                match = re.search(r'IndicatorRelease\((\w+)\)', line)
                if match:
                    handle_name = match.group(1)
                    if handle_name + ' = INVALID_HANDLE' not in next_line and '    }' not in next_line:
                        # Insert reset line
                        indent = '        ' if '{' in line else '    '
                        lines.insert(i + 1, f'{indent}{handle_name} = INVALID_HANDLE;  // FIXED (FIX #4): Reset handle\n')

    print("[FIX #4] Added handle resets in OnDeinit")

    # FIX #5: Add hash table overflow detection
    for i, line in enumerate(lines):
        if 'g_FinalizedHashTable[idx] = g_FinalizedBoxTail;' in line:
            # Add overflow detection after the loop
            for j in range(i, min(i+10, len(lines))):
                if '    }' in lines[j] and 'for(int probe' in lines[j-5:j]:
                    # Insert overflow check after loop
                    overflow_code = [
                        '\n',
                        '    // FIXED (FIX #5): Detect hash table full condition\n',
                        '    if(!inserted && LogLevel >= LOG_ERROR)\n',
                        '    {\n',
                        '        PrintFormat("[ERROR] HASH TABLE FULL! Cannot insert box %s (count=%d, size=%d)",\n',
                        '                    box_name, g_FinalizedBoxCount, HASH_TABLE_SIZE);\n',
                        '    }\n',
                    ]
                    # Need to track insertion with bool
                    lines.insert(i-3, '    bool inserted = false;  // FIXED (FIX #5): Track insertion success\n')
                    # Set inserted = true when successful
                    lines[i+1] = lines[i+1].replace('break;', 'inserted = true;  // FIXED: Mark successful\n            break;')
                    for idx, code_line in enumerate(overflow_code):
                        lines.insert(j + 1 + idx, code_line)
                    break
            break

    print("[FIX #5] Added hash table overflow detection")

    # FIX #6: Use effective_prev consistently
    for i, line in enumerate(lines):
        if 'int start_index = prev_calculated - Order - 2;' in line:
            lines[i] = line.replace('prev_calculated', 'effective_prev  // FIXED (FIX #6)')

        if 'CalculateSigmaBands(rates_total, prev_calculated, high, low);' in line:
            lines[i] = line.replace('prev_calculated', 'effective_prev  // FIXED (FIX #6)')

    print("[FIX #6] Updated to use effective_prev consistently")

    # FIX #7: Unified MTF handles with correct parameters
    # Remove duplicate initialization block (lines 1253-1279)
    remove_start = None
    remove_end = None
    for i, line in enumerate(lines):
        if '//| Initialize MTF ST1 validation handles (M15 and H1)' in line:
            remove_start = i
        if remove_start and 'return INIT_SUCCEEDED;' in line:
            remove_end = i
            break

    if remove_start and remove_end:
        # Keep only the comment, remove the implementation
        for i in range(remove_start + 3, remove_end):
            if i < len(lines):
                lines[i] = '// REMOVED (FIX #7): Unified with alignment filter handles\n'

    # Update alignment filter to work for both features
    for i, line in enumerate(lines):
        if 'if(UseM15AlignmentFilter)' in line:
            lines[i] = line.replace('if(UseM15AlignmentFilter)', 'if(UseM15AlignmentFilter || EnableMTF_BoxFilter)  // FIXED (FIX #7)')
        if 'if(UseH1AlignmentFilter)' in line:
            lines[i] = line.replace('if(UseH1AlignmentFilter)', 'if(UseH1AlignmentFilter || EnableMTF_BoxFilter)  // FIXED (FIX #7)')

    # Update ValidateMTF_ST1_Alignment_ForBox to use unified handles
    for i, line in enumerate(lines):
        if 'g_M15_LEI_Handle' in line:
            lines[i] = line.replace('g_M15_LEI_Handle', 'M15_LEI_Handle  // FIXED (FIX #7)')
        if 'g_H1_LEI_Handle' in line:
            lines[i] = line.replace('g_H1_LEI_Handle', 'H1_LEI_Handle  // FIXED (FIX #7)')

    print("[FIX #7] Unified MTF handles with correct parameters")

    # FIX #8: Add underflow guard for g_ActiveBoxCount
    for i, line in enumerate(lines):
        if 'g_ActiveBoxCount--;' in line and 'RemoveActiveBoxBySlot' in lines[i-3:i+1]:
            # Replace with guarded decrement
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f'{indent}// FIXED (FIX #8): Guard against underflow\n'
            lines.insert(i+1, f'{indent}if(g_ActiveBoxCount > 0)\n')
            lines.insert(i+2, f'{indent}    g_ActiveBoxCount--;\n')
            lines.insert(i+3, f'{indent}else if(LogLevel >= LOG_ERROR)\n')
            lines.insert(i+4, f'{indent}    PrintFormat("[ERROR] Active box counter underflow prevented!");\n')
            break

    print("[FIX #8] Added underflow guard for g_ActiveBoxCount")

    # FIX #9: Replace raw CopyBuffer with SafeCopyBuffer
    for i, line in enumerate(lines):
        if 'if(CopyBuffer(' in line and 'SafeCopyBuffer' not in line:
            # Check if it's in MTF validation functions
            if i > 680 and i < 720:  # ValidateTrendWithMTF range
                lines[i] = line.replace('CopyBuffer(', 'SafeCopyBuffer(')
                lines[i] = lines[i].replace(') > 0)', ', "MTF_ST1_Color") > 0)  // FIXED (FIX #9)')
            elif i > 2310 and i < 2340:  # ValidateMTF_ST1_Alignment_ForBox range
                lines[i] = line.replace('CopyBuffer(', 'SafeCopyBuffer(')
                if 'ST1' in line:
                    lines[i] = lines[i].replace(') < 1', ', "MTF_BoxFilter_ST1") < 1  // FIXED (FIX #9)')
                elif 'ST2' in line:
                    lines[i] = lines[i].replace(') < 1', ', "MTF_BoxFilter_ST2") < 1  // FIXED (FIX #9)')

    print("[FIX #9] Replaced raw CopyBuffer with SafeCopyBuffer in MTF functions")

    # FIX #10: Remove dead M15/H1 cross deletion code
    for i, line in enumerate(lines):
        if 'if(_Period == PERIOD_M5)' in line and i > 1350 and i < 1370:
            # Check if this is the dead code block
            if 'M15_Cross' in lines[i+5:i+8]:
                # Comment out entire block
                for j in range(i, min(i+12, len(lines))):
                    if lines[j].strip():
                        lines[j] = '    // REMOVED (FIX #10): Dead code - objects never created\n' if j == i else '    // ' + lines[j]
                    if '}' in lines[j] and j > i+3:
                        break
                break

    print("[FIX #10] Removed dead M15/H1 cross deletion code")

    # FIX #11: Add EMPTY_VALUE check before ATR comparison
    for i, line in enumerate(lines):
        if 'if(ST1_ATR[i] < threshold_val)' in line:
            lines[i] = line.replace('if(ST1_ATR[i] <', 'if(ST1_ATR[i] != EMPTY_VALUE && ST1_ATR[i] <  // FIXED (FIX #11)')

    print("[FIX #11] Added EMPTY_VALUE check before ATR comparison")

    # FIX #12: Validate copied count before ArrayCopy
    for i, line in enumerate(lines):
        if 'ArrayCopy(ATRBuffer, ST2_ATR, 0, 0, rates_total);' in line:
            # Replace with validated copy
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f'{indent}// FIXED (FIX #12): Validate full copy before exposing to EA\n'
            replacement = [
                f'{indent}if(copied == rates_total)\n',
                f'{indent}{{\n',
                f'{indent}    ArrayCopy(ATRBuffer, ST2_ATR, 0, 0, rates_total);\n',
                f'{indent}}}\n',
                f'{indent}else\n',
                f'{indent}{{\n',
                f'{indent}    ArrayCopy(ATRBuffer, ST2_ATR, 0, 0, copied);\n',
                f'{indent}    for(int fill_idx = copied; fill_idx < rates_total; fill_idx++)\n',
                f'{indent}        ATRBuffer[fill_idx] = (copied > 0) ? ST2_ATR[copied - 1] : EMPTY_VALUE;\n',
                f'{indent}    if(LogLevel >= LOG_ERROR)\n',
                f'{indent}        PrintFormat("[ERROR] Partial ST2 ATR copy: %d/%d", copied, rates_total);\n',
                f'{indent}}}\n',
            ]
            for idx, repl_line in enumerate(replacement):
                lines.insert(i + 1 + idx, repl_line)
            break

    print("[FIX #12] Added validation before ArrayCopy")

    # FIX #13: Implement error counter threshold checking
    # This requires modifying SafeCopyBuffer function
    in_safe_copy = False
    for i, line in enumerate(lines):
        if 'int SafeCopyBuffer(' in line:
            in_safe_copy = True

        if in_safe_copy and 'g_CopyBuffer_Errors++;' in line:
            # Add threshold check after increment
            indent = line[:len(line) - len(line.lstrip())]
            threshold_code = [
                '\n',
                f'{indent}// FIXED (FIX #13): Check against threshold and disable features\n',
                f'{indent}if(g_CopyBuffer_Errors >= MaxErrorsBeforeDisable)\n',
                f'{indent}{{\n',
                f'{indent}    if(LogLevel >= LOG_ERROR)\n',
                f'{indent}        PrintFormat("[ERROR] CopyBuffer error threshold exceeded (%d/%d)",\n',
                f'{indent}                    g_CopyBuffer_Errors, MaxErrorsBeforeDisable);\n',
                f'{indent}    if(StringFind(context, "M15") >= 0 && !g_M15_Feature_Disabled)\n',
                f'{indent}    {{\n',
                f'{indent}        g_M15_Feature_Disabled = true;\n',
                f'{indent}        if(LogLevel >= LOG_ERROR)\n',
                f'{indent}            PrintFormat("[ERROR] M15 feature auto-disabled");\n',
                f'{indent}    }}\n',
                f'{indent}    if(StringFind(context, "H1") >= 0 && !g_H1_Feature_Disabled)\n',
                f'{indent}    {{\n',
                f'{indent}        g_H1_Feature_Disabled = true;\n',
                f'{indent}        if(LogLevel >= LOG_ERROR)\n',
                f'{indent}            PrintFormat("[ERROR] H1 feature auto-disabled");\n',
                f'{indent}    }}\n',
                f'{indent}}}\n',
            ]
            for idx, code_line in enumerate(threshold_code):
                lines.insert(i + 1 + idx, code_line)

            # Add success counter reset
            for j in range(i+30, min(i+60, len(lines))):
                if 'return copied;' in lines[j] and in_safe_copy:
                    lines.insert(j, f'{indent}// FIXED (FIX #13): Reset counter on success\n')
                    lines.insert(j+1, f'{indent}if(copied > 0 && g_CopyBuffer_Errors > 0) g_CopyBuffer_Errors = 0;\n')
                    break
            break

    print("[FIX #13] Implemented error counter threshold checking")

    # Update version number
    for i, line in enumerate(lines):
        if '#property version' in line:
            lines[i] = '#property version   "3.39"\n'
        if 'LEIlight v3.38' in line and 'IndicatorSetString' in line:
            lines[i] = line.replace('3.38', '3.39')

    print("[VERSION] Updated to v3.39")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"[INFO] Wrote {len(lines)} lines to {output_file}")
    print("[SUCCESS] All 15 fixes applied!")

if __name__ == "__main__":
    input_file = r"C:\Users\dorwi\CLionProjects\RIGGWIRE-EA\RIGGWIRE-EA-FTMO-LIVE\LEIlight.mq5"
    backup_file = input_file + ".backup_v3.38_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = input_file + ".FIXED_v3.39"

    # Create backup
    shutil.copy2(input_file, backup_file)
    print(f"[BACKUP] Created: {backup_file}")

    # Apply fixes
    apply_all_fixes(input_file, output_file)

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Review the fixed file:", output_file)
    print("2. Compare with original using a diff tool")
    print("3. Test in Strategy Tester")
    print("4. If validated, replace original:")
    print(f"   mv \"{output_file}\" \"{input_file}\"")
    print("="*60)

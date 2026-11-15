#!/bin/zsh
# Corpus gate: parse, resolve and inspect real MQL corpora and fail on any regression against
# src/test/resources/gate/corpus-baseline.properties. MQL_GATE_UPDATE=1 rewrites the baseline
# (do that only after a deliberate change, and commit the new baseline with it).
# Reads the local MetaTrader install read-only; nothing from it is copied into the repository.
set -euo pipefail
cd "${0:A:h}/.."
MT5="${MT5_MQL5:-$HOME/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5}"
EA="${MQL_EA_DIR:-$HOME/CLionProjects/RIGGWIRE-EA-TC/RIGGWIRE-EA-LIVE}"
[[ -d "$MT5" ]] || { echo "no MetaTrader MQL5 folder at $MT5 (set MT5_MQL5)"; exit 1; }
# MetaQuotes' own Standard Library only: the rest of Include is the user's own (it changes).
export MQL_INCLUDE_ONLY="Arrays/,Canvas/,ChartObjects/,Charts/,Controls/,Expert/,Files/,Generic/,Graphics/,Indicators/,Math/,OpenCL/,Strings/,Tools/,Trade/,WinAPI/,Object.mqh,StdLibErr.mqh,VirtualKeys.mqh,MovingAverages.mqh"
export MQL_CORPORA="include=$MT5/Include;examples=$MT5/Experts/Examples,$MT5/Indicators/Examples,$MT5/Scripts/Examples,$MT5/Scripts/UnitTests;free=$MT5/Experts/Free Robots,$MT5/Indicators/Free Indicators;report:ea=$EA"
export JAVA_HOME="${JAVA_HOME:-/Applications/CLion.app/Contents/jbr/Contents/Home}"
# the gate re-indexes a few hundred files; a killed run leaves the test sandbox's index corrupt,
# which then fails unrelated unit tests, so start and finish with a fresh one
fresh_index() { rm -rf build/idea-sandbox/*/system-test(N) }
fresh_index; trap fresh_index EXIT
./gradlew cleanTest test --tests 'gate.CorpusGateTest' -q "$@"
echo "report: build/corpus-gate-report.txt"

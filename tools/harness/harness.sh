#!/bin/zsh
# MetaEditor harness, plugin side: scores the plugin against the verdicts metaeditor_verdicts.py
# stored (run that first, while MetaTrader is idle). Writes build/harness-report.md and fails when
# open sources' false or missed errors rise above src/test/resources/gate/harness-baseline.properties
# (MQL_HARNESS_UPDATE=1 rewrites it after a deliberate change; MQL_HARNESS_HELDOUT=1 adds held-out sources).
set -euo pipefail
cd "${0:A:h}/../.."
export MQL_HARNESS="${MQL_HARNESS:-$PWD/tools/harness/corpus.json}"
export JAVA_HOME="${JAVA_HOME:-/Applications/CLion.app/Contents/jbr/Contents/Home}"
# a killed run leaves the test sandbox's index corrupt, so start and finish with a fresh one
fresh_index() { rm -rf build/idea-sandbox/*/system-test(N) }
fresh_index; trap fresh_index EXIT
./gradlew cleanTest test --tests 'gate.HarnessTest' -q "$@"
echo "report: build/harness-report.md"

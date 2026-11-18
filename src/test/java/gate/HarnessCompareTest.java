/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package gate;

import gate.HarnessCompare.MetaEditorDiag;
import gate.HarnessCompare.Outcome;
import gate.HarnessCompare.PluginDiag;
import gate.HarnessCompare.Result;
import gate.HarnessCompare.Verdict;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/** The harness scoring rules (specs/001-metaeditor-harness/data-model.md). */
class HarnessCompareTest {

    private static Verdict clean() {
        return new Verdict("s", "A.mq5", null, List.of());
    }

    private static Verdict errorsAt(MetaEditorDiag... d) {
        return new Verdict("s", "A.mq5", null, List.of(d));
    }

    private static MetaEditorDiag err(String file, int line) {
        return new MetaEditorDiag(file, line, true, 256, "'x' - undeclared identifier");
    }

    private static PluginDiag plug(String file, int line) {
        return new PluginDiag(file, line, "parse", "PsiErrorElement", "';' expected");
    }

    @Test
    void bothCleanAgree() {
        assertThat(HarnessCompare.classify(clean(), List.of()).outcome()).isEqualTo(Outcome.AGREE_CLEAN);
    }

    @Test
    void pluginErrorOnCleanCodeIsAFalseError() {
        Result r = HarnessCompare.classify(clean(), List.of(plug("A.mq5", 40)));
        assertThat(r.outcome()).isEqualTo(Outcome.FALSE_ERROR);
        assertThat(r.kinds()).extracting(HarnessCompare.Example::kind).containsExactly("plugin:parse:PsiErrorElement");
    }

    @Test
    void metaEditorErrorThePluginMissesIsAMissedError() {
        Result r = HarnessCompare.classify(errorsAt(err("A.mq5", 12)), List.of());
        assertThat(r.outcome()).isEqualTo(Outcome.MISSED_ERROR);
        assertThat(r.kinds()).extracting(HarnessCompare.Example::kind).containsExactly("metaeditor:256 'x' - undeclared identifier");
    }

    @Test
    void errorsWithinOneLineInTheSameFileAgree() {
        assertThat(HarnessCompare.classify(errorsAt(err("A.mq5", 12)), List.of(plug("A.mq5", 13))).outcome())
                .isEqualTo(Outcome.AGREE_ERRORS);
    }

    @Test
    void errorsOnUnrelatedLinesAreDisjointNotAgreement() {
        Result r = HarnessCompare.classify(errorsAt(err("A.mq5", 900)), List.of(plug("A.mq5", 40)));
        assertThat(r.outcome()).isEqualTo(Outcome.DISJOINT_ERRORS);
        assertThat(r.kinds()).hasSize(2);
        assertThat(HarnessCompare.classify(errorsAt(err("B.mqh", 40)), List.of(plug("A.mq5", 40))).outcome())
                .isEqualTo(Outcome.DISJOINT_ERRORS);
    }

    @Test
    void aMetaEditorCascadeCountsOnceAndKeepsTheFirstError() {
        Result r = HarnessCompare.classify(errorsAt(err("A.mq5", 30), err("A.mq5", 31), err("A.mq5", 10), err("A.mq5", 55)), List.of());
        assertThat(r.outcome()).isEqualTo(Outcome.MISSED_ERROR);
        assertThat(r.kinds()).singleElement().satisfies(x -> assertThat(x.line()).isEqualTo(10));
    }

    @Test
    void warningsNeverDecide() {
        Verdict onlyWarning = new Verdict("s", "A.mq5", null, List.of(new MetaEditorDiag("A.mq5", 5, false, 43, "possible loss of data")));
        assertThat(HarnessCompare.classify(onlyWarning, List.of()).outcome()).isEqualTo(Outcome.AGREE_CLEAN);
    }

    @Test
    void excludedKeepsItsReason() {
        Result r = HarnessCompare.classify(new Verdict("s", "A.mq5", "missing-include", List.of()), List.of(plug("A.mq5", 1)));
        assertThat(r.outcome()).isEqualTo(Outcome.EXCLUDED);
        assertThat(r.excludedReason()).isEqualTo("missing-include");
    }

    @Test
    void theReportIsDeterministicAndScoresOnlyOpenSources() {
        List<Result> results = List.of(
                HarnessCompare.classify(new Verdict("b", "Z.mq5", null, List.of()), List.of(plug("Z.mq5", 3))),
                HarnessCompare.classify(new Verdict("a", "Y.mq5", null, List.of()), List.of()),
                HarnessCompare.classify(new Verdict("ea", "E.mq5", null, List.of()), List.of(plug("E.mq5", 9))),
                HarnessCompare.classify(new Verdict("a", "X.mq5", "no-log", List.of()), List.of()));
        Map<String, String> roles = Map.of("a", "open", "b", "open", "ea", "report");
        String one = HarnessCompare.report(results, roles);
        String two = HarnessCompare.report(List.of(results.get(3), results.get(2), results.get(1), results.get(0)), roles);
        assertThat(one).isEqualTo(two);
        assertThat(one).contains("- judged programs: 2\n", "- false-error: 1\n", "- agree-clean: 1\n", "- no-log: 1\n");
        assertThat(one).contains("**plugin:parse:PsiErrorElement**: 1 programs", "  - b/Z.mq5:3");
        assertThat(one).doesNotContain("E.mq5:9");
    }
}

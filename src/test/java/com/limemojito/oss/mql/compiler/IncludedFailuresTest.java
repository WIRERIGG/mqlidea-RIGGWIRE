/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/** A program whose own lines are clean still names the headers that keep it from building. */
class IncludedFailuresTest {

    private static final List<CompilerDiagnostic> LOG = CompilerOutputParser.parse(String.join("\n",
            "Z:\\Users\\u\\EA\\Main.mq5(3,1) : warning 43: possible loss of data",
            "Z:\\Users\\u\\EA\\RiskManager.mqh(40,5) : error 256: undeclared identifier 'y'",
            "Z:\\Users\\u\\EA\\RiskManager.mqh(41,5) : error 256: undeclared identifier 'z'",
            "Z:\\Users\\u\\EA\\Clock.mqh(9,1) : error 100: boom",
            "Z:\\Users\\u\\EA\\Clock.mqh(10,1) : warning 43: possible loss of data"));

    private static MqlCompilerService.CompileResult result(List<CompilerDiagnostic> d) {
        return new MqlCompilerService.CompileResult(d, true, 3, 2);
    }

    @Test
    void headersWithErrorsAreNamedWithTheirCounts() {
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(LOG, List.of("/Users/u/EA/Main.mq5"), true);
        assertThat(MqlCompilerExternalAnnotator.includedFailures(result(LOG), own))
                .isEqualTo("RiskManager.mqh (2), Clock.mqh (1)");
    }

    @Test
    void warningsAloneAndTheProgramsOwnErrorsAreNotIncludedFailures() {
        List<CompilerDiagnostic> clean = CompilerOutputParser.parse(String.join("\n",
                "Z:\\Users\\u\\EA\\Main.mq5(3,1) : error 256: undeclared identifier 'x'",
                "Z:\\Users\\u\\EA\\Clock.mqh(10,1) : warning 43: possible loss of data"));
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(clean, List.of("/Users/u/EA/Main.mq5"), true);
        assertThat(MqlCompilerExternalAnnotator.includedFailures(result(clean), own)).isNull();
    }
}

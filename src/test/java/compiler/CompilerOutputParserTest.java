/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import com.limemojito.oss.mql.compiler.CompilerDiagnostic;
import com.limemojito.oss.mql.compiler.CompilerDiagnostic.Severity;
import com.limemojito.oss.mql.compiler.CompilerOutputParser;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CompilerOutputParserTest {

    @Test
    void parsesLocatedErrorWithCode() {
        List<CompilerDiagnostic> d = CompilerOutputParser.parse(
                "MyExpert.mq5(12,5) : error 100: 'x' - undeclared identifier");
        assertThat(d).hasSize(1);
        CompilerDiagnostic e = d.get(0);
        assertThat(e.fileName()).isEqualTo("MyExpert.mq5");
        assertThat(e.line()).isEqualTo(12);
        assertThat(e.column()).isEqualTo(5);
        assertThat(e.severity()).isEqualTo(Severity.ERROR);
        assertThat(e.code()).isEqualTo("100");
        assertThat(e.message()).isEqualTo("'x' - undeclared identifier");
        assertThat(e.hasLocation()).isTrue();
    }

    @Test
    void parsesWarningAndErrorWithoutCode() {
        List<CompilerDiagnostic> d = CompilerOutputParser.parse(
                "a.mq5(20,10) : warning 43: declaration of 'y' hides a global declaration\n" +
                "a.mq5(3,1) : error : unexpected token");
        assertThat(d).hasSize(2);
        assertThat(d.get(0).severity()).isEqualTo(Severity.WARNING);
        assertThat(d.get(0).code()).isEqualTo("43");
        assertThat(d.get(1).severity()).isEqualTo(Severity.ERROR);
        assertThat(d.get(1).code()).isNull();
        assertThat(d.get(1).message()).isEqualTo("unexpected token");
    }

    @Test
    void extractsBareFileNameFromWindowsPath() {
        List<CompilerDiagnostic> d = CompilerOutputParser.parse(
                "C:\\Users\\me\\MQL5\\Experts\\My.mq5(7,2) : error 145: some error");
        assertThat(d).hasSize(1);
        assertThat(d.get(0).fileName()).isEqualTo("My.mq5");
    }

    @Test
    void parsesFileLevelInformationWithoutLocation() {
        List<CompilerDiagnostic> d = CompilerOutputParser.parse(
                "My.mq5 : information: compiling 'My.mq5'");
        assertThat(d).hasSize(1);
        assertThat(d.get(0).severity()).isEqualTo(Severity.INFORMATION);
        assertThat(d.get(0).hasLocation()).isFalse();
        assertThat(d.get(0).line()).isZero();
    }

    @Test
    void ignoresBannersBlankLinesAndResultTrailer() {
        List<CompilerDiagnostic> d = CompilerOutputParser.parse(
                "MetaEditor 5 build 4000\n\n" +
                "My.mq5(1,1) : error 1: boom\n" +
                "Result: 1 error(s), 0 warning(s), ...\n");
        assertThat(d).hasSize(1);
        assertThat(d.get(0).message()).isEqualTo("boom");
    }

    @Test
    void parsesSummaryCounts() {
        int[] s = CompilerOutputParser.parseSummary("Result: 2 error(s), 3 warning(s), 1 msec elapsed");
        assertThat(s).containsExactly(2, 3);
    }

    @Test
    void emptyOrNullLogYieldsNoDiagnostics() {
        assertThat(CompilerOutputParser.parse(null)).isEmpty();
        assertThat(CompilerOutputParser.parse("   \n  \n")).isEmpty();
        assertThat(CompilerOutputParser.parseSummary("no result here")).isNull();
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import com.limemojito.oss.mql.compiler.CompilerDiagnostic;
import com.limemojito.oss.mql.compiler.CompilerOutputParser;
import com.limemojito.oss.mql.compiler.DiagnosticFileMatcher;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Attribution of MetaEditor diagnostics to files, using log lines in the exact shape MetaEditor writes
 * when a program's compile reports errors inside its {@code #include}d headers.
 */
class DiagnosticFileMatcherTest {

    private static final String TERMINAL = "/Users/u/Library/Application Support/net.metaquotes.wine.metatrader5"
            + "/drive_c/Program Files/MetaTrader 5/";

    private static final String LOG = String.join("\n",
            "MQL5\\Experts\\RIGGWIRE\\Main.mq5 : information: compiling MQL5\\Experts\\RIGGWIRE\\Main.mq5",
            "MQL5\\Experts\\RIGGWIRE\\Main.mq5(10,3) : error 256: undeclared identifier 'a'",
            "MQL5\\Experts\\RIGGWIRE\\DualOrderManager.mqh(169,59) : error 256: undeclared identifier 'IsOurStrategy'",
            "MQL5\\Experts\\RIGGWIRE\\Utils.mqh(4,1) : warning 43: possible loss of data",
            "MQL5\\Include\\Other\\Utils.mqh(7,2) : error 256: undeclared identifier 'b'",
            "Result: 3 errors, 1 warnings");

    private final List<CompilerDiagnostic> diagnostics = CompilerOutputParser.parse(LOG);

    @Test
    void parserKeepsThePrintedPath() {
        assertThat(diagnostics.get(2).path()).isEqualTo("MQL5\\Experts\\RIGGWIRE\\DualOrderManager.mqh");
        assertThat(diagnostics.get(2).fileName()).isEqualTo("DualOrderManager.mqh");
    }

    @Test
    void headerGetsOnlyItsOwnDiagnostics() {
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(diagnostics,
                List.of(TERMINAL + "MQL5/Experts/RIGGWIRE/DualOrderManager.mqh"), false);
        assertThat(own).extracting(CompilerDiagnostic::line).containsExactly(169);
    }

    @Test
    void sameNamedHeadersInDifferentFoldersAreKeptApart() {
        List<CompilerDiagnostic> experts = DiagnosticFileMatcher.forFile(diagnostics,
                List.of(TERMINAL + "MQL5/Experts/RIGGWIRE/Utils.mqh"), false);
        List<CompilerDiagnostic> include = DiagnosticFileMatcher.forFile(diagnostics,
                List.of(TERMINAL + "MQL5/Include/Other/Utils.mqh"), false);
        assertThat(experts).extracting(CompilerDiagnostic::line).containsExactly(4);
        assertThat(include).extracting(CompilerDiagnostic::line).containsExactly(7);
    }

    @Test
    void matchingIsCaseInsensitive() {
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(diagnostics,
                List.of(TERMINAL + "mql5/experts/riggwire/dualordermanager.MQH"), false);
        assertThat(own).hasSize(1);
    }

    @Test
    void headerOutsideTheLoggedTreeGetsNothingEvenWithTheSameName() {
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(diagnostics,
                List.of("/Users/u/CLionProjects/Repo/DualOrderManager.mqh"), false);
        assertThat(own).isEmpty();
    }

    @Test
    void canonicalPathIsTriedToo() {
        List<CompilerDiagnostic> own = DiagnosticFileMatcher.forFile(diagnostics,
                List.of("/Users/u/link/DualOrderManager.mqh", TERMINAL + "MQL5/Experts/RIGGWIRE/DualOrderManager.mqh"),
                false);
        assertThat(own).hasSize(1);
    }

    @Test
    void absoluteWinePathMatchesTheUnixPath() {
        List<CompilerDiagnostic> wine = CompilerOutputParser.parse(
                "Z:\\home\\u\\mql\\Lib.mqh(3,1) : error 100: boom");
        assertThat(DiagnosticFileMatcher.forFile(wine, List.of("/home/u/mql/Lib.mqh"), false)).hasSize(1);
    }

    /** A repo checkout compiled through mt5 (Z: drive): a worktree copy of the same header gets nothing. */
    @Test
    void repoCheckoutHeaderIsMatchedAndItsWorktreeCopyIsNot() {
        List<CompilerDiagnostic> repo = CompilerOutputParser.parse(String.join("\n",
                "Z:\\Users\\u\\Repo\\EA\\Main.mq5(2,1) : error 256: undeclared identifier 'x'",
                "Z:\\Users\\u\\Repo\\EA\\RiskManager.mqh(40,5) : error 256: undeclared identifier 'y'"));
        assertThat(DiagnosticFileMatcher.forFile(repo, List.of("/Users/u/Repo/EA/RiskManager.mqh"), false))
                .extracting(CompilerDiagnostic::line).containsExactly(40);
        assertThat(DiagnosticFileMatcher.forFile(repo, List.of("/Users/u/Repo/worktrees/seed/EA/RiskManager.mqh"), false))
                .isEmpty();
        assertThat(DiagnosticFileMatcher.forFile(repo, List.of("/Users/u/Repo/EA/Main.mq5"), true))
                .extracting(CompilerDiagnostic::line).containsExactly(2);
    }

    @Test
    void compiledProgramFallsBackToItsBareNameWhenUnambiguous() {
        List<CompilerDiagnostic> bare = CompilerOutputParser.parse("Main.mq5(2,1) : error 100: boom");
        assertThat(DiagnosticFileMatcher.forFile(bare, List.of("/elsewhere/Main.mq5"), true)).hasSize(1);
        assertThat(DiagnosticFileMatcher.forFile(bare, List.of("/elsewhere/Main.mq5"), false)).isEmpty();
    }

    @Test
    void nameFallbackRefusesAnAmbiguousName() {
        assertThat(DiagnosticFileMatcher.forFile(diagnostics, List.of("/elsewhere/Utils.mqh"), true)).isEmpty();
    }
}

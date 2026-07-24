/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.limemojito.oss.mql.compiler.MetaEditorLauncher;
import com.limemojito.oss.mql.compiler.Mt5CliLauncher;
import com.limemojito.oss.mql.compiler.WineLauncher;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermission;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Pure tests (no IntelliJ platform bootstrap needed) of the Phase 1 launcher-selection strategies
 * against a faked filesystem/OS environment &mdash; per docs/REVAMP_PLAN.md's "probed
 * auto-detection... never assume" mitigation for the old broken
 * {@code OSUtils.isWine() == !isWindowsOS()} + bare-{@code wine}-on-PATH assumption.
 *
 * <p>These complement {@code compiler.MqlCompilerServiceTest}, which exercises
 * {@code MqlCompilerService}'s own ordering/caching logic against fully-fake launchers.</p>
 */
class LauncherAvailabilityTest {

    private String originalUserHome;
    private String originalOsName;
    private String originalWinePathProperty;

    @BeforeEach
    void saveSystemState() {
        originalUserHome = System.getProperty("user.home");
        originalOsName = System.getProperty("os.name");
        originalWinePathProperty = System.getProperty("mql.wine.path");
    }

    @AfterEach
    void restoreSystemState() {
        setOrClear("user.home", originalUserHome);
        setOrClear("os.name", originalOsName);
        setOrClear("mql.wine.path", originalWinePathProperty);
    }

    private static void setOrClear(String key, String value) {
        if (value == null) {
            System.clearProperty(key);
        } else {
            System.setProperty(key, value);
        }
    }

    @Test
    void mt5CliLauncherIsUnavailableWithoutTheWrapper(@TempDir Path emptyHome) {
        System.setProperty("user.home", emptyHome.toString());

        assertThat(new Mt5CliLauncher().commandFor(new File("Test.mq5"))).isNull();
    }

    @Test
    void mt5CliLauncherFindsTheWrapperUnderUserHome(@TempDir Path fakeHome) throws IOException {
        System.setProperty("user.home", fakeHome.toString());
        Path mt5 = fakeHome.resolve(".local/bin/mt5");
        Files.createDirectories(mt5.getParent());
        Files.writeString(mt5, "#!/bin/sh\n");
        makeExecutable(mt5);

        GeneralCommandLine cmd = new Mt5CliLauncher().commandFor(new File("Test.mq5"));

        assertThat(cmd).isNotNull();
        assertThat(cmd.getExePath()).isEqualTo(mt5.toString());
        assertThat(cmd.getParametersList().getArray())
                .containsExactly("compile", new File("Test.mq5").getAbsolutePath());
    }

    @Test
    void metaEditorLauncherIsUnavailableOffWindows() {
        System.setProperty("os.name", "Mac OS X");

        assertThat(new MetaEditorLauncher().commandFor(new File("Test.mq5"))).isNull();
    }

    @Test
    void wineLauncherIsUnavailableOnWindows() {
        System.setProperty("os.name", "Windows 11");

        assertThat(new WineLauncher().commandFor(new File("Test.mq5"))).isNull();
    }

    @Test
    void wineLauncherIsUnavailableWithoutADiscoverableWineBinary() {
        System.setProperty("os.name", "Linux");
        System.clearProperty("mql.wine.path");

        // No Wine binary is expected at the common install paths probed by WineLauncher on the
        // machine running this suite; even if one legitimately exists there, the launcher still
        // requires a configured MQL4 SDK (never registered in this pure unit test) before it will
        // hand back a command -- see WineLauncher/MetaEditorLauncher.findMetaEditorExe().
        assertThat(new WineLauncher().commandFor(new File("Test.mq5"))).isNull();
    }

    private static void makeExecutable(Path path) throws IOException {
        Files.setPosixFilePermissions(path, Set.of(
                PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE));
    }
}

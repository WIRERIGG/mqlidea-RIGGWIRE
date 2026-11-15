/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package deploy;

import com.limemojito.oss.mql.deploy.Mt5Mirror;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/** The repository-to-MetaTrader mapping follows the mt5 bridge's sync rules, and comparing never writes. */
class Mt5MirrorTest {

    @TempDir
    Path tmp;

    private Path repo;
    private Path mql5;

    private Path write(Path p, String text) throws IOException {
        Files.createDirectories(p.getParent());
        return Files.writeString(p, text);
    }

    private void layout(String config) throws IOException {
        repo = tmp.resolve("repo");
        mql5 = tmp.resolve("MT5/MQL5");
        Files.createDirectories(repo.resolve(".git"));
        if (config != null) {
            write(repo.resolve(".claude/mt5-bridge.json"), config);
        }
        Files.createDirectories(mql5.resolve("Experts/EA_CHECK"));
    }

    @Test
    void mapsThroughTheBridgeConfigAndReportsEachState() throws IOException {
        layout("{\n  \"experts_subdir\": \"EA_CHECK\",\n  \"project_src\": \"src\"\n}\n");
        Path main = write(repo.resolve("src/Main.mq5"), "void OnTick() {}\n");
        Path lib = write(repo.resolve("src/Lib/Part.mqh"), "int a;\n");
        Path fresh = write(repo.resolve("src/New.mqh"), "int b;\n");
        write(mql5.resolve("Experts/EA_CHECK/Main.mq5"), "void OnTick() {}\n");
        write(mql5.resolve("Experts/EA_CHECK/Lib/Part.mqh"), "int old;\n");
        write(repo.resolve("src/notes.txt"), "not a source");

        Mt5Mirror mirror = Mt5Mirror.forFile(main, mql5, Map.of(), null);
        assertThat(mirror).isNotNull();
        assertThat(mirror.copyOf(lib)).isEqualTo(mql5.resolve("Experts/EA_CHECK/Lib/Part.mqh"));
        assertThat(mirror.state(main)).isEqualTo(Mt5Mirror.State.SAME);
        assertThat(mirror.state(lib)).isEqualTo(Mt5Mirror.State.DIFFERENT);
        assertThat(mirror.state(fresh)).isEqualTo(Mt5Mirror.State.MISSING);
        assertThat(mirror.drifted()).containsExactly("Lib/Part.mqh", "New.mqh");
        assertThat(Files.readString(mql5.resolve("Experts/EA_CHECK/Lib/Part.mqh"))).isEqualTo("int old;\n");
    }

    @Test
    void environmentOverridesTheConfig() throws IOException {
        layout("{ \"experts_subdir\": \"WRONG\", \"project_src\": \"src\" }");
        Path main = write(repo.resolve("src/Main.mq5"), "x");
        assertThat(Mt5Mirror.forFile(main, mql5, Map.of(), null)).isNull(); // MQL5/Experts/WRONG doesn't exist
        Mt5Mirror mirror = Mt5Mirror.forFile(main, mql5, Map.of("MT5_EXPERTS_SUBDIR", "EA_CHECK"), null);
        assertThat(mirror).isNotNull();
        assertThat(mirror.mirror).isEqualTo(mql5.resolve("Experts/EA_CHECK"));
    }

    @Test
    void filesOutsideTheSourceFolderHaveNoMirror() throws IOException {
        layout("{ \"experts_subdir\": \"EA_CHECK\", \"project_src\": \"src\" }");
        Path tool = write(repo.resolve("tools/Gen.mq5"), "x");
        assertThat(Mt5Mirror.forFile(tool, mql5, Map.of(), null)).isNull();
    }

    @Test
    void withoutAConfigTheBridgeDefaultsApply() throws IOException {
        layout(null);
        Path home = tmp.resolve("home");
        Path src = home.resolve("CLionProjects/RIGGWIRE-EA-LIVE/RIGGWIRE-EA-LIVE");
        Files.createDirectories(src.getParent().resolve(".git"));
        Path main = write(src.resolve("Main.mq5"), "x");
        Files.createDirectories(mql5.resolve("Experts/RIGGWIRE"));
        Mt5Mirror mirror = Mt5Mirror.forFile(main, mql5, Map.of(), home);
        assertThat(mirror).isNotNull();
        assertThat(mirror.drifted()).isEqualTo(List.of("Main.mq5"));
    }
}

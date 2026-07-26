/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * Test-only stand-in for the real MetaEditor compiler: writes a fixed one-error compile log to the
 * path given in {@code args[0]}, encoded UTF-16 <b>little-endian without a BOM</b> (MetaEditor's real
 * Windows output). Run as a genuine subprocess by {@code MqlCompilerServiceTest} so the log appears
 * <em>during</em> the compile run — which is what {@link com.limemojito.oss.mql.compiler.MqlCompilerService}'s
 * stale-log deletion now requires (a pre-planted fixture would be deleted before the run). Doubles as
 * an end-to-end check of the LE-no-BOM decode path.
 */
public final class CompileLogWriterMain {

    private CompileLogWriterMain() {
    }

    public static void main(String[] args) throws Exception {
        String content = "Expert.mq5(2,3) : error 5: fake error\n"
                + "Result: 1 error(s), 0 warning(s), 1 msec elapsed\n";
        Files.write(Paths.get(args[0]), content.getBytes(StandardCharsets.UTF_16LE));
    }
}

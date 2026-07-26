/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import com.limemojito.oss.mql.compiler.CompilerOutputParser;
import com.limemojito.oss.mql.compiler.MqlCompilerService;
import junit.framework.TestCase;

import java.nio.charset.StandardCharsets;

/**
 * Locks {@link MqlCompilerService#decodeMqlLog(byte[])} against the endianness bug that made a
 * BOM-less UTF-16LE MetaEditor log (the real Windows output) decode to byte-swapped mojibake under
 * the JVM-default {@code StandardCharsets.UTF_16} — which then matched no diagnostics and reported a
 * false "0 errors". All three real shapes must round-trip to the same readable text.
 */
public class CompileLogDecodeTest extends TestCase {

    private static final String LOG =
            "Expert.mq5(12,5) : error 100: 'x' - some undeclared identifier\n"
                    + "Result: 1 error(s), 0 warning(s), 3 msec elapsed\n";

    public void testDecodesLittleEndianWithoutBom() {
        // MetaEditor's actual output on Windows; the JVM default would mis-read this as big-endian.
        byte[] leNoBom = LOG.getBytes(StandardCharsets.UTF_16LE);
        assertEquals(LOG, MqlCompilerService.decodeMqlLog(leNoBom));
        // And it parses to a real diagnostic, not silence.
        assertEquals(1, CompilerOutputParser.parse(MqlCompilerService.decodeMqlLog(leNoBom)).size());
    }

    public void testDecodesLittleEndianWithBom() {
        byte[] leBom = withBom(new byte[]{(byte) 0xFF, (byte) 0xFE}, LOG.getBytes(StandardCharsets.UTF_16LE));
        assertEquals(LOG, MqlCompilerService.decodeMqlLog(leBom));
    }

    public void testDecodesBigEndianWithBom() {
        // Java's UTF_16 encoder emits BE-with-BOM; a log produced that way must still read back cleanly.
        byte[] beBom = LOG.getBytes(StandardCharsets.UTF_16);
        assertEquals(LOG, MqlCompilerService.decodeMqlLog(beBom));
    }

    public void testEmptyInputIsSafe() {
        assertEquals("", MqlCompilerService.decodeMqlLog(new byte[0]));
    }

    private static byte[] withBom(byte[] bom, byte[] body) {
        byte[] out = new byte[bom.length + body.length];
        System.arraycopy(bom, 0, out, 0, bom.length);
        System.arraycopy(body, 0, out, bom.length, body.length);
        return out;
    }
}

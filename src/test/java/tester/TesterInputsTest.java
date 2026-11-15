/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package tester;

import com.limemojito.oss.mql.tester.TesterInputs;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

class TesterInputsTest {

    /** A .set as MetaTrader saves it: UTF-16LE with a byte-order mark, CRLF, ; comments, optimisation ranges. */
    private static byte[] utf16Set(String text) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        out.write(0xFF);
        out.write(0xFE);
        out.writeBytes(text.replace("\n", "\r\n").getBytes(StandardCharsets.UTF_16LE));
        return out.toByteArray();
    }

    @Test
    void readsAMetaTraderSetFile() {
        String text = TesterInputs.decode(utf16Set("""
                ; saved on 2026.07.24 10:00:00
                ; this file contains input parameters for testing/optimizing RIGGWIRE_FINAL expert advisor
                ;
                TC_ExtremeLevel=75||45||5||95||N
                EntryUsesTC=false||false||0||true||N
                InpComment=a=b
                """));
        assertThat(TesterInputs.entries(text)).extracting(TesterInputs.Entry::name)
                .containsExactly("TC_ExtremeLevel", "EntryUsesTC", "InpComment");
        assertThat(TesterInputs.entries(text).get(0).value()).isEqualTo("75");
        assertThat(TesterInputs.entries(text).get(2).value()).isEqualTo("a=b");
        assertThat(TesterInputs.testerSection(text))
                .isEqualTo("TC_ExtremeLevel=75||45||5||95||N\nEntryUsesTC=false||false||0||true||N\nInpComment=a=b\n");
    }

    @Test
    void plainNameValueLinesPassThroughAndTheLastOneWins() {
        String text = TesterInputs.decode("﻿Risk=1.0\nRisk=0.5\n\njunk line\n".getBytes(StandardCharsets.UTF_8));
        assertThat(TesterInputs.testerSection(text)).isEqualTo("Risk=0.5\n");
    }
}

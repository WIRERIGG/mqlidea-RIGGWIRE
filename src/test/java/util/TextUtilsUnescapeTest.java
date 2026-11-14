/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package util;

import com.intellij.xml.util.XmlUtil;
import com.limemojito.oss.mql.util.TextUtils;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * {@link TextUtils#unescape} replaced the platform's {@code XmlUtil.unescape}, which CLion 2026.3
 * no longer exposes to this plugin. The index keys it produces must not change, so it is checked
 * against the original on the test platform, where {@code XmlUtil} is still available.
 */
class TextUtilsUnescapeTest {

    @Test
    void matchesXmlUtilUnescape() {
        String[] inputs = {"", "OnTick", "CTrade", "a&lt;b", "&gt;&apos;&quot;", "&amp;lt;", "&amp;amp;",
                "&", "&unknown;", "x &amp y", "&lt&gt;"};
        for (String in : inputs) {
            assertThat(TextUtils.unescape(in)).as(in).isEqualTo(XmlUtil.unescape(in));
        }
    }

    @Test
    void nullStaysNull() {
        assertThat(TextUtils.unescape(null)).isNull();
    }
}

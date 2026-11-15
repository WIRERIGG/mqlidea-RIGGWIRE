/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.openapi.util.JDOMExternalizerUtil;
import com.intellij.openapi.util.JDOMUtil;
import junit.framework.TestCase;
import org.jdom.Element;

/**
 * The run configuration's own {@code <tag value="..."/>} helpers replace the deprecated
 * {@code JDOMExternalizerUtil.addElementWithValueAttribute} / {@code getFirstChildValueAttribute}.
 * They must write the same XML and read it back the same way, or configurations saved by earlier
 * versions would lose their SDK, file and encoding settings.
 */
public class RunConfigXmlParityTest extends TestCase {

    private static final String[] VALUES = {"MetaTrader 5", "Experts/My EA.mq5", "", null};

    @SuppressWarnings("deprecation") // the deprecated helpers are the reference being matched
    public void testWritesTheSameXmlAsTheDeprecatedHelper() {
        Element ours = new Element("configuration");
        Element theirs = new Element("configuration");
        for (int i = 0; i < VALUES.length; i++) {
            MQL4RunCompilerConfiguration.writeValueChild(ours, "tag" + i, VALUES[i]);
            JDOMExternalizerUtil.addElementWithValueAttribute(theirs, "tag" + i, VALUES[i]);
        }
        assertEquals(JDOMUtil.writeElement(theirs), JDOMUtil.writeElement(ours));
    }

    @SuppressWarnings("deprecation")
    public void testReadsTheSameValuesAsTheDeprecatedHelper() {
        Element saved = new Element("configuration");
        for (int i = 0; i < VALUES.length; i++) {
            JDOMExternalizerUtil.addElementWithValueAttribute(saved, "tag" + i, VALUES[i]);
        }
        for (int i = 0; i < VALUES.length; i++) {
            assertEquals(JDOMExternalizerUtil.getFirstChildValueAttribute(saved, "tag" + i),
                    MQL4RunCompilerConfiguration.readValueChild(saved, "tag" + i));
        }
        assertNull("a missing tag reads as null", MQL4RunCompilerConfiguration.readValueChild(saved, "absent"));
    }
}

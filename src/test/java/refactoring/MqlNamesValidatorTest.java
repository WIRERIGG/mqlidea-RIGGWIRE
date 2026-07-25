/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package refactoring;

import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.refactoring.MqlNamesValidator;

/**
 * Phase 1 (REVAMP_PLAN.md) test for {@link MqlNamesValidator}: legal vs illegal identifier
 * spelling, and reserved-keyword detection backed by the bundled {@code mql4-keywords.json}
 * catalog.
 */
public class MqlNamesValidatorTest extends BasePlatformTestCase {

    private final MqlNamesValidator validator = new MqlNamesValidator();

    public void testValidIdentifier() {
        assertTrue(validator.isIdentifier("g_x", getProject()));
    }

    public void testIdentifierCannotStartWithDigit() {
        assertFalse(validator.isIdentifier("2x", getProject()));
    }

    public void testIdentifierCannotContainSpace() {
        assertFalse(validator.isIdentifier("my name", getProject()));
    }

    public void testRealKeywordIsRecognised() {
        assertTrue(validator.isKeyword("if", getProject()));
        assertTrue(validator.isKeyword("class", getProject()));
    }

    public void testKeywordIsNotAValidIdentifier() {
        assertFalse(validator.isIdentifier("if", getProject()));
    }

    public void testOrdinaryWordIsNotAKeyword() {
        assertFalse(validator.isKeyword("g_x", getProject()));
    }
}

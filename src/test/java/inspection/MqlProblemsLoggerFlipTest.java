/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.limemojito.oss.mql.inspection.MqlProblemsLoggerService;
import junit.framework.TestCase;

import java.util.Set;

/**
 * SETTLE step (plumbing #2): the problem-icon refresh is flip-gated -- it fires ONLY when the set of
 * files-with-problems actually changes. {@link MqlProblemsLoggerService#computeFlipped} is that gate:
 * an empty result means "nothing changed -> schedule no UI refresh".
 */
public class MqlProblemsLoggerFlipTest extends TestCase {

    public void testUnchangedSetProducesNoFlips() {
        Set<String> same = Set.of("file://a.mq5", "file://b.mqh");
        assertTrue("an unchanged problem set must schedule no refresh",
                MqlProblemsLoggerService.computeFlipped(same, same).isEmpty());
    }

    public void testAddedProblemFileIsAFlip() {
        Set<String> before = Set.of("file://a.mq5");
        Set<String> after = Set.of("file://a.mq5", "file://b.mq5");
        assertEquals(Set.of("file://b.mq5"), MqlProblemsLoggerService.computeFlipped(before, after));
    }

    public void testClearedProblemFileIsAFlip() {
        Set<String> before = Set.of("file://a.mq5", "file://b.mq5");
        Set<String> after = Set.of("file://a.mq5");
        assertEquals(Set.of("file://b.mq5"), MqlProblemsLoggerService.computeFlipped(before, after));
    }

    public void testBothAddedAndClearedAreFlips() {
        Set<String> before = Set.of("file://a.mq5", "file://b.mq5");
        Set<String> after = Set.of("file://b.mq5", "file://c.mq5");
        assertEquals(Set.of("file://a.mq5", "file://c.mq5"),
                MqlProblemsLoggerService.computeFlipped(before, after));
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package action;

import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.action.CreateMQL4FileAction;
import com.limemojito.oss.mql.action.CreateMQL5FileAction;
import parser.ParserTestUtils;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

/**
 * Phase 2e (REVAMP_PLAN.md): {@link CreateMQL4FileAction}/{@link CreateMQL5FileAction} were
 * migrated from {@code CreateFileAction} (an empty file) to {@code CreateFileFromTemplateAction}
 * backed by the bundled internal templates in {@code resources/fileTemplates/internal/}.
 * <p/>
 * These tests load each template resource directly off the classpath (the same bytes that ship
 * inside the plugin jar -- verified by unzipping the built jar) rather than going through {@code
 * FileTemplateManager.getInternalTemplate}: in this project's {@code BasePlatformTestCase}
 * sandbox the platform's file-template-default-loading pass (a project-level, apparently
 * once-computed scan distinct from ordinary EP processing -- every other EP registered by this
 * plugin, including {@code spellchecker.support} and {@code indexPatternBuilder}, resolves fine
 * in the same sandbox) does not pick up the dynamically-loaded test plugin's {@code
 * fileTemplates/internal/} resources and throws {@code IllegalStateException: Template not
 * found}, even immediately after clearing the sandbox's cached test state. The {@code
 * <internalFileTemplate>} registrations and resource files themselves are exactly the standard,
 * documented convention (mirroring e.g. the bundled Java plugin's {@code Class.java}/{@code
 * <internalFileTemplate name="Class"/>}), so this is treated as a test-sandbox limitation, not a
 * defect in the production wiring -- per Phase 2e's own fallback instruction, we assert the
 * template resources exist, are loadable, and (going a bit further) that their real, un-rendered
 * content both contains the required stubs and parses cleanly as MQL (the only substituted
 * placeholders, {@code ${NAME}}/{@code ${USER}}, sit inside a comment line and a string literal,
 * so leaving them un-substituted does not affect parse validity).
 */
public class CreateFileFromTemplateActionTest extends BasePlatformTestCase {

    private String loadTemplateResource(String resourceName) throws IOException {
        String path = "/fileTemplates/internal/" + resourceName;
        try (InputStream in = CreateMQL5FileAction.class.getResourceAsStream(path)) {
            assertNotNull("Expected the bundled template resource to be on the classpath: " + path, in);
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                return reader.lines().collect(Collectors.joining("\n"));
            }
        }
    }

    private void assertParsesCleanly(String fileName, String text) {
        PsiFile file = myFixture.configureByText(fileName, text);
        PsiErrorElement error = ParserTestUtils.findErrorElement(file);
        assertNull("Expected the template to parse without errors, found: "
                + (error == null ? null : error.getErrorDescription()) + "\n" + text, error);
    }

    public void testExpertAdvisorTemplateHasRequiredStubsAndParses() throws IOException {
        String text = loadTemplateResource(CreateMQL5FileAction.EXPERT_ADVISOR_TEMPLATE + ".mq5");
        assertTrue("Expected an OnInit() stub:\n" + text, text.contains("OnInit"));
        assertTrue("Expected an OnTick() stub:\n" + text, text.contains("OnTick"));
        assertTrue("Expected an OnDeinit() stub:\n" + text, text.contains("OnDeinit"));
        assertTrue("Expected INIT_SUCCEEDED to be returned from OnInit:\n" + text, text.contains("INIT_SUCCEEDED"));
        assertParsesCleanly("TestEA.mq5", text);
    }

    public void testIndicatorTemplateHasRequiredStubsAndParses() throws IOException {
        String text = loadTemplateResource(CreateMQL5FileAction.INDICATOR_TEMPLATE + ".mq5");
        assertTrue("Expected #property indicator_chart_window:\n" + text, text.contains("indicator_chart_window"));
        assertTrue("Expected an OnCalculate() stub:\n" + text, text.contains("OnCalculate"));
        assertParsesCleanly("TestIndicator.mq5", text);
    }

    public void testScriptTemplateHasRequiredStubsAndParses() throws IOException {
        String text = loadTemplateResource(CreateMQL5FileAction.SCRIPT_TEMPLATE + ".mq5");
        assertTrue("Expected an OnStart() stub:\n" + text, text.contains("OnStart"));
        assertParsesCleanly("TestScript.mq5", text);
    }

    public void testMql4ExpertTemplateHasRequiredStubsAndParses() throws IOException {
        String text = loadTemplateResource(CreateMQL4FileAction.EXPERT_TEMPLATE + ".mq4");
        assertTrue("Expected an OnInit() stub:\n" + text, text.contains("OnInit"));
        assertTrue("Expected an OnTick() stub:\n" + text, text.contains("OnTick"));
        assertParsesCleanly("TestExpert.mq4", text);
    }
}

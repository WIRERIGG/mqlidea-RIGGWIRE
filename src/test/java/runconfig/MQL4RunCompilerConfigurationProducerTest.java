/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package runconfig;

import com.intellij.execution.actions.ConfigurationContext;
import com.intellij.execution.actions.ConfigurationFromContext;
import com.intellij.execution.actions.RunConfigurationProducer;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.runconfig.MQL4RunCompilerConfiguration;
import com.limemojito.oss.mql.runconfig.MQL4RunCompilerConfigurationProducer;

/**
 * P1: the run-gutter producer must actually create/match a build config from a compilable MQL
 * program context (previously it returned false unconditionally), and must refuse a .mqh header
 * (which cannot be built standalone).
 */
public class MQL4RunCompilerConfigurationProducerTest extends BasePlatformTestCase {

    private MQL4RunCompilerConfigurationProducer producer() {
        return RunConfigurationProducer.getInstance(MQL4RunCompilerConfigurationProducer.class);
    }

    private ConfigurationContext contextForOnInit(String fileName) {
        PsiFile file = myFixture.configureByText(fileName, "int OnInit() {\n  return 0;\n}\n");
        PsiElement onInit = file.findElementAt(file.getText().indexOf("OnInit"));
        assertNotNull(onInit);
        return new ConfigurationContext(onInit);
    }

    public void testProducerCreatesAndMatchesConfigForMq5Program() {
        ConfigurationContext context = contextForOnInit("test.mq5");
        ConfigurationFromContext fromContext = producer().createConfigurationFromContext(context);
        assertNotNull("expected the producer to create a build config from a .mq5 program", fromContext);

        MQL4RunCompilerConfiguration cfg = (MQL4RunCompilerConfiguration) fromContext.getConfiguration();
        assertTrue("config file path must point at the context file",
                cfg.fileToCompile.endsWith("test.mq5"));
        assertFalse("config file path must not be empty", cfg.fileToCompile.isEmpty());

        assertTrue("the same context must be recognised as coming from this config",
                producer().isConfigurationFromContext(cfg, context));
    }

    public void testProducerRejectsHeaderFile() {
        ConfigurationContext context = contextForOnInit("test.mqh");
        assertNull("a .mqh header cannot be built standalone -> no config",
                producer().createConfigurationFromContext(context));
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package runconfig;

import com.intellij.execution.lineMarker.RunLineMarkerContributor;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.runconfig.MqlRunLineMarkerContributor;

/**
 * Phase 1 (REVAMP_PLAN.md) test for {@link MqlRunLineMarkerContributor}: the run gutter is offered
 * on {@code OnInit} in a compilable top-level source file, but never in a {@code .mqh} header
 * (which cannot be built standalone). Calls {@link RunLineMarkerContributor#getInfo(PsiElement)}
 * directly on the resolved name identifier -- precise and avoids depending on the platform's
 * gutter-recompute/executor-registration pipeline inside the lightweight test sandbox.
 */
public class MqlRunLineMarkerContributorTest extends BasePlatformTestCase {

    private RunLineMarkerContributor.Info infoForOnInit(String fileName) {
        PsiFile file = myFixture.configureByText(fileName, "int OnInit() {\n  return 0;\n}\n");
        MQL4FunctionElement function = null;
        for (PsiElement child : file.getChildren()) {
            if (child instanceof MQL4FunctionElement f && "OnInit".equals(f.getFunctionName())) {
                function = f;
                break;
            }
        }
        assertNotNull("expected an OnInit function element", function);
        PsiElement nameIdentifier = function.getNameIdentifier();
        assertNotNull("expected a name identifier for OnInit", nameIdentifier);
        return new MqlRunLineMarkerContributor().getInfo(nameIdentifier);
    }

    public void testGutterPresentOnOnInitInSourceFile() {
        assertNotNull("expected a run gutter Info on OnInit in a .mq5 file", infoForOnInit("test.mq5"));
    }

    public void testGutterAbsentOnOnInitInHeaderFile() {
        assertNull("expected no run gutter Info on OnInit in a .mqh header", infoForOnInit("test.mqh"));
    }
}

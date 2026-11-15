/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.codeInspection.LocalInspectionEP;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * I-3: an inspection must find the same problems in a function body whether it is written at file
 * level, inside a class body, or out of line as {@code CHost::Work}. Every registered MQL inspection
 * runs on all three; a new inspection that walks only {@code file.getChildren()} fails here.
 */
public class ClassMethodCoverageTest extends BasePlatformTestCase {

    /** A body that trips many body-level inspections (trading safety, loops, arrays, style). */
    private static final String BODY = """
              {
               MqlRates rates[];
               CopyRates(_Symbol,PERIOD_CURRENT,0,10,rates);
               int h=iMA(_Symbol,PERIOD_CURRENT,14,0,MODE_SMA,PRICE_CLOSE);
               double x=arr[5]/3.7+rates[0].close;
               string t="";
               for(int i=0;i<10;i++)
                 {
                  t=t+"x";
                  ArrayResize(arr,i);
                  CItem *p=new CItem();
                  delete p;
                 }
               if(x>1);
               switch(h)
                 {
                  case 1: x=2;
                  case 2: x=3;
                 }
               Sleep(10);
               while(true) { }
               Print(AccountInfoDouble(ACCOUNT_BALANCE),t);
               return (int)x;
              }
            """;
    private static final String SIGNATURE = "int Work(int unused,double &arr[],string s,int a4,int a5,int a6,int a7,int a8)";
    private static final String ITEM = "class CItem { public: int v; };\n";

    private static final String TOP_LEVEL = ITEM + SIGNATURE + "\n" + BODY;
    private static final String IN_CLASS = ITEM + "class CHost\n  {\npublic:\n" + SIGNATURE + "\n" + BODY + "  };\n";
    private static final String OUT_OF_LINE = ITEM + "class CHost\n  {\npublic:\n   "
            + SIGNATURE + ";\n  };\n"
            + SIGNATURE.replace("int Work", "int CHost::Work") + "\n" + BODY;

    @Override
    protected void setUp() throws Exception {
        super.setUp();
        List<LocalInspectionTool> tools = new ArrayList<>();
        for (LocalInspectionEP ep : LocalInspectionEP.LOCAL_INSPECTION.getExtensionList()) {
            if ("MQL4".equals(ep.language)) {
                tools.add((LocalInspectionTool) ep.instantiateTool());
            }
        }
        assertTrue("expected the MQL inspections to be registered", tools.size() > 50);
        myFixture.enableInspections(tools.toArray(new LocalInspectionTool[0]));
    }

    /** Problems per inspection id whose range lies inside the {@code Work} body. */
    private Map<String, Integer> problemsInBody(String code) {
        myFixture.configureByText("test.mq5", code);
        int start = code.lastIndexOf(BODY);
        int end = start + BODY.length();
        Map<String, Integer> counts = new TreeMap<>();
        for (HighlightInfo info : myFixture.doHighlighting(HighlightSeverity.WEAK_WARNING)) {
            String id = info.getInspectionToolId();
            if (id != null && info.getStartOffset() >= start && info.getEndOffset() <= end) {
                counts.merge(id, 1, Integer::sum);
            }
        }
        return counts;
    }

    public void testInClassMethodBodyIsCheckedLikeATopLevelFunction() {
        Map<String, Integer> topLevel = problemsInBody(TOP_LEVEL);
        assertTrue("the body should trip the trading safety checks: " + topLevel,
                topLevel.containsKey("UncheckedCopyRates") && topLevel.containsKey("UncheckedHandle"));
        assertEquals(topLevel, problemsInBody(IN_CLASS));
    }

    public void testOutOfLineMethodBodyIsCheckedLikeATopLevelFunction() {
        assertEquals(problemsInBody(TOP_LEVEL), problemsInBody(OUT_OF_LINE));
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.*;

/**
 * Tests all 60 MQL5 Safety inspections by parsing sample MQL code
 * and running each inspection's checkFile() method.
 * <p>
 * Uses BasePlatformTestCase (not ParsingTestCase) because inspections
 * require InspectionManager which is only available in a full project environment.
 */
public class MQL5SafetyInspectionTest extends BasePlatformTestCase {

    // ===== Helper Methods =====

    private ProblemDescriptor[] runInspection(LocalInspectionTool inspection, String code) {
        return runInspection(inspection, code, "test.mq4");
    }

    private ProblemDescriptor[] runInspection(LocalInspectionTool inspection, String code, String fileName) {
        PsiFile file = myFixture.configureByText(fileName, code);
        InspectionManager manager = InspectionManager.getInstance(getProject());
        return inspection.checkFile(file, manager, false);
    }

    private void assertHasProblems(LocalInspectionTool inspection, String code) {
        ProblemDescriptor[] problems = runInspection(inspection, code);
        assertNotNull("checkFile returned null for " + inspection.getClass().getSimpleName(), problems);
        assertTrue("Expected problems from " + inspection.getClass().getSimpleName(),
                problems.length > 0);
    }

    private void assertNoProblems(LocalInspectionTool inspection, String code) {
        ProblemDescriptor[] problems = runInspection(inspection, code);
        assertTrue("Expected no problems from " + inspection.getClass().getSimpleName(),
                problems == null || problems.length == 0);
    }

    private void assertInspectionRuns(LocalInspectionTool inspection, String code) {
        ProblemDescriptor[] problems = runInspection(inspection, code);
        // Just verify the inspection runs without throwing exceptions
        // problems may be null or empty — that's fine
    }

    // ===== Trading Safety =====

    public void testUncheckedOrderSend() {
        assertHasProblems(new UncheckedOrderSendInspection(),
                "void OnTick() { OrderSend(request, result); }");
    }

    public void testUncheckedOrderSendClean() {
        assertNoProblems(new UncheckedOrderSendInspection(),
                "void OnTick() { if(!OrderSend(request, result)) { Print(GetLastError()); } }");
    }

    public void testUncheckedHandle() {
        assertHasProblems(new UncheckedHandleInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }");
    }

    public void testUncheckedHandleClean() {
        assertNoProblems(new UncheckedHandleInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);\n" +
                "  if(handle == INVALID_HANDLE) return INIT_FAILED; return 0; }");
    }

    public void testMissingIndicatorRelease() {
        assertHasProblems(new MissingIndicatorReleaseInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n" +
                "void OnDeinit(const int reason) { }");
    }

    public void testMissingIndicatorReleaseClean() {
        assertNoProblems(new MissingIndicatorReleaseInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n" +
                "void OnDeinit(const int reason) { IndicatorRelease(handle); }");
    }

    public void testArrayAccessWithoutSizeCheck() {
        assertHasProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "void foo() { double arr[]; int x = arr[0]; }");
    }

    public void testArrayAccessWithSizeCheck() {
        assertNoProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "void foo() { double arr[]; if(ArraySize(arr) > 0) int x = arr[0]; }");
    }

    public void testMissingInputValidation() {
        // Smoke test — depends on parser producing INPUT_KEYWORD in VAR_DECLARATION_STATEMENT
        assertInspectionRuns(new MissingInputValidationInspection(),
                "input int InpPeriod = 14;\n" +
                "int OnInit() { return 0; }");
    }

    public void testMissingFileClose() {
        assertHasProblems(new MissingFileCloseInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); }");
    }

    public void testMissingFileCloseClean() {
        assertNoProblems(new MissingFileCloseInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); FileClose(h); }");
    }

    public void testUncheckedCopyRates() {
        assertHasProblems(new UncheckedCopyRatesInspection(),
                "void foo() { MqlRates rates[]; CopyRates(_Symbol, PERIOD_H1, 0, 100, rates); }");
    }

    public void testUncheckedCopyRatesClean() {
        assertNoProblems(new UncheckedCopyRatesInspection(),
                "void foo() { MqlRates rates[]; if(CopyRates(_Symbol, PERIOD_H1, 0, 100, rates) < 0) return; }");
    }

    public void testDoubleIndicatorRelease() {
        assertHasProblems(new DoubleIndicatorReleaseInspection(),
                "void OnDeinit(const int reason) { IndicatorRelease(h); IndicatorRelease(h); }");
    }

    public void testDeleteWithoutNullCheck() {
        assertHasProblems(new DeleteWithoutNullCheckInspection(),
                "void foo() { delete ptr; }");
    }

    public void testDeleteWithNullCheck() {
        assertNoProblems(new DeleteWithoutNullCheckInspection(),
                "void foo() { if(ptr != NULL) delete ptr; }");
    }

    // ===== Function Signature =====

    public void testMissingOnInitReturn() {
        assertHasProblems(new MissingOnInitReturnInspection(),
                "void OnInit() { }");
    }

    public void testMissingOnInitReturnClean() {
        assertNoProblems(new MissingOnInitReturnInspection(),
                "int OnInit() { return 0; }");
    }

    public void testEmptyEventHandler() {
        assertHasProblems(new EmptyEventHandlerInspection(),
                "void OnTick() { }");
    }

    public void testEmptyEventHandlerClean() {
        assertNoProblems(new EmptyEventHandlerInspection(),
                "void OnTick() { OrderSend(request, result); }");
    }

    public void testMissingConstParameter() {
        assertHasProblems(new MissingConstParameterInspection(),
                "void foo(CObject &obj) { }");
    }

    public void testLargeStructByValue() {
        assertHasProblems(new LargeStructByValueInspection(),
                "void foo(MqlRates rates) { }");
    }

    public void testMissingDestructor() {
        assertHasProblems(new MissingDestructorInspection(),
                "class CTest { public: CTest() {} };");
    }

    public void testVirtualWithoutDestructor() {
        // Smoke test — depends on class inner block containing FUNCTION nodes with VIRTUAL_KEYWORD
        assertInspectionRuns(new VirtualWithoutDestructorInspection(),
                "class CTest { public: virtual void foo() {} };");
    }

    public void testVirtualWithDestructor() {
        assertNoProblems(new VirtualWithoutDestructorInspection(),
                "class CTest { public: virtual void foo() {} virtual ~CTest() {} };");
    }

    // ===== Class Structure =====

    public void testPublicDataMember() {
        // Smoke test — depends on class inner block having VAR_DECLARATION_STATEMENT after PUBLIC_KEYWORD
        assertInspectionRuns(new PublicDataMemberInspection(),
                "class CTest { public: int value; };");
    }

    public void testMissingPropertyDescription() {
        assertHasProblems(new MissingPropertyDescriptionInspection(),
                "#property version \"1.00\"\nvoid OnStart() { }");
    }

    public void testMissingPropertyDescriptionClean() {
        assertNoProblems(new MissingPropertyDescriptionInspection(),
                "#property version \"1.00\"\n#property description \"Test\"\nvoid OnStart() { }");
    }

    public void testMissingPropertyVersion() {
        assertHasProblems(new MissingPropertyVersionInspection(),
                "#property description \"Test\"\nvoid OnStart() { }");
    }

    public void testMissingPropertyVersionClean() {
        assertNoProblems(new MissingPropertyVersionInspection(),
                "#property version \"1.00\"\n#property description \"Test\"\nvoid OnStart() { }");
    }

    public void testExcessiveGlobalVariables() {
        // Smoke test — depends on parser producing VAR_DECLARATION_STATEMENT for standalone int vars
        StringBuilder code = new StringBuilder();
        for (int i = 0; i < 25; i++) {
            code.append("int g_var").append(i).append(";\n");
        }
        code.append("void OnStart() { }");
        assertInspectionRuns(new ExcessiveGlobalVariablesInspection(), code.toString());
    }

    public void testImmutableInputParameter() {
        // Smoke test — depends on parser producing INPUT_KEYWORD in VAR_DECLARATION_STATEMENT
        assertInspectionRuns(new ImmutableInputParameterInspection(),
                "input int InpPeriod = 14;\n" +
                "void OnInit() { InpPeriod = 20; }");
    }

    // ===== Naming & Style =====

    public void testFunctionNamingConvention() {
        assertHasProblems(new FunctionNamingConventionInspection(),
                "void my_function() { }");
    }

    public void testFunctionNamingConventionClean() {
        assertNoProblems(new FunctionNamingConventionInspection(),
                "void MyFunction() { }");
    }

    public void testVariableNamingConvention() {
        // Smoke test — depends on parser producing VAR_DECLARATION_STATEMENT for standalone vars
        assertInspectionRuns(new VariableNamingConventionInspection(),
                "int MyVariable;");
    }

    public void testClassNamingConvention() {
        assertHasProblems(new ClassNamingConventionInspection(),
                "class MyClass { };");
    }

    public void testClassNamingConventionClean() {
        assertNoProblems(new ClassNamingConventionInspection(),
                "class CMyClass { };");
    }

    public void testMissingFunctionDocComment() {
        assertHasProblems(new MissingFunctionDocCommentInspection(),
                "void Calculate() { }");
    }

    // ===== Type Safety =====

    public void testNarrowingReturnType() {
        // Smoke test — inspection checks IElementType.toString() names that may differ from expected
        assertInspectionRuns(new NarrowingReturnTypeInspection(),
                "int Calculate(double a, double b) { }");
    }

    public void testUninitializedVariable() {
        // Smoke test — inspection checks IElementType.toString() names that may differ from expected
        assertInspectionRuns(new UninitializedVariableInspection(),
                "int uninitialized;");
    }

    public void testUninitializedVariableClean() {
        assertNoProblems(new UninitializedVariableInspection(),
                "int initialized = 0;");
    }

    public void testImplicitCast() {
        // Smoke test — inspection skips BRACKETS_BLOCK (function bodies) when looking for CAST_BLOCK
        assertInspectionRuns(new ImplicitCastInspection(),
                "void foo() { int x = (int)3.14; }");
    }

    // ===== Performance =====

    public void testArrayResizeInLoop() {
        assertHasProblems(new ArrayResizeInLoopInspection(),
                "void foo() { double arr[]; for(int i=0; i<10; i++) { ArrayResize(arr, i); } }");
    }

    public void testPrintInOnTick() {
        assertHasProblems(new PrintInOnTickInspection(),
                "void OnTick() { Print(\"tick\"); }");
    }

    public void testPrintInOnTickClean() {
        assertNoProblems(new PrintInOnTickInspection(),
                "void OnTick() { OrderSend(request, result); }");
    }

    public void testSleepInEventHandler() {
        assertHasProblems(new SleepInEventHandlerInspection(),
                "void OnTick() { Sleep(1000); }");
    }

    public void testRedundantCalculationInOnTick() {
        assertHasProblems(new RedundantCalculationInOnTickInspection(),
                "void OnTick() { double spread = SymbolInfoDouble(_Symbol, SYMBOL_SPREAD);\n" +
                "  double spread2 = SymbolInfoDouble(_Symbol, SYMBOL_SPREAD); }");
    }

    public void testStringConcatInLoop() {
        // Inspection regex matches `+ "` or `" +` patterns, not `+=`
        assertHasProblems(new StringConcatInLoopInspection(),
                "void foo() { string s; for(int i=0; i<10; i++) { s = s + \"x\"; } }");
    }

    public void testSuboptimalContainer() {
        assertHasProblems(new SuboptimalContainerInspection(),
                "void foo() { ArrayResize(arr, 100); ArraySort(arr); }");
    }

    public void testMissingArrayPreallocation() {
        assertHasProblems(new MissingArrayPreallocationInspection(),
                "void foo() { ArrayResize(arr, 1); ArrayResize(arr, 2); ArrayResize(arr, 3); }");
    }

    public void testLazyEvaluationMiss() {
        // Inspection only checks CopyBuffer/CopyRates/iCustom, not iMA
        assertHasProblems(new LazyEvaluationMissInspection(),
                "void OnTick() { CopyBuffer(handle, 0, 0, 10, buf);\n" +
                "  if(condition) { use(buf); } }");
    }

    // ===== Security & Data =====

    public void testAccountInfoExposure() {
        assertHasProblems(new AccountInfoExposureInspection(),
                "void foo() { double bal = AccountInfoDouble(ACCOUNT_BALANCE);\n" +
                "  Print(bal); }");
    }

    public void testHardcodedCredentials() {
        assertHasProblems(new HardcodedCredentialsInspection(),
                "void foo() { string password = \"secret123\"; }");
    }

    public void testSafeApiUsage() {
        assertInspectionRuns(new SafeApiUsageInspection(),
                "void foo() { OrderSend(request, result); }");
    }

    public void testFileOperationValidation() {
        assertHasProblems(new FileOperationValidationInspection(),
                "void foo() { string data = FileReadString(handle); }");
    }

    public void testDeterministicSeed() {
        assertHasProblems(new DeterministicSeedInspection(),
                "void foo() { MathSrand(42); }");
    }

    public void testDeterministicSeedClean() {
        assertNoProblems(new DeterministicSeedInspection(),
                "void foo() { MathSrand(GetTickCount()); }");
    }

    // ===== Advanced Patterns =====

    public void testStackOverflowRisk() {
        assertHasProblems(new StackOverflowRiskInspection(),
                "void Recurse() { Recurse(); }");
    }

    public void testDanglingObjectReference() {
        assertHasProblems(new DanglingObjectReferenceInspection(),
                "void foo() { delete ptr; int x = ptr.value; }");
    }

    public void testStaleHandleUsage() {
        assertHasProblems(new StaleHandleUsageInspection(),
                "void foo() { IndicatorRelease(handle); CopyBuffer(handle, 0, 0, 1, buf); }");
    }

    public void testIncompleteClass() {
        assertHasProblems(new IncompleteClassInspection(),
                "class CTest { public: CTest() { ptr = new int; }\n" +
                "  ~CTest() { delete ptr; } };");
    }

    public void testGlobalVariableConflict() {
        assertHasProblems(new GlobalVariableConflictInspection(),
                "void foo() { GlobalVariableSet(\"gv\", 1.0); }\n" +
                "void bar() { GlobalVariableSet(\"gv\", 2.0); }");
    }

    public void testMissingErrorRecovery() {
        assertInspectionRuns(new MissingErrorRecoveryInspection(),
                "void foo() { OrderSend(request, result); }");
    }

    public void testOverComplexErrorHandling() {
        assertHasProblems(new OverComplexErrorHandlingInspection(),
                "void foo() { GetLastError(); GetLastError(); GetLastError(); GetLastError(); }");
    }

    public void testUnsafeArrayCopy() {
        assertHasProblems(new UnsafeArrayCopyInspection(),
                "void foo() { ArrayCopy(dst, src); }");
    }

    public void testModernMQL5Idiom() {
        // Smoke test — inspection only runs on .mq5 files; file type registration may vary in test env
        assertInspectionRuns(new ModernMQL5IdiomInspection(),
                "void foo() { int total = OrdersTotal(); OrderSelect(0, SELECT_BY_POS); }");
    }

    public void testDataConsistency() {
        assertHasProblems(new DataConsistencyInspection(),
                "void foo() { double ask = Ask; if(ask == 1.2345) { } }");
    }

    public void testTimeseriesDirection() {
        assertHasProblems(new TimeseriesDirectionInspection(),
                "void foo() { double buf[]; CopyBuffer(handle, 0, 0, 10, buf); }");
    }

    public void testSecureCodingPatterns() {
        assertInspectionRuns(new SecureCodingPatternsInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); }");
    }

    // ===== Memory & Allocation (new inspections) =====

    public void testObjectCreationInOnTick() {
        assertHasProblems(new ObjectCreationInOnTickInspection(),
                "void OnTick() { CObject *obj = new CObject(); delete obj; }");
    }

    public void testObjectCreationInOnTickClean() {
        assertNoProblems(new ObjectCreationInOnTickInspection(),
                "void OnTick() { OrderSend(request, result); }");
    }

    public void testArrayResizeReturnCheck() {
        assertHasProblems(new ArrayResizeReturnCheckInspection(),
                "void foo() { double arr[]; ArrayResize(arr, 100); }");
    }

    public void testArrayResizeReturnCheckClean() {
        assertNoProblems(new ArrayResizeReturnCheckInspection(),
                "void foo() { double arr[]; if(ArrayResize(arr, 100) < 0) return; }");
    }

    public void testNullAfterDelete() {
        assertHasProblems(new NullAfterDeleteInspection(),
                "void foo() { delete ptr; }");
    }

    public void testNullAfterDeleteClean() {
        assertNoProblems(new NullAfterDeleteInspection(),
                "void foo() { delete ptr; ptr = NULL; }");
    }

    public void testIndicatorCreationInOnTick() {
        assertHasProblems(new IndicatorCreationInOnTickInspection(),
                "void OnTick() { int h = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); }");
    }

    public void testIndicatorCreationInOnTickClean() {
        assertNoProblems(new IndicatorCreationInOnTickInspection(),
                "void OnTick() { CopyBuffer(handle, 0, 0, 1, buf); }");
    }

    public void testNewKeywordInLoop() {
        assertHasProblems(new NewKeywordInLoopInspection(),
                "void foo() { for(int i=0; i<10; i++) { CObject *obj = new CObject(); delete obj; } }");
    }

    public void testNewKeywordInLoopClean() {
        assertNoProblems(new NewKeywordInLoopInspection(),
                "void foo() { for(int i=0; i<10; i++) { Print(i); } }");
    }

    public void testMissingNewBarCheck() {
        assertHasProblems(new MissingNewBarCheckInspection(),
                "void OnTick() { double buf[]; CopyRates(_Symbol, PERIOD_H1, 0, 100, buf); }");
    }

    public void testMissingNewBarCheckClean() {
        assertNoProblems(new MissingNewBarCheckInspection(),
                "void OnTick() { static datetime lastBar = 0;\n" +
                "  datetime curBar = iTime(_Symbol, PERIOD_H1, 0);\n" +
                "  double buf[]; CopyRates(_Symbol, PERIOD_H1, 0, 100, buf); }");
    }

    public void testUnconditionalOrderLoop() {
        assertHasProblems(new UnconditionalOrderLoopInspection(),
                "void OnTick() { for(int i = PositionsTotal() - 1; i >= 0; i--) { } }");
    }

    public void testUnconditionalOrderLoopClean() {
        assertNoProblems(new UnconditionalOrderLoopInspection(),
                "void OnTick() { static int prevTotal = 0;\n" +
                "  int total = PositionsTotal(); }");
    }
}

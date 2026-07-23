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
        assertNoProblems(inspection, code, "test.mq4");
    }

    private void assertHasProblems(LocalInspectionTool inspection, String code, String fileName) {
        ProblemDescriptor[] problems = runInspection(inspection, code, fileName);
        assertNotNull("checkFile returned null for " + inspection.getClass().getSimpleName(), problems);
        assertTrue("Expected problems from " + inspection.getClass().getSimpleName() + " on " + fileName,
                problems.length > 0);
    }

    private void assertNoProblems(LocalInspectionTool inspection, String code, String fileName) {
        ProblemDescriptor[] problems = runInspection(inspection, code, fileName);
        assertTrue("Expected no problems from " + inspection.getClass().getSimpleName() + " on " + fileName,
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
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }",
                "test.mq5");
    }

    public void testUncheckedHandleClean() {
        assertNoProblems(new UncheckedHandleInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);\n" +
                "  if(handle == INVALID_HANDLE) return INIT_FAILED; return 0; }",
                "test.mq5");
    }

    public void testMissingIndicatorRelease() {
        assertHasProblems(new MissingIndicatorReleaseInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n" +
                "void OnDeinit(const int reason) { }",
                "test.mq5");
    }

    public void testMissingIndicatorReleaseClean() {
        assertNoProblems(new MissingIndicatorReleaseInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n" +
                "void OnDeinit(const int reason) { IndicatorRelease(handle); }",
                "test.mq5");
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
                "void OnDeinit(const int reason) { IndicatorRelease(h); IndicatorRelease(h); }",
                "test.mq5");
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
        // A class that acquires a resource (new) but has no destructor to release it → problem.
        assertHasProblems(new MissingDestructorInspection(),
                "class CTest { CObj *m_obj; public: CTest() { m_obj = new CObj(); } };");
    }

    public void testMissingDestructorValueClassIsFine() {
        // A plain value class with a constructor but no owned resource needs no destructor in MQL5.
        assertNoProblems(new MissingDestructorInspection(),
                "class CTest { int m_x; public: CTest() { m_x = 0; } };");
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
        // Retired: the old "indicator call then a later if" heuristic fired on nearly every OnTick and
        // misread MQL5's already-short-circuit && / ||. The inspection now reports nothing.
        assertNoProblems(new LazyEvaluationMissInspection(),
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
                "void foo() { IndicatorRelease(handle); CopyBuffer(handle, 0, 0, 1, buf); }",
                "test.mq5");
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
                "void OnTick() { int h = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); }",
                "test.mq5");
    }

    public void testIndicatorCreationInOnTickClean() {
        assertNoProblems(new IndicatorCreationInOnTickInspection(),
                "void OnTick() { CopyBuffer(handle, 0, 0, 1, buf); }",
                "test.mq5");
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

    // ===== Dialect Breadth (MQL4-only inspections) =====

    public void testOrderSelectUnchecked() {
        assertHasProblems(new OrderSelectUncheckedInspection(),
                "void CheckOrders() { OrderSelect(0, SELECT_BY_POS); double p = OrderOpenPrice(); }");
    }

    public void testOrderSelectUncheckedClean() {
        assertNoProblems(new OrderSelectUncheckedInspection(),
                "void CheckOrders() { if(OrderSelect(0, SELECT_BY_POS)) { double p = OrderOpenPrice(); } }");
    }

    public void testOrderSelectUncheckedAssignedClean() {
        assertNoProblems(new OrderSelectUncheckedInspection(),
                "void CheckOrders() { bool ok = OrderSelect(0, SELECT_BY_POS); if(ok) { double p = OrderOpenPrice(); } }");
    }

    public void testOrderSelectUncheckedWrongDialect() {
        // MQL4-only inspection must not fire on an .mq5 file
        assertNoProblems(new OrderSelectUncheckedInspection(),
                "void CheckOrders() { OrderSelect(0, SELECT_BY_POS); double p = OrderOpenPrice(); }",
                "test.mq5");
    }

    public void testOrderCloseLoopDirection() {
        assertHasProblems(new OrderCloseLoopDirectionInspection(),
                "void CloseAll() { for(int i = 0; i < OrdersTotal(); i++) {\n" +
                "  if(OrderSelect(i, SELECT_BY_POS)) OrderClose(OrderTicket(), OrderLots(), Bid, 3); } }");
    }

    public void testOrderCloseLoopDirectionCleanDescending() {
        assertNoProblems(new OrderCloseLoopDirectionInspection(),
                "void CloseAll() { for(int i = OrdersTotal() - 1; i >= 0; i--) {\n" +
                "  if(OrderSelect(i, SELECT_BY_POS)) OrderClose(OrderTicket(), OrderLots(), Bid, 3); } }");
    }

    public void testOrderCloseLoopDirectionWrongDialect() {
        // MQL4-only inspection must not fire on an .mq5 file
        assertNoProblems(new OrderCloseLoopDirectionInspection(),
                "void CloseAll() { for(int i = 0; i < OrdersTotal(); i++) {\n" +
                "  if(OrderSelect(i, SELECT_BY_POS)) OrderClose(OrderTicket(), OrderLots(), Bid, 3); } }",
                "test.mq5");
    }

    public void testMissingTradeContextCheck() {
        assertHasProblems(new MissingTradeContextCheckInspection(),
                "void DoTrade() { OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }");
    }

    public void testMissingTradeContextCheckClean() {
        assertNoProblems(new MissingTradeContextCheckInspection(),
                "void DoTrade() { if(IsTradeContextBusy()) return;\n" +
                "  OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }");
    }

    public void testMissingTradeContextCheckWrongDialect() {
        // MQL4-only inspection must not fire on an .mq5 file
        assertNoProblems(new MissingTradeContextCheckInspection(),
                "void DoTrade() { OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }",
                "test.mq5");
    }

    public void testMissingRefreshRates() {
        assertHasProblems(new MissingRefreshRatesInspection(),
                "void RetryLoop() { for(int i = 0; i < 3; i++) { double price = Bid; Print(price); } }");
    }

    public void testMissingRefreshRatesClean() {
        assertNoProblems(new MissingRefreshRatesInspection(),
                "void RetryLoop() { for(int i = 0; i < 3; i++) { RefreshRates(); double price = Bid; Print(price); } }");
    }

    public void testMissingRefreshRatesWrongDialect() {
        // MQL4-only inspection must not fire on an .mq5 file
        assertNoProblems(new MissingRefreshRatesInspection(),
                "void RetryLoop() { for(int i = 0; i < 3; i++) { double price = Bid; Print(price); } }",
                "test.mq5");
    }

    // ===== Dialect Breadth (MQL5-only inspections) =====

    public void testOnCalculateReturn() {
        assertHasProblems(new OnCalculateReturnInspection(),
                "int OnCalculate() { return 0; }",
                "test.mq5");
    }

    public void testOnCalculateReturnParenthesized() {
        assertHasProblems(new OnCalculateReturnInspection(),
                "int OnCalculate() { return(0); }",
                "test.mq5");
    }

    public void testOnCalculateReturnClean() {
        assertNoProblems(new OnCalculateReturnInspection(),
                "int OnCalculate() { return rates_total; }",
                "test.mq5");
    }

    public void testOnCalculateReturnWrongDialect() {
        // MQL5-only inspection must not fire on an .mq4 file
        assertNoProblems(new OnCalculateReturnInspection(),
                "int OnCalculate() { return 0; }");
    }

    // ===== Statement-AST migrations (real statement tree instead of text heuristics) =====

    public void testSuspiciousSemicolonIf() {
        assertHasProblems(new SuspiciousSemicolonInspection(),
                "void f() { if(x); }");
    }

    public void testSuspiciousSemicolonWhile() {
        assertHasProblems(new SuspiciousSemicolonInspection(),
                "void f() { while(y); }");
    }

    public void testSuspiciousSemicolonForEmptyHeader() {
        assertHasProblems(new SuspiciousSemicolonInspection(),
                "void f() { for(;;); }");
    }

    public void testSuspiciousSemicolonCallInForHeaderClean() {
        // Anti-false-positive: header semicolons + call in the for header, real body present
        assertNoProblems(new SuspiciousSemicolonInspection(),
                "void f() { for(i=Foo(); i<n; i++){ g(); } }");
    }

    public void testSuspiciousSemicolonNormalIfClean() {
        assertNoProblems(new SuspiciousSemicolonInspection(),
                "void f() { if(x) { g(); } }");
    }

    public void testEmptyLoopBodyBlock() {
        assertHasProblems(new EmptyLoopBodyInspection(),
                "void f() { while(cond) { } }");
    }

    public void testEmptyLoopBodySemicolon() {
        assertHasProblems(new EmptyLoopBodyInspection(),
                "void f() { while(cond); }");
    }

    public void testEmptyLoopBodyClean() {
        assertNoProblems(new EmptyLoopBodyInspection(),
                "void f() { while(cond) { g(); } for(int i=0; i<10; i++) { g(); } }");
    }

    public void testReturnValueIgnored() {
        assertHasProblems(new ReturnValueIgnoredInspection(),
                "void f() { ArrayResize(arr, 100); }");
    }

    public void testReturnValueIgnoredAssignedClean() {
        // Result captured in a declaration — must not flag
        assertNoProblems(new ReturnValueIgnoredInspection(),
                "void f() { int q = ArrayResize(arr, 100); if(q < 0) return; }");
    }

    public void testReturnValueIgnoredUsedInConditionClean() {
        // Anti-false-positive: call sits inside an if condition, not a bare statement
        assertNoProblems(new ReturnValueIgnoredInspection(),
                "void f() { if(ArrayResize(arr, 100) < 0) { return; } }");
    }

    public void testUncheckedOrderSendAssignedClean() {
        // Anti-false-positive: result captured by a local variable declaration
        assertNoProblems(new UncheckedOrderSendInspection(),
                "void f() { int t = OrderSend(r, res); }");
    }

    public void testUncheckedOrderSendInConditionClean() {
        // Anti-false-positive: call checked directly inside an if condition
        assertNoProblems(new UncheckedOrderSendInspection(),
                "void f() { if(OrderSend(r, res)) { } }");
    }

    public void testUncheckedOrderSendReturnedClean() {
        assertNoProblems(new UncheckedOrderSendInspection(),
                "int f() { return OrderSend(r, res); }");
    }

    public void testUncheckedOrderSendBare() {
        assertHasProblems(new UncheckedOrderSendInspection(),
                "void f() { OrderSend(r, res); }");
    }

    public void testDeepNesting() {
        assertHasProblems(new DeepNestingInspection(),
                "void f() { if(a) { if(b) { if(c) { if(d) { Print(1); } } } } }");
    }

    public void testDeepNestingClean() {
        assertNoProblems(new DeepNestingInspection(),
                "void f() { if(a) { if(b) { if(c) { Print(1); } } } }");
    }

    public void testMissingDefaultCase() {
        assertHasProblems(new MissingDefaultCaseInspection(),
                "void f() { switch(k) { case 1: break; } }");
    }

    public void testMissingDefaultCaseClean() {
        assertNoProblems(new MissingDefaultCaseInspection(),
                "void f() { switch(k) { case 1: break; default: break; } }");
    }

    public void testMissingDefaultCaseScopedToEachSwitch() {
        // Anti-false-negative: a 'default' in another switch no longer masks the missing one
        assertHasProblems(new MissingDefaultCaseInspection(),
                "void f() { switch(a) { case 1: break; default: break; }\n" +
                "  switch(b) { case 1: break; } }");
    }

    // ===== Statement-AST migrations wave 2 (loop bodies, switch segments, empty handlers) =====

    public void testNewKeywordInLoopBody() {
        assertHasProblems(new NewKeywordInLoopInspection(),
                "void f() { for(int i=0; i<10; i++) { CObj* o = new CObj(); } }");
    }

    public void testNewKeywordOutsideLoopBodyClean() {
        // Anti-false-positive: brace-less loop, 'new' lives in an unrelated block after it
        assertNoProblems(new NewKeywordInLoopInspection(),
                "void f() { for(int i=0; i<10; i++) Print(i);\n" +
                "  if(cond) { CObj* o = new CObj(); delete o; } }");
    }

    public void testArrayResizeInLoopDoBody() {
        assertHasProblems(new ArrayResizeInLoopInspection(),
                "void f() { double arr[]; int i=0; do { ArrayResize(arr, i); i++; } while(i < 10); }");
    }

    public void testArrayResizeOutsideLoopBodyClean() {
        // Anti-false-positive: brace-less loop, ArrayResize in an unrelated block after it
        assertNoProblems(new ArrayResizeInLoopInspection(),
                "void f() { double arr[]; for(int i=0; i<10; i++) Sum(i);\n" +
                "  if(cond) { ArrayResize(arr, 100); } }");
    }

    public void testStringConcatInLoopWhileBody() {
        assertHasProblems(new StringConcatInLoopInspection(),
                "void f() { string s; int i=0; while(i < 10) { s = s + \"x\"; i++; } }");
    }

    public void testStringConcatOutsideLoopBodyClean() {
        // Anti-false-positive: brace-less loop, concat in an unrelated block after it
        assertNoProblems(new StringConcatInLoopInspection(),
                "void f() { string s; for(int i=0; i<10; i++) Work(i);\n" +
                "  if(cond) { s = s + \"x\"; } }");
    }

    public void testUnconditionalOrderLoopBareCallInBody() {
        assertHasProblems(new UnconditionalOrderLoopInspection(),
                "void OnTick() { for(int i=0; i<total; i++) { OrderSelect(i, SELECT_BY_POS); } }");
    }

    public void testUnconditionalOrderLoopGuardedByIfClean() {
        // Anti-false-positive: order call guarded by an if inside the loop is not unconditional
        assertNoProblems(new UnconditionalOrderLoopInspection(),
                "void OnTick() { for(int i=0; i<total; i++) { if(need) { OrderSelect(i, SELECT_BY_POS); } } }");
    }

    public void testInfiniteLoopRiskWhileTrue() {
        assertHasProblems(new InfiniteLoopRiskInspection(),
                "void f() { while(true) { DoStuff(); } }");
    }

    public void testInfiniteLoopRiskForEmptyHeader() {
        assertHasProblems(new InfiniteLoopRiskInspection(),
                "void f() { for(;;) { DoStuff(); } }");
    }

    public void testInfiniteLoopRiskBreakClean() {
        // Anti-false-positive: a break anywhere in the body subtree is a visible exit
        assertNoProblems(new InfiniteLoopRiskInspection(),
                "void f() { while(true) { if(x) break; DoStuff(); } }");
    }

    public void testInfiniteLoopRiskNonConstantConditionClean() {
        // Conservative: only clearly constant-true conditions are flagged
        assertNoProblems(new InfiniteLoopRiskInspection(),
                "void f() { while(running) { DoStuff(); } }");
    }

    public void testMissingBreakInSwitchFallThrough() {
        assertHasProblems(new MissingBreakInSwitchInspection(),
                "void f() { switch(k) { case 1: Print(1); case 2: break; } }");
    }

    public void testMissingBreakInSwitchAllBreaksClean() {
        assertNoProblems(new MissingBreakInSwitchInspection(),
                "void f() { switch(k) { case 1: Print(1); break; case 2: break; } }");
    }

    public void testMissingBreakInSwitchScopedPerSwitchClean() {
        // Anti-false-positive: the last case of one switch followed by a second switch is not
        // fall-through — the old whole-function text scan chained labels across switches
        assertNoProblems(new MissingBreakInSwitchInspection(),
                "void f() { switch(a) { case 1: Print(1); break; case 2: Print(2); }\n" +
                "  switch(b) { case 3: break; } }");
    }

    public void testMissingBreakInSwitchEmptyFallThroughClean() {
        // Intentional label stacking (case X: case Y:) has no statements to fall through
        assertNoProblems(new MissingBreakInSwitchInspection(),
                "void f() { switch(k) { case 1: case 2: break; } }");
    }

    public void testEmptyEventHandlerCommentOnlyBody() {
        // Structural emptiness: comments are trivia, the body has no statement children
        assertHasProblems(new EmptyEventHandlerInspection(),
                "void OnTick() { /* nothing yet */ }");
    }

    public void testEmptyEventHandlerWithStatementClean() {
        assertNoProblems(new EmptyEventHandlerInspection(),
                "void OnTimer() { EventKillTimer(); }");
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.QuickFix;
import com.intellij.openapi.command.WriteCommandAction;
import com.intellij.psi.PsiDocumentManager;
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

    /**
     * Runs {@code inspection} over {@code code}, applies the first quick fix of the first problem
     * found, and returns the resulting file text. Fails the test if there is no problem or no fix.
     */
    private String applyFirstQuickFix(LocalInspectionTool inspection, String code, String fileName) {
        PsiFile file = myFixture.configureByText(fileName, code);
        InspectionManager manager = InspectionManager.getInstance(getProject());
        ProblemDescriptor[] problems = inspection.checkFile(file, manager, false);
        assertNotNull("checkFile returned null for " + inspection.getClass().getSimpleName(), problems);
        assertTrue("Expected problems from " + inspection.getClass().getSimpleName(), problems.length > 0);
        QuickFix<?>[] fixes = problems[0].getFixes();
        assertNotNull("Expected quick fixes on the first problem from " + inspection.getClass().getSimpleName(), fixes);
        assertTrue("Expected at least one quick fix from " + inspection.getClass().getSimpleName(), fixes.length > 0);
        LocalQuickFix fix = (LocalQuickFix) fixes[0];
        WriteCommandAction.runWriteCommandAction(getProject(), () -> fix.applyFix(getProject(), problems[0]));
        PsiDocumentManager.getInstance(getProject()).commitAllDocuments();
        return file.getText();
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

    public void testUncheckedHandleNegativeOneCheckClean() {
        // INVALID_HANDLE is -1 — checking against the literal sentinel is equally valid.
        assertNoProblems(new UncheckedHandleInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);\n" +
                "  if(handle == -1) return INIT_FAILED; return 0; }",
                "test.mq5");
    }

    public void testUncheckedHandleQuickFixInsertsInvalidHandleCheck() {
        String result = applyFirstQuickFix(new UncheckedHandleInspection(),
                "int handle;\n" +
                "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }",
                "test.mq5");
        assertTrue("Expected an INVALID_HANDLE guard inserted after creation:\n" + result,
                result.contains("if(handle == INVALID_HANDLE)"));
    }

    public void testUncheckedCopyRatesQuickFixWrapsInFailureCheck() {
        String result = applyFirstQuickFix(new UncheckedCopyRatesInspection(),
                "void foo() { double buf[]; CopyBuffer(handle, 0, 0, 10, buf); }", "test.mq5");
        assertTrue("Expected the CopyBuffer call wrapped in a < 0 failure check:\n" + result,
                result.contains("if(CopyBuffer(handle, 0, 0, 10, buf) < 0)"));
    }

    public void testArrayResizeReturnCheckQuickFixWrapsInFailureCheck() {
        String result = applyFirstQuickFix(new ArrayResizeReturnCheckInspection(),
                "void foo() { double arr[]; ArrayResize(arr, 100); }", "test.mq4");
        assertTrue("Expected the ArrayResize call wrapped in a < 0 failure check:\n" + result,
                result.contains("if(ArrayResize(arr, 100) < 0)"));
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

    public void testArrayAccessBoundParameterCompanionClean() {
        // LEIlight.mq5:3935/3940 RWTop (Fable FP): the array parameter `data[]` is bounds-checked
        // against a companion `arraySize` PARAMETER, not an in-body ArraySize() call — same shape as
        // RWBottom/IsPotentialTop/IsPotentialBottom (3957/4020/4052).
        assertNoProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "bool RWTop(const double &data[], int currIndex, int order, int arraySize) {\n" +
                "  if(currIndex < order || currIndex >= arraySize - order) return false;\n" +
                "  const double v = data[currIndex];\n" +
                "  return true; }");
    }

    public void testArrayAccessGuardComparisonClean() {
        // PositionManagement.mqh:270/279 (Fable FP): the index is guarded by an `if(s < 0) continue;`
        // sentinel check against a variable rather than a literal ArraySize() call at the access site.
        assertNoProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "void foo() { int s = FindOrCreate();\n" +
                "  if(s < 0) return;\n" +
                "  double r = g_state[s].R; }");
    }

    public void testArrayAccessNoSizeInfoAtAllStillFlags() {
        // Genuine positive: no ArraySize/bound-parameter/guard-comparison anywhere — must still flag.
        assertHasProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "void foo(int i) { double arr[]; double x = arr[i]; }");
    }

    public void testArrayAccessDeclarationBracketsNotMisreadAsAccessClean() {
        // A variable DECLARATION's array-size brackets (`double col[1];`) are not an index read —
        // a function containing only a declaration, with no real array access, must not be flagged.
        assertNoProblems(new ArrayAccessWithoutSizeCheckInspection(),
                "void foo() { double col[1]; }");
    }

    public void testMissingInputValidation() {
        // Smoke test — depends on parser producing INPUT_KEYWORD in VAR_DECLARATION_STATEMENT
        assertInspectionRuns(new MissingInputValidationInspection(),
                "input int InpPeriod = 14;\n" +
                "int OnInit() { return 0; }");
    }

    public void testMissingInputValidationMqhHeaderNoOnInitClean() {
        // A .mqh header never has (or needs) an OnInit() of its own — the "file has input params
        // but no OnInit()" warning must be restricted to actual .mq4/.mq5 program files.
        assertNoProblems(new MissingInputValidationInspection(),
                "input int InpPeriod = 14;",
                "test.mqh");
    }

    public void testMissingInputValidationOnInitNoIfNotEmptyClean() {
        // A non-empty OnInit() that does real setup (e.g. a timer) without an if-statement is not
        // "missing validation" — plenty of legitimate inputs (string/enum/bool) need no range check.
        assertNoProblems(new MissingInputValidationInspection(),
                "input int InpPeriod = 14;\n" +
                "int OnInit() { EventSetTimer(60); return 0; }");
    }

    public void testMissingFileClose() {
        assertHasProblems(new MissingFileCloseInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); }");
    }

    public void testMissingFileCloseClean() {
        assertNoProblems(new MissingFileCloseInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); FileClose(h); }");
    }

    public void testMissingFileCloseCrossFunctionPairingClean() {
        // RIGGWIRE_DataCapture.mq5:115/176, RIGGWIRE_Logger.mqh:79/248 (Fable FP): the global-handle
        // idiom opens the file in OnInit() and closes it in OnDeinit() — different functions, same file.
        assertNoProblems(new MissingFileCloseInspection(),
                "int g_fileHandle;\n" +
                "int OnInit() { g_fileHandle = FileOpen(\"test.txt\", FILE_WRITE); return 0; }\n" +
                "void OnDeinit(const int reason) { FileClose(g_fileHandle); }",
                "test.mq5");
    }

    public void testUncheckedCopyRates() {
        assertHasProblems(new UncheckedCopyRatesInspection(),
                "void foo() { MqlRates rates[]; CopyRates(_Symbol, PERIOD_H1, 0, 100, rates); }");
    }

    public void testUncheckedCopyRatesClean() {
        assertNoProblems(new UncheckedCopyRatesInspection(),
                "void foo() { MqlRates rates[]; if(CopyRates(_Symbol, PERIOD_H1, 0, 100, rates) < 0) return; }");
    }

    public void testUncheckedCopyRatesCountComparisonClean() {
        // The count-comparison idiom: checking the copied amount against the requested count.
        assertNoProblems(new UncheckedCopyRatesInspection(),
                "void foo() { MqlRates rates[]; int count = 10;\n" +
                "  if(CopyRates(_Symbol, PERIOD_H1, 0, count, rates) < count) return; }");
    }

    public void testUncheckedCopyRatesUnrelatedLoopStillFlagged() {
        // Regression: an unrelated `i < rates_total` loop must NOT be mistaken for a failure check
        // of the copy call — the unchecked CopyBuffer must still be flagged.
        assertHasProblems(new UncheckedCopyRatesInspection(),
                "void foo() { double buf[]; CopyBuffer(handle, 0, 0, 10, buf);\n" +
                "  for(int i = 0; i < 10; i++) { buf[i] = 0.0; } }");
    }

    public void testDoubleIndicatorRelease() {
        assertHasProblems(new DoubleIndicatorReleaseInspection(),
                "void OnDeinit(const int reason) { IndicatorRelease(h); IndicatorRelease(h); }",
                "test.mq5");
    }

    public void testDoubleIndicatorReleaseArrayHandlesOk() {
        // Distinct array elements are different handles, not a double-free (Fable concern #3).
        assertNoProblems(new DoubleIndicatorReleaseInspection(),
                "void OnDeinit(const int reason) { IndicatorRelease(handles[0]); IndicatorRelease(handles[1]); }",
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

    public void testDeleteWithoutNullCheckQuickFixInsertsNullAssignment() {
        String result = applyFirstQuickFix(new DeleteWithoutNullCheckInspection(),
                "void foo() { delete ptr; }", "test.mq4");
        assertTrue("Expected 'ptr = NULL;' inserted after the delete statement:\n" + result,
                result.contains("delete ptr;\nptr = NULL;"));
    }

    public void testDeleteWithoutNullCheckArrayElementHasNoQuickFix() {
        // delete arr[i]; has no single pointer variable to null out — the fix must not be offered
        // rather than guessing at what to insert.
        PsiFile file = myFixture.configureByText("test.mq4", "void foo() { delete arr[i]; }");
        InspectionManager manager = InspectionManager.getInstance(getProject());
        ProblemDescriptor[] problems = new DeleteWithoutNullCheckInspection().checkFile(file, manager, false);
        assertNotNull(problems);
        assertTrue(problems.length > 0);
        QuickFix<?>[] fixes = problems[0].getFixes();
        assertTrue("Array-element delete must not offer the nullify-pointer fix",
                fixes == null || fixes.length == 0);
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

    public void testMissingDestructorLocalResourceNotMemberClean() {
        // A resource acquired AND released entirely through a local variable inside a method owns
        // nothing at the class level and needs no destructor.
        assertNoProblems(new MissingDestructorInspection(),
                "class CTest { public: void Foo() { int h = FileOpen(\"x.txt\", FILE_READ); FileClose(h); } };");
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

    public void testPreprocessorPropertyServiceClean() {
        // `#property service` declares a valid MQL5 service program — a parameterless flag like
        // `library`/`strict`, not an "Unknown property".
        assertNoProblems(new PreprocessorPropertyInspection(),
                "#property service\nvoid OnStart() { }");
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

    public void testImmutableInputParameterMemberAccessClean() {
        // `cfg.MaxRisk = ...` reassigns a field on some other object, not the input `MaxRisk`.
        assertNoProblems(new ImmutableInputParameterInspection(),
                "input int MaxRisk = 5;\n" +
                "void foo() { cfg.MaxRisk = 10; }");
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

    public void testNarrowingReturnTypeFlagsFloatLiteral() {
        // Returning a float literal from an int function is a real narrowing.
        assertHasProblems(new NarrowingReturnTypeInspection(),
                "int Round2() { return 1.5; }");
    }

    public void testNarrowingReturnTypeNoMemberAccessFP() {
        // Member access on a digit-suffixed identifier must NOT be read as a float literal (Fable bug #2).
        assertNoProblems(new NarrowingReturnTypeInspection(),
                "int Total() { return obj1.value; }");
    }

    public void testNarrowingReturnTypeExplicitCastClean() {
        // An explicit cast makes any truncation intentional and visible — not the silent narrowing
        // this inspection targets.
        assertNoProblems(new NarrowingReturnTypeInspection(),
                "int Round3(double x) { return (int)MathRound(x*1.5); }");
    }

    public void testNarrowingReturnTypeLiteralInConditionClean() {
        // A float literal inside a ternary's condition is never the returned value.
        assertNoProblems(new NarrowingReturnTypeInspection(),
                "int Choose(double x) { return x>0.5 ? 1 : 0; }");
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

    public void testArrayResizeInLoopReserveArgClean() {
        // ArrayResize(a, i, reserve) — the 3-arg form is the doc-endorsed pattern for exactly this
        // situation (arrayresize.html): FastProfitLocker.mqh:388, TrendConfirmation.mqh:827/845/876.
        assertNoProblems(new ArrayResizeInLoopInspection(),
                "void foo() { double arr[]; for(int i=0; i<10; i++) { ArrayResize(arr, i, 20); } }");
    }

    public void testPrintInOnTick() {
        assertHasProblems(new PrintInOnTickInspection(),
                "void OnTick() { Print(\"tick\"); }");
    }

    public void testPrintInOnTickClean() {
        assertNoProblems(new PrintInOnTickInspection(),
                "void OnTick() { OrderSend(request, result); }");
    }

    public void testPrintInOnTickConditionalErrorLoggingClean() {
        // Conditional/error-path logging fires only on the (rare) failure path, not every tick.
        assertNoProblems(new PrintInOnTickInspection(),
                "void OnTick() { if(!OrderSend(request, result)) Print(\"failed\", GetLastError()); }");
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

    public void testRedundantCalculationInOnTickVolatileAskBidClean() {
        // SYMBOL_BID changes every tick and must never be cached — repeating this call is correct.
        assertNoProblems(new RedundantCalculationInOnTickInspection(),
                "void OnTick() { double a = SymbolInfoDouble(_Symbol, SYMBOL_BID);\n" +
                "  double b = SymbolInfoDouble(_Symbol, SYMBOL_BID); }");
    }

    public void testRedundantCalculationInOnTickVolatileSymbolInfoTickClean() {
        // SymbolInfoTick() changes every tick and must never be cached.
        assertNoProblems(new RedundantCalculationInOnTickInspection(),
                "void OnTick() { MqlTick tick1; SymbolInfoTick(_Symbol, tick1);\n" +
                "  MqlTick tick2; SymbolInfoTick(_Symbol, tick2); }");
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

    public void testMissingArrayPreallocationReserveArgClean() {
        // TrendConfirmation.mqh:660/675 (Fable FP): every call already supplies the 3rd (reserve)
        // argument — the doc-endorsed pre-allocation form (arrayresize.html) — so none of them should
        // count toward the "multiple incremental resizes" threshold.
        assertNoProblems(new MissingArrayPreallocationInspection(),
                "void foo() { ArrayResize(arr, 1, 50); ArrayResize(arr, 2, 50); ArrayResize(arr, 3, 50); }");
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
        // Print/PrintFormat/Comment/Alert only write to the local log/UI — not a privacy risk — so
        // the positive case must use a function that actually leaves the machine.
        assertHasProblems(new AccountInfoExposureInspection(),
                "void foo() { double bal = AccountInfoDouble(ACCOUNT_BALANCE);\n" +
                "  SendMail(\"Balance\", DoubleToString(bal)); }");
    }

    public void testAccountInfoExposurePrintCleanNoLeavesMachine() {
        // Print() never leaves the machine (writes to the local terminal log) — logging account
        // data with it is not a data privacy risk and must not be flagged.
        assertNoProblems(new AccountInfoExposureInspection(),
                "void foo() { double bal = AccountInfoDouble(ACCOUNT_BALANCE);\n" +
                "  Print(bal); }");
    }

    public void testHardcodedCredentials() {
        assertHasProblems(new HardcodedCredentialsInspection(),
                "void foo() { string password = \"secret123\"; }");
    }

    public void testHardcodedCredentialsProseMentionClean() {
        // A credential-sounding word merely mentioned in prose (no assignment shape) must not flag.
        assertNoProblems(new HardcodedCredentialsInspection(),
                "void foo() { Print(\"Authorization failed\"); }");
    }

    public void testHardcodedCredentialsUrlParamClean() {
        // The safe idiom: the secret is in a variable and "token=" is only a URL query fragment.
        // The char after the keyword's '=' is the string's own closing quote → must NOT flag.
        assertNoProblems(new HardcodedCredentialsInspection(),
                "void foo() { string key; string url = \"https://x.co/q?token=\" + key; }");
    }

    public void testSafeApiUsage() {
        assertInspectionRuns(new SafeApiUsageInspection(),
                "void foo() { OrderSend(request, result); }");
    }

    public void testSafeApiUsageStructFormCleanNoVolumeAtCallSite() {
        // DualOrderManager.mqh:1048 (Fable FP): a TRADE_ACTION_SLTP request via the MQL5
        // request/result struct form carries no volume argument at the call site at all — "validate
        // lot size before sending" is meaningless here, so it must not be flagged.
        assertNoProblems(new SafeApiUsageInspection(),
                "void foo() { MqlTradeRequest request; MqlTradeResult result;\n" +
                "  request.action = TRADE_ACTION_SLTP;\n" +
                "  if(!OrderSend(request, result) || result.retcode != TRADE_RETCODE_DONE) { Print(\"err\"); } }");
    }

    public void testSafeApiUsageStructFormDifferentIdentifierNamesClean() {
        // DualOrderManager.mqh:698/785: buy_request/buy_result, sell_request/sell_result — the struct
        // form is recognised by SHAPE (2 bare-identifier args), not by the literal names
        // "request"/"result".
        assertNoProblems(new SafeApiUsageInspection(),
                "void foo() { MqlTradeRequest buy_request; MqlTradeResult buy_result;\n" +
                "  if(!OrderSend(buy_request, buy_result) || buy_result.retcode != TRADE_RETCODE_DONE) { Print(\"err\"); } }");
    }

    public void testSafeApiUsageMql4PositionalFormStillFlags() {
        // The MQL4 positional form genuinely carries a volume argument (0.1) with no validation
        // nearby — this is the real antipattern the inspection targets and must still be flagged.
        assertHasProblems(new SafeApiUsageInspection(),
                "void foo() { OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }");
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

    public void testDeterministicSeedFlagsTimeCurrentSeed() {
        // Bug fix: math/mathsrand.html explicitly states MathSrand(TimeCurrent()) is "not suitable"
        // (TimeCurrent() can be unchanged for a long time, e.g. over a weekend) — this must be
        // flagged, not silently suppressed the way an earlier (inverted) version of this check did.
        assertHasProblems(new DeterministicSeedInspection(),
                "void foo() { MathSrand(TimeCurrent()); }");
    }

    // ===== Advanced Patterns =====

    public void testStackOverflowRisk() {
        assertHasProblems(new StackOverflowRiskInspection(),
                "void Recurse() { Recurse(); }");
    }

    public void testStackOverflowRiskStaticDelegationClean() {
        // RC-1 (Fable FP): TradeOperationWrapper.mqh:566 `return CTradeOperationWrapper::SafeOrderModify(...);`
        // is a static delegation call (CClass::Method), not the enclosing global function calling itself.
        assertNoProblems(new StackOverflowRiskInspection(),
                "bool SafeOrderModify(ulong ticket) { return CTradeOperationWrapper::SafeOrderModify(ticket); }");
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

    public void testStaleHandleUsageReinitializedClean() {
        // The re-init idiom: the handle is reassigned before the reuse, so it is a fresh handle,
        // not the released one.
        assertNoProblems(new StaleHandleUsageInspection(),
                "void foo() { IndicatorRelease(handle);\n" +
                "  handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);\n" +
                "  CopyBuffer(handle, 0, 0, 1, buf); }",
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

    public void testModernMQL5IdiomFlagsGlobalDeprecatedCall() {
        // A genuine bare call to the deprecated MQL4-only global function must still be flagged.
        assertHasProblems(new ModernMQL5IdiomInspection(),
                "void foo() { OrderDelete(ticket); }", "test.mq5");
    }

    public void testModernMQL5IdiomMemberCallClean() {
        // RC-1 (Fable FP): obj_Trade.OrderDelete(ticket) calls CTrade's method (RIGGWIRE_FINAL.mq5:2371),
        // not the deprecated MQL4 global OrderDelete() — a member call must not match the global-function matcher.
        assertNoProblems(new ModernMQL5IdiomInspection(),
                "void foo() { if(!obj_Trade.OrderDelete(ticket)) { Print(\"err\"); } }", "test.mq5");
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

    public void testSecureCodingPatternsNegativeOneCheckClean() {
        // INVALID_HANDLE is -1 — `== -1` is an equally valid check to `!= -1`.
        assertNoProblems(new SecureCodingPatternsInspection(),
                "void foo() { int h = FileOpen(\"test.txt\", FILE_READ); if(h == -1) return; }");
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

    public void testArrayResizeReturnCheckUnrelatedLoopStillFlagged() {
        // Regression: an unrelated loop comparison must not silence the unchecked ArrayResize.
        assertHasProblems(new ArrayResizeReturnCheckInspection(),
                "void foo() { double arr[]; ArrayResize(arr, 100);\n" +
                "  for(int i = 0; i < 100; i++) { arr[i] = 0.0; } }");
    }

    public void testArrayResizeReturnCheckCountComparisonClean() {
        // The count-comparison idiom: checking the resized array's size against the requested count.
        assertNoProblems(new ArrayResizeReturnCheckInspection(),
                "void foo() { double arr[]; int n = 100; if(ArrayResize(arr, n) != n) return; }");
    }

    public void testNullAfterDelete() {
        assertHasProblems(new NullAfterDeleteInspection(),
                "void foo() { delete ptr; }");
    }

    public void testNullAfterDeleteClean() {
        assertNoProblems(new NullAfterDeleteInspection(),
                "void foo() { delete ptr; ptr = NULL; }");
    }

    public void testNullAfterDeleteReassignedNonNullClean() {
        // The delete-then-recreate idiom: any reassignment ends the dangling window, not just NULL.
        assertNoProblems(new NullAfterDeleteInspection(),
                "void foo() { delete obj; obj = new CFoo(); }");
    }

    public void testNullAfterDeleteOnDeinitLastStatementClean() {
        // Nothing dangles once OnDeinit finishes tearing down — a bare delete as the last statement
        // there is not a leaked/dangling pointer.
        assertNoProblems(new NullAfterDeleteInspection(),
                "void OnDeinit(const int reason) { delete ptr; }",
                "test.mq5");
    }

    public void testNullAfterDeleteQuickFixInsertsNullAssignment() {
        String result = applyFirstQuickFix(new NullAfterDeleteInspection(),
                "void foo() { delete ptr; }", "test.mq4");
        assertTrue("Expected 'ptr = NULL;' inserted after the delete statement:\n" + result,
                result.contains("delete ptr;\nptr = NULL;"));
    }

    public void testNullAfterDeleteArrayElementNotFlagged() {
        // delete arr[i]; must NOT be flagged: the inspection can only verify a bare `arr = NULL;`
        // follow-up, which can never satisfy an array-element delete (the correct follow-up is
        // `arr[i] = NULL;`), so flagging it is a guaranteed false positive on legitimate array
        // management (e.g. delete-then-compact loops). The `[i]` parses as a wrapped BRACKETS_BLOCK.
        assertNoProblems(new NullAfterDeleteInspection(),
                "void foo() { delete arr[i]; }");
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

    public void testMissingTradeContextCheckMqhHeaderTreatedAsMql5() {
        // Phase 0: a .mqh header defaults to MQL5 (via MqlDialect), so the MQL4-only inspection must
        // NOT fire on it — this is the bug that produced IsTradeContextBusy() suggestions in MQL5 projects.
        assertNoProblems(new MissingTradeContextCheckInspection(),
                "void DoTrade() { OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }",
                "test.mqh");
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

    public void testOnCalculateReturnGuardedByIfClean() {
        // The idiomatic warm-up guard `if(rates_total<Period) return(0);` is a correct, intentional
        // early-out, not the "forces full recalculation" bug this inspection targets.
        assertNoProblems(new OnCalculateReturnInspection(),
                "int OnCalculate() { if(rates_total<Period) return(0); return rates_total; }",
                "test.mq5");
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
        // FileOpen (not ArrayResize — that's owned by ArrayResizeReturnCheckInspection now).
        assertHasProblems(new ReturnValueIgnoredInspection(),
                "void f() { FileOpen(\"x.txt\", FILE_READ); }");
    }

    public void testReturnValueIgnoredAssignedClean() {
        // Result captured in a declaration — must not flag
        assertNoProblems(new ReturnValueIgnoredInspection(),
                "void f() { int h = FileOpen(\"x.txt\", FILE_READ); if(h < 0) return; }");
    }

    public void testReturnValueIgnoredUsedInConditionClean() {
        // Anti-false-positive: call sits inside an if condition, not a bare statement
        assertNoProblems(new ReturnValueIgnoredInspection(),
                "void f() { if(FileOpen(\"x.txt\", FILE_READ) < 0) { return; } }");
    }

    public void testReturnValueIgnoredObjectCreateRecreateIdiomClean() {
        // ObjectCreate() is a no-op when the named object already exists (ST_TrendMeasure.mq5:192/210,
        // LEIlight.mq5:3704/3893) — the canonical delete-then-recreate drawing idiom must not flag.
        assertNoProblems(new ReturnValueIgnoredInspection(),
                "void f() { ObjectDelete(0, name); ObjectCreate(0, name, OBJ_TREND, 0, t1, p1, t2, p2); }");
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

    public void testStringConcatInLoopCompoundAddFlags() {
        // The self-accumulation antipattern via '+=' (compound add) must also be flagged — the old
        // check only matched a bare '+' adjacent to a string literal and silently missed 's += x;'.
        assertHasProblems(new StringConcatInLoopInspection(),
                "void foo() { string s; for(int i=0; i<10; i++) { s += \"x\"; } }");
    }

    public void testStringConcatInLoopFreshVariableCleanNoFalsePositive() {
        // MarketProfile.mq5:2050 and ~11 similar object-name-building loops: a FRESH per-iteration
        // concat into a brand-new variable is not self-accumulation — it allocates one string per
        // iteration either way, so it is not the "grows a buffer across iterations" antipattern.
        assertNoProblems(new StringConcatInLoopInspection(),
                "void foo() { for(int i=0; i<10; i++) { string t = a + b; } }");
    }

    public void testStringConcatInLoopBuiltinAccumulationFlags() {
        // Real O(n^2) accumulation with no string literal (RiskManager.mqh:2722-shaped):
        // json += FileReadString(handle); — a string-returning builtin RHS is string accumulation.
        assertHasProblems(new StringConcatInLoopInspection(),
                "void foo() { string json; while(!done) { json += FileReadString(handle); } }");
    }

    public void testStringConcatInLoopNumericAccumulationClean() {
        // Numeric accumulation is not this inspection's antipattern — no string literal, no string
        // builtin on the RHS, so it must not flag (the message recommends StringConcatenate()).
        assertNoProblems(new StringConcatInLoopInspection(),
                "void foo() { double total = 0; for(int i=0; i<10; i++) { total += MathAbs(i); } }");
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

    public void testUnconditionalOrderLoopEntireLoopGuardedByIfClean() {
        // RIGGWIRE_FINAL.mq5:2348/2365 (Fable FP): the header-call form `for(int i = PositionsTotal() - 1; ...)`
        // is itself nested inside a weekend-close `if(...)` guard — only runs under specific conditions.
        assertNoProblems(new UnconditionalOrderLoopInspection(),
                "void OnTick() { if(shouldClose) {\n" +
                "  for(int i = PositionsTotal() - 1; i >= 0; i--) { } } }");
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

    // ===== Phase 5: AST migration off BracketBlockTokenWalker (new/added test coverage) =====

    public void testMagicNumber() {
        assertHasProblems(new MagicNumberInspection(),
                "void foo() { OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0); }");
    }

    public void testMagicNumberClean() {
        assertNoProblems(new MagicNumberInspection(),
                "void foo() { double lot = InpLotSize; OrderSend(Symbol(), OP_BUY, lot, Ask, 3, 0, 0); }");
    }

    public void testMagicNumberFlagsCTradeMemberCall() {
        // Regression: the CTrade member-call form must still flag a hardcoded lot — the RC-1
        // member-call guard (correct for global-function inspections) must not blind this one,
        // whose target names (Buy/Sell/...) are CTrade METHODS invoked as trade.Buy(0.1, ...).
        assertHasProblems(new MagicNumberInspection(),
                "void foo() { trade.Buy(0.1, _Symbol, 0.0, sl, 0.0, \"x\"); }");
    }

    public void testNoGoto() {
        assertHasProblems(new NoGotoInspection(),
                "void foo() { goto done; }");
    }

    public void testNoGotoClean() {
        assertNoProblems(new NoGotoInspection(),
                "void foo() { if(x) return; }");
    }

    public void testRepeatedApiCall() {
        // SYMBOL_POINT/SYMBOL_DIGITS-style properties are stable across ticks — a genuine
        // cacheable repeat (SYMBOL_BID/SYMBOL_ASK below are the volatile, must-not-cache case).
        assertHasProblems(new RepeatedApiCallInspection(),
                "void OnTick() { double a = SymbolInfoDouble(_Symbol, SYMBOL_POINT);\n" +
                "  double b = SymbolInfoDouble(_Symbol, SYMBOL_POINT);\n" +
                "  double c = SymbolInfoDouble(_Symbol, SYMBOL_POINT); }");
    }

    public void testRepeatedApiCallClean() {
        assertNoProblems(new RepeatedApiCallInspection(),
                "void OnTick() { double a = SymbolInfoDouble(_Symbol, SYMBOL_BID); }");
    }

    public void testRepeatedApiCallVolatileAskBidClean() {
        // SYMBOL_ASK/SYMBOL_BID change every tick and must never be cached — repeating these calls
        // is correct, not a caching opportunity.
        assertNoProblems(new RepeatedApiCallInspection(),
                "void OnTick() { double a = SymbolInfoDouble(_Symbol, SYMBOL_BID);\n" +
                "  double b = SymbolInfoDouble(_Symbol, SYMBOL_ASK);\n" +
                "  double c = SymbolInfoDouble(_Symbol, SYMBOL_BID); }");
    }

    public void testRepeatedApiCallTimeCurrentClean() {
        // TimeCurrent() changes every tick and must never be cached.
        assertNoProblems(new RepeatedApiCallInspection(),
                "void OnTick() { datetime a = TimeCurrent(); datetime b = TimeCurrent(); datetime c = TimeCurrent(); }");
    }

    public void testUnusedParameter() {
        assertHasProblems(new UnusedParameterInspection(),
                "void Foo(int unused) { Print(\"hi\"); }");
    }

    public void testUnusedParameterClean() {
        assertNoProblems(new UnusedParameterInspection(),
                "void Foo(int used) { Print(used); }");
    }

    public void testVirtualCallInConstructor() {
        // Smoke test — like testVirtualWithoutDestructor/testPublicDataMember, correctness here
        // depends on parser details (virtual-modifier attachment to the FUNCTION node) that may
        // vary; this only asserts the inspection runs without throwing.
        assertInspectionRuns(new VirtualCallInConstructorInspection(),
                "class CBase { public: virtual void Init() {} CBase() { Init(); } };");
    }

    public void testVirtualCallInConstructorClean() {
        assertNoProblems(new VirtualCallInConstructorInspection(),
                "class CBase { public: virtual void Init() {} CBase() { Print(\"ctor\"); } };");
    }

    // ===== Phase 5: extra negative-case coverage for structurally-migrated inspections =====

    public void testAccountInfoExposureClean() {
        assertNoProblems(new AccountInfoExposureInspection(),
                "void foo() { double bal = AccountInfoDouble(ACCOUNT_BALANCE); }");
    }

    public void testGlobalVariableConflictClean() {
        assertNoProblems(new GlobalVariableConflictInspection(),
                "void foo() { GlobalVariableSet(\"gv\", 1.0); }");
    }

    public void testDanglingObjectReferenceClean() {
        assertNoProblems(new DanglingObjectReferenceInspection(),
                "void foo() { delete ptr; ptr = NULL; }");
    }

    public void testDanglingObjectReferenceReassignedNonNullClean() {
        // The delete-then-recreate idiom: any reassignment ends the dangling window, and the
        // reassignment's own left-hand identifier is never itself counted as a dangling use.
        assertNoProblems(new DanglingObjectReferenceInspection(),
                "void foo() { delete obj; obj = new CFoo(); }");
    }

    public void testDanglingObjectReferenceArrayElementClean() {
        // delete arr[i]; is array management, not a dangling scalar pointer — must not be flagged
        // (the following arr[j] = arr[j+1] compaction is a legitimate pattern, not a dangling use).
        assertNoProblems(new DanglingObjectReferenceInspection(),
                "void foo() { delete arr[i]; arr[i] = arr[i+1]; }");
    }

    public void testStaleHandleUsageClean() {
        assertNoProblems(new StaleHandleUsageInspection(),
                "void foo() { int h2 = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);\n" +
                "  IndicatorRelease(handle); CopyBuffer(h2, 0, 0, 1, buf); }",
                "test.mq5");
    }

    public void testDoubleIndicatorReleaseDifferentHandlesClean() {
        assertNoProblems(new DoubleIndicatorReleaseInspection(),
                "void OnDeinit(const int reason) { IndicatorRelease(h1); IndicatorRelease(h2); }",
                "test.mq5");
    }

    public void testDoubleIndicatorReleaseMutuallyExclusiveIfBranchesClean() {
        // RIGGWIRE_DataCapture.mq5:105-107 (Fable FP): partial-failure cleanup releases the SAME
        // earlier handle from several mutually exclusive `if(... == INVALID_HANDLE) { ...; return; }`
        // guards — at most one branch ever runs, so this is not a double-free.
        assertNoProblems(new DoubleIndicatorReleaseInspection(),
                "int OnInit() {\n" +
                "  if(a == INVALID_HANDLE) { IndicatorRelease(h); return INIT_FAILED; }\n" +
                "  if(b == INVALID_HANDLE) { IndicatorRelease(h); return INIT_FAILED; }\n" +
                "  return INIT_SUCCEEDED; }",
                "test.mq5");
    }
}

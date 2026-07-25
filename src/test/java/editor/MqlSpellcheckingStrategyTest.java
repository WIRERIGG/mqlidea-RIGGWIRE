/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.spellchecker.tokenizer.SpellcheckingStrategy;
import com.intellij.spellchecker.tokenizer.Tokenizer;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MqlBundledDictionaryProvider;
import com.limemojito.oss.mql.editor.MqlSpellcheckingStrategy;
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Phase 2c (REVAMP_PLAN.md): {@link MqlSpellcheckingStrategy} wires comments/strings/identifiers
 * into the platform spellchecker; {@link MqlBundledDictionaryProvider} allow-lists common
 * MQL/MetaTrader jargon (spellcheck/mql.dic) so it isn't flagged as a typo.
 * <p/>
 * These tests exercise {@code getTokenizer} directly (and the EP registration lookup via
 * {@link SpellcheckingStrategy#getSpellcheckingStrategy}) rather than running the actual "Typo"
 * daemon inspection end-to-end: the concrete, instantiable spellchecking {@code
 * LocalInspectionTool} shipped in this IDE version ({@code GrazieSpellCheckingInspection}) lives
 * in the (optional, heavyweight) bundled Grazie plugin, not in {@code intellij.spellchecker}
 * itself ({@code com.intellij.spellchecker.inspections.SpellCheckingInspection} is abstract with
 * no visitor of its own) -- adding a Grazie dependency just to drive a test would be a much bigger
 * footprint than this lang-only plugin needs for a real "Typo" checker isn't part of the platform
 * module we depend on.
 */
public class MqlSpellcheckingStrategyTest extends BasePlatformTestCase {

    private final MqlSpellcheckingStrategy strategy = new MqlSpellcheckingStrategy();

    @Nullable
    private static PsiElement findByElementType(@NotNull PsiElement root, @NotNull IElementType type) {
        ASTNode node = root.getNode();
        return node == null ? null : findByElementType(node, type);
    }

    @Nullable
    private static PsiElement findByElementType(@NotNull ASTNode node, @NotNull IElementType type) {
        if (node.getElementType() == type) {
            return node.getPsi();
        }
        for (ASTNode child : node.getChildren(null)) {
            PsiElement found = findByElementType(child, type);
            if (found != null) {
                return found;
            }
        }
        return null;
    }

    public void testCommentUsesTextTokenizer() {
        PsiFile file = myFixture.configureByText("test.mq4", "// a comment\nvoid f() {}\n");
        PsiComment comment = PsiTreeUtil.findChildOfType(file, PsiComment.class);
        assertNotNull(comment);
        assertSame(SpellcheckingStrategy.TEXT_TOKENIZER, strategy.getTokenizer(comment));
    }

    public void testStringLiteralUsesTextTokenizer() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() { string s = \"hello\"; }\n");
        PsiElement stringLiteral = findByElementType(file, MQL4Elements.STRING_LITERAL);
        assertNotNull(stringLiteral);
        assertSame(SpellcheckingStrategy.TEXT_TOKENIZER, strategy.getTokenizer(stringLiteral));
    }

    public void testKeywordUsesEmptyTokenizer() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() {}\n");
        PsiElement keyword = findByElementType(file, MQL4Elements.VOID_KEYWORD);
        assertNotNull(keyword);
        assertSame(SpellcheckingStrategy.EMPTY_TOKENIZER, strategy.getTokenizer(keyword));
    }

    public void testNumberLiteralUsesEmptyTokenizer() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() { int x = 123; }\n");
        PsiElement number = findByElementType(file, MQL4Elements.INTEGER_LITERAL);
        assertNotNull(number);
        assertSame(SpellcheckingStrategy.EMPTY_TOKENIZER, strategy.getTokenizer(number));
    }

    public void testIdentifierUsesADedicatedSplittingTokenizer() {
        PsiFile file = myFixture.configureByText("test.mq4", "void myFastMa() {}\n");
        PsiElement identifier = findByElementType(file, MQL4Elements.IDENTIFIER);
        assertNotNull(identifier);
        Tokenizer<?> tokenizer = strategy.getTokenizer(identifier);
        assertNotSame("identifiers must not be skipped entirely", SpellcheckingStrategy.EMPTY_TOKENIZER, tokenizer);
        assertNotSame("identifiers must be split (camelCase), not checked as one free-text run", SpellcheckingStrategy.TEXT_TOKENIZER, tokenizer);
    }

    /** Confirms the {@code spellchecker.support} EP registration in plugin.xml actually resolves for MQL4. */
    public void testStrategyIsRegisteredForMql4Language() {
        PsiFile file = myFixture.configureByText("test.mq4", "// x\nvoid f() {}\n");
        PsiComment comment = PsiTreeUtil.findChildOfType(file, PsiComment.class);
        assertNotNull(comment);
        SpellcheckingStrategy resolved = SpellcheckingStrategy.getSpellcheckingStrategy(comment);
        assertNotNull("Expected an MQL4-registered spellchecking strategy", resolved);
        assertTrue("Expected MqlSpellcheckingStrategy to be resolved for an MQL4 PsiElement, got " + resolved.getClass(),
                resolved instanceof MqlSpellcheckingStrategy);
    }

    public void testBundledDictionaryProviderPointsAtLoadableResource() throws Exception {
        String[] dictionaries = new MqlBundledDictionaryProvider().getBundledDictionaries();
        assertEquals(1, dictionaries.length);
        assertEquals("/spellcheck/mql.dic", dictionaries[0]);

        try (InputStream in = MqlBundledDictionaryProvider.class.getResourceAsStream(dictionaries[0])) {
            assertNotNull("Expected the bundled dictionary resource to be present on the classpath", in);
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                Stream<String> lines = reader.lines();
                java.util.List<String> words = lines.map(String::trim).filter(s -> !s.isEmpty()).collect(Collectors.toList());
                assertTrue("Expected 'riggwire' in the bundled dictionary", words.contains("riggwire"));
                assertTrue("Expected 'deinit' in the bundled dictionary", words.contains("deinit"));
                assertTrue("Expected 'mql5' in the bundled dictionary", words.contains("mql5"));
            }
        }
    }
}

/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.type;

import com.intellij.lang.ASTNode;
import com.intellij.lang.LighterAST;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.LighterASTTokenNode;
import com.intellij.psi.impl.source.tree.LightTreeUtil;
import com.intellij.psi.stubs.ILightStubElementType;
import com.intellij.psi.stubs.IndexSink;
import com.intellij.psi.stubs.StubElement;
import com.intellij.psi.stubs.StubInputStream;
import com.intellij.psi.stubs.StubOutputStream;
import com.intellij.util.io.StringRef;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.index.MQL4IndexKeys;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.psi.stub.MQL4GlobalVarElementStub;
import com.limemojito.oss.mql.psi.stub.MQL4StubElements;
import com.limemojito.oss.mql.psi.stub.impl.MQL4GlobalVarElementStubImpl;
import com.limemojito.oss.mql.util.TextUtils;

import java.io.IOException;

/**
 * Light stub for a TOP-LEVEL (file-scope) global {@code VAR_DEFINITION}.
 *
 * <p>{@code VAR_DEFINITION} is the SAME element type for locals, class fields and globals, so a
 * plain type-only check would over-index. {@link #shouldCreateStub} therefore accepts a node ONLY
 * when its enclosing {@code VAR_DECLARATION_STATEMENT} is a direct child of the file node:</p>
 * <pre>VAR_DEFINITION &lt;- VAR_DEFINITION_LIST &lt;- VAR_DECLARATION_STATEMENT &lt;- FILE</pre>
 * <p>A field's statement sits under {@code CLASS_INNER_BLOCK} and a local's under a code block, so
 * both are rejected — reproducing exactly the former {@code topLevelVarsByName} file-child scan.
 * The AST and light-tree predicates are identical node-type/parent-type chains (NO text
 * heuristics), so stub building is consistent across both passes.</p>
 */
public class MQL4GlobalVarElementStubType extends ILightStubElementType<MQL4GlobalVarElementStub, MQL4VarDefinitionElement> {

    public MQL4GlobalVarElementStubType() {
        super("VAR_DEFINITION", MQL4Language.INSTANCE);
    }

    /** AST-pass predicate: enclosing VAR_DECLARATION_STATEMENT is a direct child of the file. */
    @Override
    public boolean shouldCreateStub(ASTNode node) {
        ASTNode list = node.getTreeParent();
        if (list == null || list.getElementType() != MQL4Elements.VAR_DEFINITION_LIST) {
            return false;
        }
        ASTNode statement = list.getTreeParent();
        if (statement == null || statement.getElementType() != MQL4Elements.VAR_DECLARATION_STATEMENT) {
            return false;
        }
        ASTNode parent = statement.getTreeParent();
        return parent != null && parent.getElementType() == MQL4StubElements.FILE;
    }

    /** Light-pass predicate: identical parent-type chain over the LighterAST. */
    @Override
    public boolean shouldCreateStub(@NotNull LighterAST tree, @NotNull LighterASTNode node, @NotNull StubElement parentStub) {
        LighterASTNode list = tree.getParent(node);
        if (list == null || list.getTokenType() != MQL4Elements.VAR_DEFINITION_LIST) {
            return false;
        }
        LighterASTNode statement = tree.getParent(list);
        if (statement == null || statement.getTokenType() != MQL4Elements.VAR_DECLARATION_STATEMENT) {
            return false;
        }
        LighterASTNode parent = tree.getParent(statement);
        return parent != null && parent.getTokenType() == MQL4StubElements.FILE;
    }

    @NotNull
    @Override
    public MQL4GlobalVarElementStub createStub(@NotNull LighterAST tree, @NotNull LighterASTNode node, @NotNull StubElement parentStub) {
        LighterASTNode nameNode = LightTreeUtil.firstChildOfType(tree, node, MQL4Elements.IDENTIFIER);
        String name = nameNode == null ? null : ((LighterASTTokenNode) nameNode).getText().toString();
        return new MQL4GlobalVarElementStubImpl(parentStub, name);
    }

    @Override
    public MQL4VarDefinitionElement createPsi(@NotNull MQL4GlobalVarElementStub stub) {
        return new MQL4VarDefinitionElement(stub);
    }

    @NotNull
    @Override
    public MQL4GlobalVarElementStub createStub(@NotNull MQL4VarDefinitionElement psi, StubElement parentStub) {
        return new MQL4GlobalVarElementStubImpl(parentStub, psi.getName());
    }

    @NotNull
    @Override
    public String getExternalId() {
        return "mqlidea.global-var";
    }

    @Override
    public void serialize(@NotNull MQL4GlobalVarElementStub stub, @NotNull StubOutputStream dataStream) throws IOException {
        dataStream.writeName(stub.getName());
    }

    @NotNull
    @Override
    public MQL4GlobalVarElementStub deserialize(@NotNull StubInputStream dataStream, StubElement parentStub) throws IOException {
        StringRef ref = dataStream.readName();
        return new MQL4GlobalVarElementStubImpl(parentStub, ref == null ? null : ref.getString());
    }

    @Override
    public void indexStub(@NotNull MQL4GlobalVarElementStub stub, @NotNull IndexSink sink) {
        String name = stub.getName();
        if (name != null && !name.isEmpty()) {
            sink.occurrence(MQL4IndexKeys.GLOBAL_VAR_NAME_INDEX_KEY, TextUtils.unescape(name));
        }
    }
}

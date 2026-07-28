/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.type;

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
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.stub.MQL4EnumElementStub;
import com.limemojito.oss.mql.psi.stub.impl.MQL4EnumElementStubImpl;
import com.limemojito.oss.mql.util.TextUtils;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Light stub for an {@code ENUM_STATEMENT}. Stores the enum TYPE name (the first direct IDENTIFIER
 * child; {@code null} for an anonymous {@code enum { ... }}). Every enum node gets a stub — a
 * class-nested enum is fine because its parent (the class) is itself stubbed. The name is indexed
 * into {@link MQL4IndexKeys#ENUM_NAME_INDEX_KEY} so enum-type resolution can query the stub index
 * instead of walking the AST of every #include-closure file.
 */
public class MQL4EnumElementStubType extends ILightStubElementType<MQL4EnumElementStub, MQL4EnumElement> {

    public MQL4EnumElementStubType() {
        super("ENUM_STATEMENT", MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public MQL4EnumElementStub createStub(@NotNull LighterAST tree, @NotNull LighterASTNode node, @NotNull StubElement parentStub) {
        // Anonymous enum: no direct IDENTIFIER child -> null name (never indexed), mirroring
        // MQL4EnumElement.getTypeName() which reads the same first direct IDENTIFIER child.
        LighterASTNode nameNode = LightTreeUtil.firstChildOfType(tree, node, MQL4Elements.IDENTIFIER);
        String name = nameNode == null ? null : ((LighterASTTokenNode) nameNode).getText().toString();
        return new MQL4EnumElementStubImpl(parentStub, name, fieldNames(tree, node));
    }

    /**
     * The constant names declared by this enum, read straight from the light tree (no AST parse):
     * the FIRST {@code IDENTIFIER} token of each {@code ENUM_FIELD} under the {@code ENUM_FIELDS_LIST}.
     * The field name always precedes any {@code = value} identifier (see {@code EnumParsing}), so the
     * first child identifier is unambiguously the constant's own name. Fields without an identifier
     * (malformed) are skipped, mirroring the enum-type name's {@code null}-on-missing handling.
     */
    @NotNull
    private static List<String> fieldNames(@NotNull LighterAST tree, @NotNull LighterASTNode enumNode) {
        LighterASTNode list = LightTreeUtil.firstChildOfType(tree, enumNode, MQL4Elements.ENUM_FIELDS_LIST);
        if (list == null) {
            return List.of();
        }
        List<String> names = new ArrayList<>();
        for (LighterASTNode field : LightTreeUtil.getChildrenOfType(tree, list, MQL4Elements.ENUM_FIELD)) {
            LighterASTNode id = LightTreeUtil.firstChildOfType(tree, field, MQL4Elements.IDENTIFIER);
            if (id != null) {
                names.add(((LighterASTTokenNode) id).getText().toString());
            }
        }
        return names;
    }

    @Override
    public MQL4EnumElement createPsi(@NotNull MQL4EnumElementStub stub) {
        return new MQL4EnumElement(stub);
    }

    @NotNull
    @Override
    public MQL4EnumElementStub createStub(@NotNull MQL4EnumElement psi, StubElement parentStub) {
        List<String> fieldNames = new ArrayList<>();
        for (MQL4EnumFieldElement field : psi.getFields()) {
            String fieldName = field.getName();
            // getFieldName() returns "???" for a field with no identifier; skip it so the stub carries
            // only real constant names (matches the light-tree path, which skips id-less fields).
            if (fieldName != null && !fieldName.isEmpty() && !"???".equals(fieldName)) {
                fieldNames.add(fieldName);
            }
        }
        return new MQL4EnumElementStubImpl(parentStub, psi.getTypeName(), fieldNames);
    }

    @NotNull
    @Override
    public String getExternalId() {
        return "mqlidea.enum";
    }

    @Override
    public void serialize(@NotNull MQL4EnumElementStub stub, @NotNull StubOutputStream dataStream) throws IOException {
        dataStream.writeName(stub.getName());
        List<String> fieldNames = stub.getFieldNames();
        dataStream.writeInt(fieldNames.size());
        for (String fieldName : fieldNames) {
            dataStream.writeName(fieldName);
        }
    }

    @NotNull
    @Override
    public MQL4EnumElementStub deserialize(@NotNull StubInputStream dataStream, StubElement parentStub) throws IOException {
        StringRef ref = dataStream.readName();
        int count = dataStream.readInt();
        List<String> fieldNames = new ArrayList<>(count);
        for (int i = 0; i < count; i++) {
            StringRef fieldRef = dataStream.readName();
            fieldNames.add(fieldRef == null ? "" : fieldRef.getString());
        }
        return new MQL4EnumElementStubImpl(parentStub, ref == null ? null : ref.getString(), fieldNames);
    }

    @Override
    public void indexStub(@NotNull MQL4EnumElementStub stub, @NotNull IndexSink sink) {
        String name = stub.getName();
        if (name != null && !name.isEmpty()) {
            sink.occurrence(MQL4IndexKeys.ENUM_NAME_INDEX_KEY, TextUtils.unescape(name));
        }
        // Index the enclosing enum under each constant name so a bare use of a constant (e.g. RED)
        // can be resolved to its declaration via the closure stub index -- without an AST walk.
        for (String fieldName : stub.getFieldNames()) {
            if (!fieldName.isEmpty()) {
                sink.occurrence(MQL4IndexKeys.ENUM_FIELD_NAME_INDEX_KEY, TextUtils.unescape(fieldName));
            }
        }
    }
}

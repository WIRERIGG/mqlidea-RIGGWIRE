/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.lang.ASTNode;
import com.intellij.lang.LanguageParserDefinitions;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.ParserDefinition;
import com.intellij.lang.PsiBuilder;
import com.intellij.lang.PsiBuilderFactory;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.stubs.IStubElementType;
import com.intellij.psi.tree.ILightStubFileElementType;
import com.intellij.util.diff.FlyweightCapableTreeStructure;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.parser.MQL4Parser;
import com.limemojito.oss.mql.index.MQL4IndexKeys;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4DefineElement;
import com.limemojito.oss.mql.psi.impl.MQL4TypedefElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.psi.stub.type.MQL4ClassElementStubType;
import com.limemojito.oss.mql.psi.stub.type.MQL4EnumElementStubType;
import com.limemojito.oss.mql.psi.stub.type.MQL4FunctionElementStubType;
import com.limemojito.oss.mql.psi.stub.type.MQL4GlobalVarElementStubType;
import com.limemojito.oss.mql.psi.stub.type.MQL4NamedElementStubType;

public interface MQL4StubElements {

    // Phase 4 (REVAMP_PLAN.md #3b): named PSI (PsiNameIdentifierOwner + setName) and reference
    // resolution semantics changed for FUNCTION/FUNCTION_DECLARATION/CLASS stubs; bump so existing
    // indexes are rebuilt rather than trusted stale.
    // v22: ENUM_STATEMENT and top-level VAR_DEFINITION became stub-backed (enum-name + global-var
    // stub indexes) so enum/global resolution no longer parses the #include-closure AST; bump forces
    // a one-time rebuild of the persisted stub indexes.
    // v23: the ENUM_STATEMENT stub now also carries its constant (field) names, indexed into the new
    // enum-field-name stub index so a bare enum-constant use resolves to its declaration; the changed
    // stub serialization forces a one-time rebuild.
    // v24: user-type, pointer, array and comma-list declarations parse as VAR_DEFINITIONs, adding
    // global-var stubs.
    // v25: `export` functions and `pack(n)` classes/structs parse into FUNCTION / CLASS nodes.
    // v26: unions are CLASS stubs of kind Union; TYPEDEF and #define (PREPROCESSOR_DEFINE_BLOCK) stubs;
    // namespace bodies, operator methods and operator-like functions now produce FUNCTION/CLASS stubs.
    // v28: variables declared after a class/struct body (struct S {...} v;) parse as top-level
    // VAR_DECLARATION_STATEMENTs, adding global-var stubs; qualified parameter and base types
    // (Outer::Item *p) parse, so functions that failed there now produce their stubs.
    int STUB_SCHEMA_VERSION = 28;

    // The debug name goes through the constructor: getDebugName() is internal API and not for overriding.
    ILightStubFileElementType FILE = new ILightStubFileElementType("RIGGWIRE MQL File", MQL4Language.INSTANCE) {
        @Override
        public String getExternalId() {
            // Distinctive, plugin-unique id so the platform can tell this stub file element
            // type apart from other MQL4 languages (e.g. the upstream investflow plugin,
            // which uses the default "MQL4.FILE"). Avoids the "Cannot distinguish
            // StubFileElementTypes" warning.
            return "riggwire.mql.FILE";
        }

        @Override
        public int getStubVersion() {
            // Tie the stub-tree format version to STUB_SCHEMA_VERSION — the SDK-canonical
            // invalidation point. Whenever the serialized stub structure changes (e.g. the enum
            // stub gaining field names in v23), bumping the constant discards persisted stub trees
            // and re-indexes from source, so a v22 stub is never deserialized with a v23 reader.
            return STUB_SCHEMA_VERSION;
        }

        public FlyweightCapableTreeStructure<LighterASTNode> parseContentsLight(ASTNode chameleon) {
            PsiElement psi = chameleon.getPsi();
            assert (psi != null) : ("Bad chameleon: " + chameleon);

            Project project = psi.getProject();
            PsiBuilderFactory factory = PsiBuilderFactory.getInstance();
            PsiBuilder builder = factory.createBuilder(project, chameleon);
            ParserDefinition parserDefinition = LanguageParserDefinitions.INSTANCE.forLanguage(getLanguage());
            assert (parserDefinition != null) : this;
            MQL4Parser parser = new MQL4Parser();
            return parser.parseLight(this, builder);
        }
    };

    IStubElementType<MQL4ClassElementStub, MQL4ClassElement> CLASS = new MQL4ClassElementStubType();

    IStubElementType<MQL4FunctionElementStub, MQL4FunctionElement> FUNCTION = new MQL4FunctionElementStubType(false);

    IStubElementType<MQL4FunctionElementStub, MQL4FunctionElement> FUNCTION_DECLARATION = new MQL4FunctionElementStubType(true);

    // v22: enum-type + top-level global variable stub types. Declared here (not in MQL4Elements)
    // so the plugin.xml <stubElementTypeHolder class="MQL4StubElements"> registers them; they are
    // inherited by MQL4Elements (extends this) so ENUM_STATEMENT / VAR_DEFINITION keep their names.
    IStubElementType<MQL4EnumElementStub, MQL4EnumElement> ENUM_STATEMENT = new MQL4EnumElementStubType();

    IStubElementType<MQL4GlobalVarElementStub, MQL4VarDefinitionElement> VAR_DEFINITION = new MQL4GlobalVarElementStubType();

    // v26: `typedef int (*TName)(...)` and `#define NAME` are named, indexed declarations.
    IStubElementType<MQL4NamedElementStub<MQL4TypedefElement>, MQL4TypedefElement> TYPEDEF =
            new MQL4NamedElementStubType<>("TYPEDEF", "mqlidea.typedef", MQL4IndexKeys.TYPEDEF_NAME_INDEX_KEY, MQL4TypedefElement::new);

    IStubElementType<MQL4NamedElementStub<MQL4DefineElement>, MQL4DefineElement> PREPROCESSOR_DEFINE_BLOCK =
            new MQL4NamedElementStubType<>("PREPROCESSOR_DEFINE_BLOCK", "mqlidea.define", MQL4IndexKeys.DEFINE_NAME_INDEX_KEY, MQL4DefineElement::new);
}

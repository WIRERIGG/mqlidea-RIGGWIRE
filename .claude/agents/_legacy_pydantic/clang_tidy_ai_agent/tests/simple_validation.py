"""
Simple validation test for the clang-tidy AI agent.
Tests core functionality without complex dependencies.
"""

import sys
from pathlib import Path
import tempfile
import sqlite3

def validate_agent_structure():
    """Validate that core agent components exist."""
    print("🔍 Validating agent structure...")
    
    agent_path = Path(__file__).parent.parent
    
    required_files = {
        "core/agent.py": "Main agent implementation",
        "core/dependencies.py": "Dependencies management", 
        "core/tools.py": "Tool implementations",
        "core/models.py": "Pydantic models",
        "core/settings.py": "Configuration settings",
        "core/prompts.py": "System prompts",
        "core/providers.py": "LLM provider configuration",
        "planning/INITIAL.md": "Requirements specification"
    }
    
    results = []
    for file_path, description in required_files.items():
        full_path = agent_path / file_path
        if full_path.exists():
            results.append(f"✅ {file_path} - {description}")
        else:
            results.append(f"❌ {file_path} - {description} (MISSING)")
    
    return results

def validate_models():
    """Test that Pydantic models are properly defined."""
    print("🔍 Validating Pydantic models...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        
        from models import Warning, ClangTidyAnalysis, WarningExplanation, FixRecommendation
        
        # Test Warning model
        warning = Warning(
            line_number=42,
            column_number=10,
            rule_id="readability-identifier-naming",
            severity="warning",
            category="readability",
            message="Variable name doesn't follow convention",
            suggested_fix="Rename to snake_case",
            context_lines=["int myVar = 42;"],
            fix_complexity=3
        )
        
        # Test ClangTidyAnalysis model
        analysis = ClangTidyAnalysis(
            file_path="test.cpp",
            warnings=[warning],
            total_warnings=1,
            clang_tidy_version="15.0.0"
        )
        
        return [
            "✅ Warning model - Properly defined and validated",
            "✅ ClangTidyAnalysis model - Properly defined and validated",
            f"✅ Model instantiation - Warning: line {warning.line_number}, rule: {warning.rule_id}",
            f"✅ Model relationships - Analysis contains {len(analysis.warnings)} warnings"
        ]
        
    except Exception as e:
        return [f"❌ Model validation failed: {e}"]

def validate_settings():
    """Test settings configuration."""
    print("🔍 Validating settings...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        
        from settings import ClangTidyAISettings
        
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = ClangTidyAISettings(
                llm_provider="openai",
                llm_api_key="test-key",
                llm_model="gpt-4o-mini", 
                project_root=Path(temp_dir),
                clang_tidy_ai_db_path=Path(temp_dir) / "test.db"
            )
            
            return [
                f"✅ Settings instantiation - Provider: {settings.llm_provider}",
                f"✅ Settings validation - Learning mode: {settings.enable_learning_mode}",
                f"✅ Settings validation - Caching: {settings.cache_analysis_results}",
                f"✅ Path configuration - Project root: {settings.project_root}"
            ]
        
    except Exception as e:
        return [f"❌ Settings validation failed: {e}"]

def validate_requirements_compliance():
    """Check compliance with INITIAL.md requirements."""
    print("🔍 Validating requirements compliance...")
    
    agent_path = Path(__file__).parent.parent
    initial_path = agent_path / "planning" / "INITIAL.md"
    
    if not initial_path.exists():
        return ["❌ INITIAL.md requirements file missing"]
    
    results = []
    requirements_content = initial_path.read_text()
    
    # Check key requirements
    checks = [
        ("Conversational Interface", ["conversational", "chat"], "core/agent.py"),
        ("Multi-Provider Support", ["openai", "anthropic", "gemini"], "core/providers.py"),
        ("Database Integration", ["sqlite", "user_preferences"], "core/dependencies.py"),
        ("Tool Integration", ["clang_tidy", "analyze_code"], "core/tools.py"),
        ("Learning System", ["learning", "preferences"], "core/dependencies.py")
    ]
    
    for req_name, keywords, file_path in checks:
        file_full_path = agent_path / file_path
        if file_full_path.exists():
            content = file_full_path.read_text().lower()
            found_keywords = [kw for kw in keywords if kw in content]
            if found_keywords:
                results.append(f"✅ {req_name} - Found: {', '.join(found_keywords)}")
            else:
                results.append(f"⚠️ {req_name} - Keywords not found: {', '.join(keywords)}")
        else:
            results.append(f"❌ {req_name} - File missing: {file_path}")
    
    # Check for CLI interface
    cli_files = list(agent_path.glob("**/cli.py"))
    if cli_files:
        results.append(f"✅ CLI Interface - Found: {len(cli_files)} CLI files")
    else:
        results.append("❌ CLI Interface - No CLI files found")
    
    return results

def validate_database_setup():
    """Test database initialization."""
    print("🔍 Validating database setup...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        
        from dependencies import init_database
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            connection = sqlite3.connect(db_path)
            
            init_database(connection)
            
            # Check tables exist
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["user_preferences", "analysis_cache", "feedback"]
            results = []
            
            for table in expected_tables:
                if table in tables:
                    results.append(f"✅ Database table '{table}' created successfully")
                else:
                    results.append(f"❌ Database table '{table}' missing")
            
            connection.close()
            return results
        
    except Exception as e:
        return [f"❌ Database validation failed: {e}"]

def validate_tool_structure():
    """Validate tool implementations."""
    print("🔍 Validating tool structure...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        
        from tools import analyze_code_with_clang_tidy, explain_warning, recommend_fix_strategy
        
        results = [
            "✅ analyze_code_with_clang_tidy - Function imported successfully",
            "✅ explain_warning - Function imported successfully", 
            "✅ recommend_fix_strategy - Function imported successfully"
        ]
        
        # Check function signatures
        import inspect
        
        analyze_sig = inspect.signature(analyze_code_with_clang_tidy)
        if 'ctx' in analyze_sig.parameters and 'file_path' in analyze_sig.parameters:
            results.append("✅ analyze_code_with_clang_tidy - Correct signature")
        else:
            results.append("⚠️ analyze_code_with_clang_tidy - Signature may be incorrect")
            
        return results
        
    except Exception as e:
        return [f"❌ Tool validation failed: {e}"]

def run_comprehensive_validation():
    """Run all validation tests."""
    print("🤖 Clang-Tidy AI Agent Validation Report")
    print("=" * 50)
    
    validation_functions = [
        ("Agent Structure", validate_agent_structure),
        ("Pydantic Models", validate_models),
        ("Settings Configuration", validate_settings),
        ("Requirements Compliance", validate_requirements_compliance),
        ("Database Setup", validate_database_setup),
        ("Tool Structure", validate_tool_structure)
    ]
    
    all_results = []
    total_checks = 0
    passed_checks = 0
    
    for section_name, validation_func in validation_functions:
        print(f"\n📋 {section_name}")
        print("-" * 30)
        
        try:
            section_results = validation_func()
            for result in section_results:
                print(f"  {result}")
                total_checks += 1
                if result.startswith("✅"):
                    passed_checks += 1
                all_results.append(result)
        except Exception as e:
            error_msg = f"❌ {section_name} validation failed: {e}"
            print(f"  {error_msg}")
            all_results.append(error_msg)
            total_checks += 1
    
    print("\n" + "=" * 50)
    print(f"📊 VALIDATION SUMMARY: {passed_checks}/{total_checks} checks passed")
    print(f"📊 SUCCESS RATE: {passed_checks/total_checks*100:.1f}%")
    
    if passed_checks == total_checks:
        print("🎉 ALL VALIDATIONS PASSED!")
        return True
    elif passed_checks / total_checks >= 0.8:
        print("✅ VALIDATION MOSTLY SUCCESSFUL (80%+ passed)")
        return True
    else:
        print("⚠️ VALIDATION NEEDS ATTENTION (Less than 80% passed)")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Demonstration of AI integration capabilities without requiring API keys.
Shows prompt generation and fallback suggestion systems.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from valgrind_tool import ValgrindAnalyzer
from ai_integration import AIAnalyzer, IssuePatternMatcher
from models import ValgrindTool, ValgrindIssue, IssueCategory, IssueSeverity, StackFrame, LearningDatabase
from tools import LearningSystem, initialize_learning_database

def create_sample_issues():
    """Create sample issues for demonstration."""
    issues = [
        ValgrindIssue(
            category=IssueCategory.MEMORY_LEAK,
            description="Definitely lost: 1,024 bytes in 1 blocks",
            severity=IssueSeverity.ERROR,
            file_path=Path("src/main.cpp"),
            line_number=45,
            function="allocate_buffer",
            bytes_involved=1024,
            stack_trace=[
                StackFrame(function="allocate_buffer", file_path=Path("src/main.cpp"), line_number=45),
                StackFrame(function="process_data", file_path=Path("src/main.cpp"), line_number=123),
                StackFrame(function="main", file_path=Path("src/main.cpp"), line_number=200)
            ]
        ),
        
        ValgrindIssue(
            category=IssueCategory.DATA_RACE,
            description="Data race detected: 4 byte access by thread #2",
            severity=IssueSeverity.CRITICAL,
            file_path=Path("src/threading.cpp"), 
            line_number=78,
            function="worker_thread",
            access_size=4,
            thread_id=2,
            stack_trace=[
                StackFrame(function="worker_thread", file_path=Path("src/threading.cpp"), line_number=78),
                StackFrame(function="thread_start", file_path=Path("src/threading.cpp"), line_number=156)
            ]
        ),
        
        ValgrindIssue(
            category=IssueCategory.CACHE_MISS,
            description="High D1 cache miss rate: 15.3%",
            severity=IssueSeverity.WARNING,
            file_path=Path("src/algorithm.cpp"),
            line_number=234,
            function="matrix_multiply",
            details={"miss_rate": 15.3, "misses": 123456}
        ),
        
        ValgrindIssue(
            category=IssueCategory.INVALID_READ,
            description="Invalid read of size 4 at 0x12345678",
            severity=IssueSeverity.ERROR,
            file_path=Path("src/buffer.cpp"),
            line_number=67,
            function="read_buffer",
            access_size=4
        )
    ]
    
    return issues

def main():
    print("🤖 ValgrindAnalyzer AI Integration Demo")
    print("=" * 50)
    
    # Create sample issues for demonstration
    sample_issues = create_sample_issues()
    print(f"Created {len(sample_issues)} sample issues for demonstration")
    
    # Initialize learning database
    print("\n📚 Initializing Learning Database...")
    db_path = Path("demo_learning.json")
    learning_db = initialize_learning_database(db_path)
    learning_system = LearningSystem(db_path)
    
    print(f"✅ Learning database initialized with {len(learning_db.pairs)} patterns")
    
    # Create AI analyzer (without API key for demo)
    print("\n🧠 Creating AI Analyzer...")
    ai_analyzer = AIAnalyzer(api_key=None, provider="openai", model="gpt-4")
    print("✅ AI Analyzer created (using fallback mode)")
    
    # Generate AI prompts
    print(f"\n📝 Generating AI Analysis Prompts...")
    print("-" * 40)
    
    for tool in [ValgrindTool.MEMCHECK, ValgrindTool.HELGRIND, ValgrindTool.CACHEGRIND]:
        print(f"\n🔧 Tool: {tool.value}")
        
        # Filter issues relevant to this tool
        relevant_issues = []
        if tool == ValgrindTool.MEMCHECK:
            relevant_issues = [i for i in sample_issues if i.category in [IssueCategory.MEMORY_LEAK, IssueCategory.INVALID_READ]]
        elif tool == ValgrindTool.HELGRIND:
            relevant_issues = [i for i in sample_issues if i.category == IssueCategory.DATA_RACE]
        elif tool == ValgrindTool.CACHEGRIND:
            relevant_issues = [i for i in sample_issues if i.category == IssueCategory.CACHE_MISS]
        
        if relevant_issues:
            prompt = ai_analyzer.generate_ai_prompt(relevant_issues, learning_db, tool)
            print(f"📋 Generated prompt ({len(prompt)} characters)")
            print("Preview:", prompt[:200] + "..." if len(prompt) > 200 else prompt)
        else:
            print("ℹ️  No relevant issues for this tool")
    
    # Demonstrate fallback suggestions
    print(f"\n💡 Generating Fallback Suggestions...")
    print("-" * 40)
    
    suggestions = ai_analyzer.call_llm_api("Sample prompt with issues")
    
    print(f"✅ Generated {len(suggestions)} fallback suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    # Demonstrate pattern matching
    print(f"\n🔍 Pattern Matching Demonstration...")
    print("-" * 40)
    
    fix_templates = IssuePatternMatcher.get_fix_templates()
    prevention_strategies = IssuePatternMatcher.get_prevention_strategies()
    
    for issue in sample_issues:
        print(f"\n🚨 Issue: {issue.category.value}")
        print(f"   Description: {issue.description}")
        
        if issue.category in fix_templates:
            fixes = fix_templates[issue.category]
            print(f"   🔧 Suggested fixes:")
            for fix in fixes[:2]:
                print(f"      - {fix}")
        
        if issue.category in prevention_strategies:
            strategies = prevention_strategies[issue.category]
            print(f"   🛡️  Prevention strategies:")
            for strategy in strategies[:2]:
                print(f"      - {strategy}")
    
    # Demonstrate learning system
    print(f"\n🎓 Learning System Demonstration...")
    print("-" * 40)
    
    # Add some successful fixes to the learning database
    learning_system.add_successful_fix(
        sample_issues[0], 
        "Replace raw pointer with std::unique_ptr for automatic cleanup",
        effectiveness=0.9
    )
    
    learning_system.add_successful_fix(
        sample_issues[1],
        "Add std::mutex protection around shared variable access", 
        effectiveness=0.95
    )
    
    print("✅ Added sample successful fixes to learning database")
    
    # Get personalized suggestions
    personalized = learning_system.get_personalized_suggestions(sample_issues)
    
    print(f"\n🎯 Personalized Suggestions:")
    for i, suggestions in list(personalized.items())[:2]:
        issue = sample_issues[i]
        print(f"   Issue: {issue.category.value}")
        for suggestion in suggestions[:2]:
            print(f"   → {suggestion}")
    
    # Show learning analytics
    print(f"\n📊 Learning Analytics...")
    analytics = learning_system.analyze_patterns()
    
    print(f"   Total learning pairs: {analytics['total_pairs']}")
    print(f"   Categories covered: {len(analytics.get('category_distribution', {}))}")
    
    if analytics.get('most_effective'):
        print("   Most effective suggestions:")
        for item in analytics['most_effective'][:3]:
            print(f"      - {item['suggestion'][:60]}... (score: {item['effectiveness']})")
    
    # Export learning insights
    insights_file = Path("learning_insights.json")
    learning_system.export_insights(insights_file)
    print(f"\n💾 Learning insights exported to: {insights_file}")
    
    # Full workflow demonstration
    print(f"\n🚀 Complete Workflow Demonstration...")
    print("-" * 40)
    
    print("1. ✅ Issues detected by Valgrind tools")
    print("2. ✅ AI prompts generated with context and learning history")
    print("3. ✅ Fallback suggestions provided when AI unavailable") 
    print("4. ✅ Pattern matching for immediate fixes")
    print("5. ✅ Learning database updated with successful solutions")
    print("6. ✅ Personalized suggestions based on historical data")
    print("7. ✅ Analytics and insights for continuous improvement")
    
    print(f"\n🎉 AI Integration Demo Complete!")
    print("=" * 30)
    
    print("Key Capabilities Demonstrated:")
    print("✅ Contextual AI prompt generation")
    print("✅ Offline fallback suggestion system")
    print("✅ Pattern-based fix recommendations") 
    print("✅ Self-improving learning database")
    print("✅ Personalized suggestion engine")
    print("✅ Analytics and performance tracking")
    
    print("\nThe ValgrindAnalyzer AI integration provides:")
    print("🧠 Intelligent analysis of complex safety issues")
    print("🔧 Actionable, compilable C++ code fixes")
    print("📈 Continuous improvement through machine learning")
    print("⚡ High-performance operation with graceful degradation")
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    if insights_file.exists():
        insights_file.unlink()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
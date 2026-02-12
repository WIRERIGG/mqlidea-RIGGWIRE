"""
Learning system for Valgrind analyzer self-improvement.
Tracks issue-suggestion pairs and learns from successful fixes.
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from models import LearningDatabase, IssueSuggestionPair, IssueCategory, ValgrindIssue


class LearningSystem:
    """Self-improvement learning system for Valgrind analysis."""
    
    def __init__(self, db_path: Path = Path("valgrind_learning.json")):
        self.db_path = db_path
        self.database = self._load_database()
        
    def _load_database(self) -> LearningDatabase:
        """Load learning database from file."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    return LearningDatabase.model_validate(data)
            except Exception as e:
                print(f"Warning: Failed to load learning database: {e}")
                return LearningDatabase()
        
        return LearningDatabase()
    
    def save_database(self):
        """Save learning database to file."""
        try:
            # Create backup of existing database
            if self.db_path.exists():
                backup_path = self.db_path.with_suffix('.bak')
                self.db_path.rename(backup_path)
            
            # Save current database
            with open(self.db_path, 'w') as f:
                f.write(self.database.model_dump_json(indent=2))
                
        except Exception as e:
            print(f"Warning: Failed to save learning database: {e}")
    
    def add_successful_fix(self, issue: ValgrindIssue, suggestion: str, effectiveness: float = 1.0):
        """Record a successful fix for learning."""
        self.database.add_pair(
            issue.category,
            issue.description,
            suggestion
        )
        
        # Update effectiveness if this pair already exists
        for pair in self.database.pairs:
            if (pair.issue_category == issue.category and 
                pair.issue_description == issue.description and
                pair.suggestion == suggestion):
                pair.effectiveness_score = max(pair.effectiveness_score, effectiveness)
                pair.usage_count += 1
                break
        
        self.save_database()
    
    def get_suggestions_for_issue(self, issue: ValgrindIssue, limit: int = 3) -> List[str]:
        """Get relevant suggestions for an issue based on learning."""
        # Get category-based suggestions
        category_suggestions = self.database.get_suggestions(issue.category, limit)
        
        # Look for similar descriptions
        description_suggestions = []
        for pair in self.database.pairs:
            if (pair.issue_category == issue.category and
                self._description_similarity(pair.issue_description, issue.description) > 0.7):
                if pair.suggestion not in category_suggestions:
                    description_suggestions.append(pair.suggestion)
        
        # Combine and limit
        all_suggestions = category_suggestions + description_suggestions
        return all_suggestions[:limit]
    
    def _description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between issue descriptions."""
        # Simple word-based similarity
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def analyze_patterns(self) -> Dict[str, any]:
        """Analyze learning patterns and provide insights."""
        if not self.database.pairs:
            return {"message": "No learning data available"}
        
        # Category distribution
        category_counts = {}
        for pair in self.database.pairs:
            category = pair.issue_category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Most effective suggestions
        effective_suggestions = sorted(
            self.database.pairs,
            key=lambda p: p.effectiveness_score * p.usage_count,
            reverse=True
        )[:10]
        
        # Recent patterns (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_pairs = [p for p in self.database.pairs if p.timestamp >= recent_cutoff]
        
        return {
            "total_pairs": len(self.database.pairs),
            "category_distribution": category_counts,
            "most_effective": [
                {
                    "category": p.issue_category.value,
                    "suggestion": p.suggestion[:100] + "..." if len(p.suggestion) > 100 else p.suggestion,
                    "effectiveness": p.effectiveness_score,
                    "usage_count": p.usage_count
                }
                for p in effective_suggestions
            ],
            "recent_patterns": len(recent_pairs),
            "learning_velocity": len(recent_pairs) / max(1, len(self.database.pairs)) * 100
        }
    
    def get_personalized_suggestions(self, issues: List[ValgrindIssue]) -> Dict[int, List[str]]:
        """Get personalized suggestions based on learning history."""
        suggestions = {}
        
        for i, issue in enumerate(issues):
            issue_suggestions = self.get_suggestions_for_issue(issue)
            
            # Add pattern-based suggestions
            pattern_suggestions = self._get_pattern_suggestions(issue)
            
            # Combine and deduplicate
            combined = issue_suggestions + pattern_suggestions
            unique_suggestions = list(dict.fromkeys(combined))  # Preserve order, remove duplicates
            
            suggestions[i] = unique_suggestions[:5]  # Limit to top 5
        
        return suggestions
    
    def _get_pattern_suggestions(self, issue: ValgrindIssue) -> List[str]:
        """Get suggestions based on learned patterns."""
        suggestions = []
        
        # File-based patterns
        if issue.file_path:
            file_extension = issue.file_path.suffix
            for pair in self.database.pairs:
                if (pair.issue_category == issue.category and
                    file_extension in pair.issue_description):
                    if pair.suggestion not in suggestions:
                        suggestions.append(pair.suggestion)
        
        # Function-based patterns
        if issue.function:
            for pair in self.database.pairs:
                if (pair.issue_category == issue.category and
                    issue.function in pair.issue_description):
                    if pair.suggestion not in suggestions:
                        suggestions.append(pair.suggestion)
        
        return suggestions
    
    def update_effectiveness(self, suggestion: str, category: IssueCategory, new_score: float):
        """Update effectiveness score for a suggestion."""
        for pair in self.database.pairs:
            if (pair.issue_category == category and 
                pair.suggestion == suggestion):
                # Use weighted average for effectiveness
                old_weight = pair.usage_count
                new_weight = 1
                total_weight = old_weight + new_weight
                
                pair.effectiveness_score = (
                    (pair.effectiveness_score * old_weight + new_score * new_weight) / total_weight
                )
                break
        
        self.save_database()
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old learning data to prevent database bloat."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Keep pairs that are either recent or highly effective
        filtered_pairs = []
        for pair in self.database.pairs:
            if (pair.timestamp >= cutoff or 
                pair.effectiveness_score > 0.8 or 
                pair.usage_count > 5):
                filtered_pairs.append(pair)
        
        original_count = len(self.database.pairs)
        self.database.pairs = filtered_pairs
        self.save_database()
        
        cleaned_count = original_count - len(filtered_pairs)
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} old learning entries")
    
    def export_insights(self, output_path: Path):
        """Export learning insights to JSON file."""
        insights = self.analyze_patterns()
        
        # Add detailed category analysis
        category_details = {}
        for category in IssueCategory:
            category_pairs = [p for p in self.database.pairs if p.issue_category == category]
            if category_pairs:
                category_details[category.value] = {
                    "count": len(category_pairs),
                    "avg_effectiveness": sum(p.effectiveness_score for p in category_pairs) / len(category_pairs),
                    "top_suggestions": [
                        p.suggestion for p in sorted(
                            category_pairs, 
                            key=lambda x: x.effectiveness_score * x.usage_count, 
                            reverse=True
                        )[:3]
                    ]
                }
        
        insights["category_details"] = category_details
        insights["export_timestamp"] = datetime.now().isoformat()
        
        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2)
    
    def get_database_stats(self) -> Dict[str, any]:
        """Get database statistics."""
        if not self.database.pairs:
            return {"empty": True}
        
        return {
            "total_pairs": len(self.database.pairs),
            "last_updated": self.database.last_updated.isoformat(),
            "version": self.database.version,
            "oldest_entry": min(p.timestamp for p in self.database.pairs).isoformat(),
            "newest_entry": max(p.timestamp for p in self.database.pairs).isoformat(),
            "categories_covered": len(set(p.issue_category for p in self.database.pairs)),
            "avg_usage_count": sum(p.usage_count for p in self.database.pairs) / len(self.database.pairs),
            "avg_effectiveness": sum(p.effectiveness_score for p in self.database.pairs) / len(self.database.pairs)
        }


# Convenience functions
def update_learning_db(db_path: Path, issues: List[ValgrindIssue], suggestions: List[str]):
    """Update learning database with new issue-suggestion pairs."""
    learning = LearningSystem(db_path)
    
    # Pair issues with suggestions (simple heuristic matching)
    for i, issue in enumerate(issues):
        if i < len(suggestions):
            learning.add_successful_fix(issue, suggestions[i])
        elif suggestions:
            # Use first suggestion for remaining issues
            learning.add_successful_fix(issue, suggestions[0])


def get_learned_suggestions(db_path: Path, issues: List[ValgrindIssue]) -> Dict[str, List[str]]:
    """Get learned suggestions for issues."""
    learning = LearningSystem(db_path)
    suggestions = learning.get_personalized_suggestions(issues)
    
    # Convert issue keys to strings for JSON serialization
    return {
        f"{issue.category.value}_{i}": sug_list 
        for i, (issue, sug_list) in enumerate(suggestions.items())
    }


def initialize_learning_database(db_path: Path) -> LearningDatabase:
    """Initialize learning database with common patterns."""
    learning = LearningSystem(db_path)
    
    # Add some seed suggestions for common categories
    seed_data = [
        (IssueCategory.MEMORY_LEAK, "Memory leak detected", "Replace raw pointers with std::unique_ptr"),
        (IssueCategory.INVALID_READ, "Invalid read access", "Add bounds checking before array access"),
        (IssueCategory.DATA_RACE, "Data race detected", "Protect shared data with std::mutex"),
        (IssueCategory.UNINITIALIZED_VALUE, "Uninitialized variable", "Initialize all variables at declaration"),
        (IssueCategory.CACHE_MISS, "High cache miss rate", "Improve data locality by reorganizing structures"),
    ]
    
    for category, description, suggestion in seed_data:
        pair = IssueSuggestionPair(
            issue_category=category,
            issue_description=description,
            suggestion=suggestion,
            effectiveness_score=0.8,  # Default good effectiveness
            usage_count=1
        )
        learning.database.pairs.append(pair)
    
    learning.save_database()
    return learning.database
"""HFT (High-Frequency Trading) specialization module for Blitzfire Code Agent."""

import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .models import CodeIssue, OptimizationTier, Architecture
from .dependencies import HFTAnalyzer


class HFTRiskLevel(Enum):
    """Risk levels for HFT code analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HFTRiskCategory(Enum):
    """Categories of HFT-specific risks."""
    OVERFLOW = "overflow"
    RACE_CONDITION = "race_condition"
    DETERMINISM = "determinism"
    LATENCY = "latency"
    REGULATORY = "regulatory"
    DATA_INTEGRITY = "data_integrity"


@dataclass
class HFTPattern:
    """Represents an HFT-specific code pattern."""
    name: str
    pattern: re.Pattern
    category: HFTRiskCategory
    risk_level: HFTRiskLevel
    description: str
    suggestion: str
    impact_description: str


class HFTSpecializationEngine:
    """Specialized engine for HFT code analysis and optimization."""

    def __init__(self):
        """Initialize HFT specialization patterns."""
        self.risk_patterns = self._init_hft_patterns()
        self.optimization_patterns = self._init_hft_optimizations()
        self.regulatory_patterns = self._init_regulatory_patterns()

    def _init_hft_patterns(self) -> List[HFTPattern]:
        """Initialize HFT-specific risk patterns."""
        return [
            # Overflow Risks
            HFTPattern(
                name="integer_overflow_risk",
                pattern=re.compile(r'(price|quantity|volume|size)\s*[+\-*]\s*\w+(?!\s*[<>=])'),
                category=HFTRiskCategory.OVERFLOW,
                risk_level=HFTRiskLevel.HIGH,
                description="Potential integer overflow in financial calculations",
                suggestion="Use SafeInt library or explicit overflow checks",
                impact_description="Could cause incorrect trade calculations and financial losses"
            ),

            HFTPattern(
                name="unchecked_multiplication",
                pattern=re.compile(r'(\w+)\s*\*\s*(\w+)(?!\s*[<>=])(?!.*SafeInt|.*check)'),
                category=HFTRiskCategory.OVERFLOW,
                risk_level=HFTRiskLevel.MEDIUM,
                description="Unchecked multiplication that could overflow",
                suggestion="Add overflow checks or use safe arithmetic",
                impact_description="Silent overflow could corrupt financial calculations"
            ),

            # Race Conditions
            HFTPattern(
                name="non_atomic_shared_variable",
                pattern=re.compile(r'(?<!atomic\s)(?<!std::atomic)\s*(\w+)\s*=\s*[^=].*(?=;)(?!.*\.load\(\)|.*\.store\()'),
                category=HFTRiskCategory.RACE_CONDITION,
                risk_level=HFTRiskLevel.CRITICAL,
                description="Non-atomic assignment to potentially shared variable",
                suggestion="Use std::atomic or proper synchronization",
                impact_description="Race conditions can cause data corruption and inconsistent state"
            ),

            HFTPattern(
                name="shared_counter_increment",
                pattern=re.compile(r'(\+\+\w+|\w+\+\+|--\w+|\w+--)(?!.*atomic)'),
                category=HFTRiskCategory.RACE_CONDITION,
                risk_level=HFTRiskLevel.HIGH,
                description="Non-atomic increment/decrement of shared counter",
                suggestion="Use atomic operations: std::atomic<T>::fetch_add()",
                impact_description="Lost updates in concurrent access scenarios"
            ),

            # Determinism Issues
            HFTPattern(
                name="floating_point_equality",
                pattern=re.compile(r'(price|rate|value)\s*[!=]=\s*[\d.]+[f]?'),
                category=HFTRiskCategory.DETERMINISM,
                risk_level=HFTRiskLevel.HIGH,
                description="Direct floating-point equality comparison",
                suggestion="Use epsilon-based comparison: abs(a - b) < epsilon",
                impact_description="Non-deterministic behavior due to floating-point precision"
            ),

            HFTPattern(
                name="uninitialized_variable",
                pattern=re.compile(r'(double|float|int)\s+(\w+);(?!\s*\w+\s*=)'),
                category=HFTRiskCategory.DETERMINISM,
                risk_level=HFTRiskLevel.MEDIUM,
                description="Potentially uninitialized variable",
                suggestion="Initialize all variables explicitly",
                impact_description="Undefined behavior leading to non-deterministic results"
            ),

            # Latency Risks
            HFTPattern(
                name="blocking_synchronization",
                pattern=re.compile(r'(mutex|lock_guard|unique_lock|shared_lock)(?!.*try_lock)'),
                category=HFTRiskCategory.LATENCY,
                risk_level=HFTRiskLevel.HIGH,
                description="Blocking synchronization in potential hot path",
                suggestion="Use lock-free algorithms or try_lock patterns",
                impact_description="Blocking can cause unpredictable latency spikes"
            ),

            HFTPattern(
                name="dynamic_allocation",
                pattern=re.compile(r'(new\s+\w+|malloc|vector\.push_back)(?!.*reserve)'),
                category=HFTRiskCategory.LATENCY,
                risk_level=HFTRiskLevel.MEDIUM,
                description="Dynamic memory allocation in hot path",
                suggestion="Pre-allocate memory or use memory pools",
                impact_description="Memory allocation can cause latency spikes"
            ),

            # Data Integrity
            HFTPattern(
                name="unchecked_array_access",
                pattern=re.compile(r'(\w+)\[(\w+)\](?!.*(?:at\(|bounds|check))'),
                category=HFTRiskCategory.DATA_INTEGRITY,
                risk_level=HFTRiskLevel.MEDIUM,
                description="Unchecked array/vector access",
                suggestion="Use at() method or add bounds checking",
                impact_description="Buffer overflow could corrupt critical trading data"
            ),

            HFTPattern(
                name="missing_error_handling",
                pattern=re.compile(r'(open|read|write|send|recv)\s*\([^)]+\)(?!\s*(?:if|&&|\|\||==|!=))'),
                category=HFTRiskCategory.DATA_INTEGRITY,
                risk_level=HFTRiskLevel.HIGH,
                description="Missing error handling for I/O operations",
                suggestion="Always check return values and handle errors",
                impact_description="Silent failures could lead to data loss or corruption"
            )
        ]

    def _init_hft_optimizations(self) -> List[Dict[str, Any]]:
        """Initialize HFT-specific optimization patterns."""
        return [
            {
                "name": "Lock-Free Queue Implementation",
                "pattern": re.compile(r'queue|deque.*push|pop'),
                "tier": 5,
                "description": "Replace standard queue with lock-free implementation",
                "code_before": '''
std::queue<Order> order_queue;
std::mutex queue_mutex;

void add_order(const Order& order) {
    std::lock_guard<std::mutex> lock(queue_mutex);
    order_queue.push(order);
}''',
                "code_after": '''
#include <boost/lockfree/queue.hpp>

boost::lockfree::queue<Order*> order_queue{1000};

void add_order(const Order& order) {
    Order* order_ptr = new Order(order);  // Use memory pool in production
    while (!order_queue.push(order_ptr)) {
        // Busy wait or handle queue full
    }
}''',
                "explanation": "Lock-free queues eliminate blocking and provide predictable latency. Essential for high-frequency trading where microsecond delays matter.",
                "estimated_speedup": 10.0,
                "hft_specific": True
            },

            {
                "name": "Atomic Price Updates",
                "pattern": re.compile(r'price\s*=|price\s*\+='),
                "tier": 3,
                "description": "Use atomic operations for price updates",
                "code_before": '''
double current_price = 100.50;

void update_price(double new_price) {
    current_price = new_price;  // Race condition!
}''',
                "code_after": '''
std::atomic<double> current_price{100.50};

void update_price(double new_price) {
    current_price.store(new_price, std::memory_order_release);
}''',
                "explanation": "Atomic operations ensure thread-safe price updates without locks, maintaining consistency across multiple trading threads.",
                "estimated_speedup": 3.0,
                "hft_specific": True
            },

            {
                "name": "NUMA-Aware Memory Layout",
                "pattern": re.compile(r'struct.*Order|class.*Order'),
                "tier": 6,
                "description": "Optimize data structures for NUMA architecture",
                "code_before": '''
struct Order {
    uint64_t order_id;
    double price;
    uint32_t quantity;
    char symbol[16];
    uint64_t timestamp;
};''',
                "code_after": '''
// Align to cache line and group frequently accessed fields
struct __attribute__((aligned(64))) Order {
    // Hot data - accessed frequently together
    double price;
    uint32_t quantity;
    uint64_t timestamp;

    // Cold data - accessed less frequently
    uint64_t order_id;
    char symbol[16];
    char padding[24];  // Ensure 64-byte alignment
};''',
                "explanation": "Cache-line aligned structures reduce false sharing and improve memory access patterns on NUMA systems.",
                "estimated_speedup": 2.0,
                "hft_specific": True
            },

            {
                "name": "Branch Prediction Optimization",
                "pattern": re.compile(r'if\s*\([^)]*\)\s*{[^}]*(?:likely|unlikely|rare)'),
                "tier": 4,
                "description": "Add branch prediction hints for common paths",
                "code_before": '''
if (order_type == MARKET_ORDER) {
    process_market_order(order);
} else {
    process_limit_order(order);
}''',
                "code_after": '''
if (__builtin_expect(order_type == MARKET_ORDER, 1)) {  // Likely
    process_market_order(order);
} else {
    process_limit_order(order);
}''',
                "explanation": "Branch prediction hints help the CPU predict which path is more likely, reducing pipeline stalls in tight trading loops.",
                "estimated_speedup": 1.5,
                "hft_specific": True
            }
        ]

    def _init_regulatory_patterns(self) -> List[Dict[str, Any]]:
        """Initialize regulatory compliance patterns."""
        return [
            {
                "pattern": re.compile(r'log|audit|trace'),
                "requirement": "Audit trail logging required for order lifecycle",
                "suggestion": "Ensure all order state changes are logged with timestamps"
            },
            {
                "pattern": re.compile(r'exception|throw|try.*catch'),
                "requirement": "Error handling and recovery procedures",
                "suggestion": "Document error recovery procedures for regulatory compliance"
            },
            {
                "pattern": re.compile(r'time|timestamp'),
                "requirement": "Clock synchronization and timestamp accuracy",
                "suggestion": "Use synchronized clocks and high-resolution timestamps"
            }
        ]

    def analyze_hft_code(
        self,
        code_content: str,
        audit_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Perform comprehensive HFT-specific code analysis."""
        results = {
            "risk_issues": [],
            "optimization_opportunities": [],
            "regulatory_concerns": [],
            "safety_score": 10,
            "latency_score": 10,
            "reliability_score": 10
        }

        lines = code_content.split('\n')

        # Analyze each line for HFT-specific patterns
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('//'):
                continue

            # Check risk patterns
            for pattern in self.risk_patterns:
                if pattern.pattern.search(line_stripped):
                    issue = CodeIssue(
                        line_number=line_num,
                        issue_type=f"hft_{pattern.category.value}",
                        severity=pattern.risk_level.value,
                        description=f"{pattern.description}: {line_stripped[:50]}...",
                        suggestion=pattern.suggestion,
                        estimated_impact=self._calculate_hft_impact(pattern)
                    )
                    results["risk_issues"].append(issue)

                    # Adjust scores based on risk
                    if pattern.category == HFTRiskCategory.RACE_CONDITION:
                        results["reliability_score"] -= 2
                    elif pattern.category == HFTRiskCategory.LATENCY:
                        results["latency_score"] -= 1
                    elif pattern.category == HFTRiskCategory.OVERFLOW:
                        results["safety_score"] -= 2

        # Check for optimization opportunities
        for opt_pattern in self.optimization_patterns:
            if opt_pattern["pattern"].search(code_content):
                results["optimization_opportunities"].append({
                    "name": opt_pattern["name"],
                    "description": opt_pattern["description"],
                    "estimated_speedup": opt_pattern["estimated_speedup"],
                    "tier": opt_pattern["tier"]
                })

        # Check regulatory patterns
        for reg_pattern in self.regulatory_patterns:
            if reg_pattern["pattern"].search(code_content):
                results["regulatory_concerns"].append({
                    "requirement": reg_pattern["requirement"],
                    "suggestion": reg_pattern["suggestion"]
                })

        # Ensure scores don't go below 1
        for score_key in ["safety_score", "latency_score", "reliability_score"]:
            results[score_key] = max(1, results[score_key])

        return results

    def _calculate_hft_impact(self, pattern: HFTPattern) -> float:
        """Calculate the impact score for an HFT pattern."""
        base_impacts = {
            HFTRiskLevel.LOW: 1.1,
            HFTRiskLevel.MEDIUM: 1.3,
            HFTRiskLevel.HIGH: 2.0,
            HFTRiskLevel.CRITICAL: 5.0
        }

        category_multipliers = {
            HFTRiskCategory.RACE_CONDITION: 1.5,
            HFTRiskCategory.LATENCY: 1.3,
            HFTRiskCategory.OVERFLOW: 1.4,
            HFTRiskCategory.DETERMINISM: 1.2,
            HFTRiskCategory.DATA_INTEGRITY: 1.3,
            HFTRiskCategory.REGULATORY: 1.0
        }

        base_impact = base_impacts.get(pattern.risk_level, 1.0)
        category_mult = category_multipliers.get(pattern.category, 1.0)

        return base_impact * category_mult

    def generate_hft_optimization_tiers(
        self,
        code_content: str,
        analysis_results: Dict[str, Any]
    ) -> List[OptimizationTier]:
        """Generate HFT-specific optimization tiers."""
        tiers = []

        # Tier 1: Immediate Safety Fixes
        if analysis_results["risk_issues"]:
            critical_issues = [issue for issue in analysis_results["risk_issues"] if issue.severity == "critical"]
            if critical_issues:
                tiers.append(OptimizationTier(
                    tier_number=1,
                    name="Critical Safety Fixes",
                    description="Fix critical race conditions and overflow risks",
                    estimated_speedup=1.0,  # Safety first, not performance
                    difficulty="medium",
                    safety_impact="high",
                    code_before="// Code with race conditions and overflow risks",
                    code_after="// Code with atomic operations and safe arithmetic",
                    explanation="🏦 In HFT, correctness trumps raw speed. Fix critical safety issues before optimizing for performance."
                ))

        # Tier 2: Lock-Free Data Structures
        if any("queue" in code_content.lower() or "lock" in code_content.lower()):
            lock_free_opt = next((opt for opt in self.optimization_patterns if "Lock-Free" in opt["name"]), None)
            if lock_free_opt:
                tiers.append(OptimizationTier(
                    tier_number=2,
                    name=lock_free_opt["name"],
                    description=lock_free_opt["description"],
                    estimated_speedup=lock_free_opt["estimated_speedup"],
                    difficulty="hard",
                    safety_impact="medium",
                    code_before=lock_free_opt["code_before"],
                    code_after=lock_free_opt["code_after"],
                    explanation=lock_free_opt["explanation"]
                ))

        # Tier 3: Memory Layout Optimization
        if re.search(r'struct|class', code_content):
            numa_opt = next((opt for opt in self.optimization_patterns if "NUMA" in opt["name"]), None)
            if numa_opt:
                tiers.append(OptimizationTier(
                    tier_number=3,
                    name=numa_opt["name"],
                    description=numa_opt["description"],
                    estimated_speedup=numa_opt["estimated_speedup"],
                    difficulty="hard",
                    safety_impact="low",
                    code_before=numa_opt["code_before"],
                    code_after=numa_opt["code_after"],
                    explanation=numa_opt["explanation"]
                ))

        # Tier 4: Branch Prediction
        if re.search(r'if\s*\(', code_content):
            branch_opt = next((opt for opt in self.optimization_patterns if "Branch" in opt["name"]), None)
            if branch_opt:
                tiers.append(OptimizationTier(
                    tier_number=4,
                    name=branch_opt["name"],
                    description=branch_opt["description"],
                    estimated_speedup=branch_opt["estimated_speedup"],
                    difficulty="easy",
                    safety_impact="none",
                    code_before=branch_opt["code_before"],
                    code_after=branch_opt["code_after"],
                    explanation=branch_opt["explanation"]
                ))

        # Tier 5: Custom Memory Allocator
        if "new" in code_content or "malloc" in code_content:
            tiers.append(OptimizationTier(
                tier_number=5,
                name="Custom Memory Pool",
                description="Implement pre-allocated memory pools for predictable allocation",
                estimated_speedup=3.0,
                difficulty="hard",
                safety_impact="medium",
                code_before="Order* order = new Order();  // Unpredictable latency",
                code_after="""
class MemoryPool {
    std::array<Order, 10000> pool;
    std::atomic<size_t> next_free{0};
public:
    Order* allocate() {
        size_t idx = next_free.fetch_add(1) % pool.size();
        return &pool[idx];
    }
};
Order* order = memory_pool.allocate();  // O(1) allocation""",
                explanation="Custom memory pools eliminate allocation latency and provide deterministic performance critical for HFT systems."
            ))

        return tiers

    def generate_hft_recommendations(
        self,
        analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Generate HFT-specific recommendations."""
        recommendations = []

        # Safety recommendations
        if analysis_results["safety_score"] < 8:
            recommendations.extend([
                "🏦 Priority 1: Address safety issues before performance optimization",
                "Use SafeInt library for all financial arithmetic operations",
                "Implement comprehensive unit tests with edge cases and stress testing"
            ])

        # Latency recommendations
        if analysis_results["latency_score"] < 8:
            recommendations.extend([
                "⚡ Use lock-free algorithms to eliminate blocking operations",
                "Pre-allocate all memory and avoid dynamic allocation in hot paths",
                "Consider NUMA topology and CPU affinity for trading threads"
            ])

        # Reliability recommendations
        if analysis_results["reliability_score"] < 8:
            recommendations.extend([
                "🛡️ Use atomic operations for all shared variable updates",
                "Implement proper error handling and recovery mechanisms",
                "Add comprehensive logging for audit trail compliance"
            ])

        # General HFT recommendations
        recommendations.extend([
            "📊 Profile your code under realistic market conditions",
            "🔍 Use hardware performance counters to measure cache misses and branch mispredictions",
            "⏰ Implement high-resolution timing for latency measurement",
            "🧪 Test with synthetic market data loads to validate performance",
            "📋 Document all optimization decisions for regulatory compliance"
        ])

        return recommendations

    def generate_hft_report(
        self,
        code_content: str,
        audit_level: str = "comprehensive"
    ) -> str:
        """Generate a comprehensive HFT analysis report."""
        analysis = self.analyze_hft_code(code_content, audit_level)

        report_lines = [
            "🏦 HFT CODE ANALYSIS REPORT",
            "=" * 50,
            "",
            f"Safety Score: {analysis['safety_score']}/10",
            f"Latency Score: {analysis['latency_score']}/10",
            f"Reliability Score: {analysis['reliability_score']}/10",
            "",
            f"Risk Issues Found: {len(analysis['risk_issues'])}",
            f"Optimization Opportunities: {len(analysis['optimization_opportunities'])}",
            f"Regulatory Concerns: {len(analysis['regulatory_concerns'])}",
            "",
        ]

        # Add critical issues
        critical_issues = [issue for issue in analysis['risk_issues'] if issue.severity == 'critical']
        if critical_issues:
            report_lines.extend([
                "🚨 CRITICAL ISSUES:",
                "-" * 20
            ])
            for issue in critical_issues:
                report_lines.append(f"Line {issue.line_number}: {issue.description}")
                report_lines.append(f"  → {issue.suggestion}")
            report_lines.append("")

        # Add recommendations
        recommendations = self.generate_hft_recommendations(analysis)
        if recommendations:
            report_lines.extend([
                "💡 RECOMMENDATIONS:",
                "-" * 20
            ])
            for rec in recommendations:
                report_lines.append(f"  • {rec}")

        return "\n".join(report_lines)


def create_hft_engine() -> HFTSpecializationEngine:
    """Create an HFT specialization engine."""
    return HFTSpecializationEngine()


# Example usage
def analyze_hft_example():
    """Example HFT code analysis."""
    hft_engine = create_hft_engine()

    sample_hft_code = '''
#include <queue>
#include <mutex>

struct Order {
    double price;
    int quantity;
    uint64_t timestamp;
};

std::queue<Order> order_queue;
std::mutex queue_mutex;
double current_price = 100.50;

void process_order(const Order& order) {
    if (order.price == current_price) {  // Dangerous equality
        current_price = order.price;  // Race condition
        order_queue.push(order);     // Blocking operation
    }
}

void update_price(double new_price) {
    current_price += new_price * 0.01;  // Potential overflow
}
'''

    return hft_engine.generate_hft_report(sample_hft_code)
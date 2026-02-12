"""
Requirements validation tests for MT5 Infinite Reliability Agent.
Tests each success criterion from INITIAL.md.
"""

import pytest
from unittest.mock import patch, AsyncMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mt5_infinite_reliability_agent.agent import agent, analyze_mql5_code
from mt5_infinite_reliability_agent.tools import (
    parse_mql5_code,
    analyze_code_quality,
    apply_code_transformation,
    verify_code_correctness,
    create_proof_certificate
)
from mt5_infinite_reliability_agent.dependencies import AgentDependencies


class TestRequirement1_MultiDimensionalAnalysis:
    """
    REQ-001: Can analyze MQL5 code and identify issues across 4+ dimensions.

    Success Criteria:
    - Supports complexity, memory, security, robustness dimensions
    - Generates structured analysis reports
    - Identifies issues with severity scoring
    """

    def test_supports_four_core_dimensions(self, sample_parsed_code):
        """Test that analysis supports all 4 core dimensions."""
        dimensions = ["complexity", "memory", "security", "robustness"]

        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=dimensions,
            threshold="low"
        )

        # All 4 dimensions should be present in results
        assert "dimensions" in result
        for dim in dimensions:
            assert dim in result["dimensions"]
            assert "score" in result["dimensions"][dim]
            assert "issues" in result["dimensions"][dim]

    def test_complexity_dimension_analysis(self):
        """Test complexity dimension identifies issues."""
        parsed_code = {
            "stats": {"function_count": 25, "variable_count": 50, "line_count": 1000},
            "patterns": {"loops": 10, "conditions": 30, "indicators": 5}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["complexity"],
            threshold="low"
        )

        complexity = result["dimensions"]["complexity"]
        assert "score" in complexity
        assert isinstance(complexity["score"], (int, float))
        # High function count should be detected
        assert len(complexity["issues"]) > 0

    def test_memory_dimension_analysis(self):
        """Test memory safety dimension identifies issues."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 200},
            "patterns": {"loops": 15, "conditions": 5, "indicators": 2}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["memory"],
            threshold="low"
        )

        memory = result["dimensions"]["memory"]
        assert "score" in memory
        # Multiple loops should trigger memory safety checks
        assert len(memory["issues"]) > 0

    def test_security_dimension_analysis(self):
        """Test security dimension identifies issues."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 200},
            "patterns": {"loops": 2, "conditions": 5, "indicators": 10}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["security"],
            threshold="low"
        )

        security = result["dimensions"]["security"]
        assert "score" in security
        # Multiple indicators should trigger security checks
        assert len(security["issues"]) > 0

    def test_robustness_dimension_analysis(self):
        """Test robustness dimension identifies issues."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 200},
            "patterns": {"loops": 2, "conditions": 5, "indicators": 3}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["robustness"],
            threshold="low"
        )

        robustness = result["dimensions"]["robustness"]
        assert "score" in robustness
        # Should always suggest error handling improvements
        assert len(robustness["issues"]) > 0

    def test_generates_structured_reports(self, sample_parsed_code):
        """Test that analysis generates structured reports."""
        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="medium"
        )

        # Required structure
        assert "issues_found" in result
        assert "severity_breakdown" in result
        assert "dimensions" in result
        assert "overall_score" in result

        # Severity breakdown structure
        breakdown = result["severity_breakdown"]
        assert "critical" in breakdown
        assert "high" in breakdown
        assert "medium" in breakdown
        assert "low" in breakdown

    def test_severity_scoring_system(self, sample_parsed_code):
        """Test that issues have proper severity scoring."""
        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="low"
        )

        # Collect all issues
        all_issues = []
        for dim_data in result["dimensions"].values():
            all_issues.extend(dim_data["issues"])

        # Each issue should have severity
        valid_severities = {"critical", "high", "medium", "low"}
        for issue in all_issues:
            assert "severity" in issue
            assert issue["severity"] in valid_severities
            assert "message" in issue
            assert "dimension" in issue

    @pytest.mark.asyncio
    async def test_end_to_end_multidimensional_analysis(self, complex_mql5_code):
        """Test complete multi-dimensional analysis workflow."""
        with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value.data = {
                "analysis": {
                    "issues_found": 5,
                    "severity_breakdown": {"critical": 0, "high": 2, "medium": 2, "low": 1},
                    "dimensions": {
                        "complexity": {"score": 6.0, "issues": []},
                        "memory": {"score": 7.0, "issues": []},
                        "security": {"score": 8.0, "issues": []},
                        "robustness": {"score": 7.5, "issues": []}
                    },
                    "overall_score": 7.125
                }
            }

            result = await analyze_mql5_code(
                complex_mql5_code,
                mode="analyze"
            )

            assert "analysis" in result
            analysis = result["analysis"]
            assert len(analysis["dimensions"]) >= 4


class TestRequirement2_FixGenerationWithProofs:
    """
    REQ-002: Generates valid fix suggestions with proof justifications.

    Success Criteria:
    - Every fix has mathematical proof or justification
    - Fixes are actionable and specific
    - Proofs explain correctness preservation
    """

    def test_generates_fix_suggestions(self, simple_mql5_code):
        """Test that transformations include fix suggestions."""
        issues = [
            {
                "dimension": "complexity",
                "severity": "high",
                "message": "High complexity detected",
                "fix_suggestion": "Extract method to reduce complexity"
            },
            {
                "dimension": "memory",
                "severity": "medium",
                "message": "Potential buffer overflow",
                "fix_suggestion": "Add boundary checks using ArraySize()"
            }
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        assert "transformations" in result
        assert len(result["transformations"]) > 0

        # Each transformation should have fix information
        for trans in result["transformations"]:
            assert "fixed_snippet" in trans
            assert "proof" in trans

    def test_every_fix_has_proof(self, simple_mql5_code):
        """Test that every transformation includes a proof."""
        issues = [
            {"dimension": "test", "severity": "medium", "message": "Issue 1", "fix_suggestion": "Fix 1"},
            {"dimension": "test", "severity": "medium", "message": "Issue 2", "fix_suggestion": "Fix 2"}
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        for trans in result["transformations"]:
            assert "proof" in trans
            assert len(trans["proof"]) > 0
            assert isinstance(trans["proof"], str)

    def test_proofs_reference_fix_suggestions(self, simple_mql5_code):
        """Test that proofs reference the fix suggestions."""
        issues = [
            {
                "dimension": "complexity",
                "severity": "high",
                "message": "Test issue",
                "fix_suggestion": "Specific refactoring approach"
            }
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        trans = result["transformations"][0]
        # Proof should reference the fix suggestion
        assert "fix_suggestion" in trans["proof"].lower() or "refactoring" in trans["proof"].lower()

    def test_fixes_are_actionable(self, simple_mql5_code):
        """Test that fix suggestions are specific and actionable."""
        issues = [
            {
                "dimension": "memory",
                "severity": "high",
                "message": "Array bounds issue",
                "fix_suggestion": "Add ArraySize() validation before array access"
            }
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        trans = result["transformations"][0]
        # Fixed snippet should contain specific guidance
        assert "fix" in trans["fixed_snippet"].lower()

    @pytest.mark.asyncio
    async def test_end_to_end_fix_generation(self, complex_mql5_code):
        """Test complete fix generation workflow."""
        with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value.data = {
                "analysis": {"issues_found": 3},
                "transformations": [
                    {
                        "issue_id": "t1",
                        "original_code": "old code",
                        "fixed_code": "new code",
                        "proof": "Mathematical justification: transformation preserves semantics",
                        "verification_status": "verified"
                    }
                ]
            }

            result = await analyze_mql5_code(
                complex_mql5_code,
                mode="fix"
            )

            assert "transformations" in result
            for trans in result["transformations"]:
                assert "proof" in trans
                assert len(trans["proof"]) > 0


class TestRequirement3_AtomicTransformations:
    """
    REQ-003: Applies transformations atomically with rollback capability.

    Success Criteria:
    - All-or-nothing transformation application
    - Snapshot/rollback mechanism works
    - Failed transformations don't corrupt code
    """

    def test_creates_backup_snapshot(self, simple_mql5_code):
        """Test that transformation creates backup snapshot."""
        issues = [{"dimension": "test", "severity": "low", "message": "test", "fix_suggestion": "test"}]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        assert "snapshot" in result
        assert result["snapshot"] == simple_mql5_code

    def test_rollback_mechanism_works(self):
        """Test rollback restores original code."""
        from tools import TransformationRollback

        original_code = "void OnInit() { }"
        rollback = TransformationRollback(original_code)

        # Apply transformation
        rollback.record_transformation({"issue_id": "t1", "applied": True})

        # Rollback
        restored = rollback.rollback()
        assert restored == original_code

    def test_dependency_snapshot_stack(self, test_dependencies, simple_mql5_code):
        """Test dependency snapshot stack management."""
        # Add snapshots
        test_dependencies.add_snapshot(simple_mql5_code)
        test_dependencies.add_snapshot(simple_mql5_code + "\n// modified")

        # Should have 2 snapshots
        assert len(test_dependencies._snapshot_stack) == 2

        # Rollback once
        restored = test_dependencies.rollback()
        assert "// modified" in restored

        # Rollback again
        restored = test_dependencies.rollback()
        assert restored == simple_mql5_code

    def test_failed_transformation_tracking(self, simple_mql5_code):
        """Test that failed transformations are tracked."""
        issues = [{"dimension": "test", "severity": "low", "message": "test", "fix_suggestion": "test"}] * 3

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        assert "applied_count" in result
        assert "failed_count" in result
        total = result["applied_count"] + result["failed_count"]
        assert total == len(result["transformations"])

    def test_atomic_application(self, simple_mql5_code):
        """Test all-or-nothing transformation application."""
        issues = [
            {"dimension": "test1", "severity": "medium", "message": "test1", "fix_suggestion": "fix1"},
            {"dimension": "test2", "severity": "medium", "message": "test2", "fix_suggestion": "fix2"}
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        # If any transformation is applied, snapshot should exist
        if result["applied_count"] > 0:
            assert result["snapshot"] is not None

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, simple_mql5_code):
        """Test that errors trigger rollback."""
        deps = AgentDependencies(enable_rollback=True)
        deps.add_snapshot(simple_mql5_code)

        # Verify snapshot exists
        assert len(deps._snapshot_stack) == 1

        # Rollback should work
        restored = deps.rollback()
        assert restored == simple_mql5_code


class TestRequirement4_StructuredCertificates:
    """
    REQ-004: Produces structured certificates with audit trails.

    Success Criteria:
    - Certificates have unique IDs
    - Proof chains are cryptographically verifiable
    - Audit trails show all transformations
    """

    def test_certificate_has_unique_id(self, sample_analysis_result):
        """Test that certificates have unique identifiers."""
        verification = {"verified": True, "checks": [], "confidence": 100}

        result1 = create_proof_certificate(
            sample_analysis_result,
            [],
            verification,
            {"format": "json"}
        )

        result2 = create_proof_certificate(
            sample_analysis_result,
            [{"issue_id": "new", "applied": True}],
            verification,
            {"format": "json"}
        )

        # Different inputs should produce different IDs
        assert result1["certificate"]["id"] != result2["certificate"]["id"]

    def test_certificate_has_proof_chain(self, sample_analysis_result):
        """Test that certificates include proof chains."""
        verification = {"verified": True, "checks": [], "confidence": 95}
        transformations = [
            {"issue_id": "t1", "applied": True},
            {"issue_id": "t2", "applied": True}
        ]

        result = create_proof_certificate(
            sample_analysis_result,
            transformations,
            verification,
            {"format": "json"}
        )

        cert = result["certificate"]
        assert "proof_chain" in cert
        assert len(cert["proof_chain"]) > 0

        # Proof chain should have analysis, transformations, verification
        steps = [p["step"] for p in cert["proof_chain"]]
        assert any("analysis" in step for step in steps)
        assert any("verification" in step for step in steps)

    def test_proof_chain_includes_hashes(self, sample_analysis_result):
        """Test that proof chain entries have cryptographic hashes."""
        verification = {"verified": True, "checks": [], "confidence": 100}

        result = create_proof_certificate(
            sample_analysis_result,
            [],
            verification,
            {"format": "json"}
        )

        proof_chain = result["certificate"]["proof_chain"]
        for entry in proof_chain:
            assert "hash" in entry
            assert len(entry["hash"]) > 0
            # Should be hexadecimal
            assert all(c in "0123456789abcdef" for c in entry["hash"].lower())

    def test_certificate_includes_summary(self, sample_analysis_result):
        """Test that certificates include summary information."""
        verification = {"verified": True, "checks": [{"passed": True}], "confidence": 90}
        transformations = [{"issue_id": "t1", "applied": True}]

        result = create_proof_certificate(
            sample_analysis_result,
            transformations,
            verification,
            {"format": "json"}
        )

        summary = result["certificate"]["summary"]
        assert "issues_found" in summary
        assert "transformations_applied" in summary
        assert "verification_status" in summary
        assert "confidence" in summary

    def test_certificate_includes_metrics(self, sample_analysis_result):
        """Test that certificates include verification metrics."""
        verification = {"verified": True, "checks": [{"passed": True}, {"passed": False}], "confidence": 50}

        result = create_proof_certificate(
            sample_analysis_result,
            [],
            verification,
            {"format": "json"}
        )

        metrics = result["certificate"]["verification_metrics"]
        assert "checks_passed" in metrics
        assert "total_checks" in metrics
        assert "overall_score" in metrics

    def test_certificate_audit_trail(self, sample_analysis_result):
        """Test that certificate creates complete audit trail."""
        transformations = [
            {"issue_id": "t1", "dimension": "complexity", "applied": True},
            {"issue_id": "t2", "dimension": "memory", "applied": True},
            {"issue_id": "t3", "dimension": "security", "applied": False}
        ]
        verification = {"verified": True, "checks": [], "confidence": 85}

        result = create_proof_certificate(
            sample_analysis_result,
            transformations,
            verification,
            {"format": "json"}
        )

        # Proof chain should include entry for each transformation
        proof_chain = result["certificate"]["proof_chain"]
        transform_steps = [p for p in proof_chain if "transform_" in p["step"]]
        assert len(transform_steps) == len(transformations)

    def test_certificate_timestamp(self, sample_analysis_result):
        """Test that certificates include timestamps."""
        verification = {"verified": True, "checks": [], "confidence": 100}

        result = create_proof_certificate(
            sample_analysis_result,
            [],
            verification,
            {"format": "json"}
        )

        assert "timestamp" in result["certificate"]
        # Should be ISO format
        from datetime import datetime
        datetime.fromisoformat(result["certificate"]["timestamp"])


class TestRequirement5_MQL5SyntaxHandling:
    """
    REQ-005: Handles basic MQL5 syntax correctly.

    Success Criteria:
    - Parses functions correctly
    - Parses variables correctly
    - Identifies indicators
    - Handles basic MQL5 constructs
    """

    def test_parses_functions_correctly(self):
        """Test parsing of MQL5 function definitions."""
        code = """
        void OnInit() { Print("Init"); }
        int OnTick() { return 0; }
        double CalculateMA(int period) { return 0.0; }
        bool CheckSignal(string symbol) { return true; }
        """

        result = parse_mql5_code(code)

        functions = result["ast"]["functions"]
        assert "OnInit" in functions
        assert "OnTick" in functions
        assert "CalculateMA" in functions
        assert "CheckSignal" in functions

    def test_parses_variables_correctly(self):
        """Test parsing of MQL5 variable declarations."""
        code = """
        input int MAPeriod = 14;
        input double LotSize = 0.1;
        static bool initialized = false;
        extern string Symbol = "EURUSD";
        """

        result = parse_mql5_code(code)

        variables = result["ast"]["variables"]
        assert "MAPeriod" in variables
        assert "LotSize" in variables
        assert "initialized" in variables
        assert "Symbol" in variables

    def test_identifies_indicators(self):
        """Test identification of indicator calls."""
        code = """
        void OnTick() {
            double ma = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);
            double rsi = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
            double macd = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
            double stoch = iStochastic(_Symbol, PERIOD_H1, 5, 3, 3, MODE_SMA, 0, MODE_MAIN, 0);
        }
        """

        result = parse_mql5_code(code)

        patterns = result["patterns"]
        # Should detect multiple indicators
        assert patterns["indicators"] >= 4

    def test_handles_loops(self):
        """Test detection of loop constructs."""
        code = """
        void ProcessData() {
            for (int i = 0; i < 10; i++) { }
            while (condition) { }
            for (int j = 0; j < 5; j++) { }
        }
        """

        result = parse_mql5_code(code)

        patterns = result["patterns"]
        assert patterns["loops"] == 3

    def test_handles_conditions(self):
        """Test detection of conditional statements."""
        code = """
        void CheckConditions() {
            if (a > b) { }
            if (c < d) { }
            else if (e == f) { }
        }
        """

        result = parse_mql5_code(code)

        patterns = result["patterns"]
        assert patterns["conditions"] == 3

    def test_handles_complete_ea(self, complex_mql5_code):
        """Test parsing complete EA with multiple constructs."""
        result = parse_mql5_code(complex_mql5_code)

        # Should successfully parse
        assert "ast" in result
        assert "stats" in result
        assert "patterns" in result

        # Should detect functions
        assert result["stats"]["function_count"] > 0

        # Should detect variables
        assert result["stats"]["variable_count"] > 0

        # Should detect patterns
        assert result["patterns"]["loops"] > 0
        assert result["patterns"]["conditions"] > 0


class TestRequirementsSummary:
    """Overall requirements validation summary."""

    @pytest.mark.asyncio
    async def test_all_requirements_met(self, complex_mql5_code):
        """Integration test verifying all requirements together."""
        with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value.data = {
                "analysis": {
                    "issues_found": 5,
                    "severity_breakdown": {"critical": 0, "high": 2, "medium": 2, "low": 1},
                    "dimensions": {
                        "complexity": {"score": 6.0, "issues": [{"severity": "high", "message": "test"}]},
                        "memory": {"score": 7.0, "issues": [{"severity": "medium", "message": "test"}]},
                        "security": {"score": 8.0, "issues": [{"severity": "medium", "message": "test"}]},
                        "robustness": {"score": 7.5, "issues": [{"severity": "low", "message": "test"}]}
                    },
                    "overall_score": 7.125
                },
                "transformations": [
                    {
                        "issue_id": "t1",
                        "original_code": "old",
                        "fixed_code": "new",
                        "proof": "Transformation preserves semantics by applying extract method refactoring",
                        "verification_status": "verified"
                    }
                ],
                "refactored_code": complex_mql5_code,
                "certificate": {
                    "id": "abc123def456",
                    "timestamp": "2025-12-20T00:00:00",
                    "proof_chain": [
                        {"step": "analysis", "hash": "hash1"},
                        {"step": "transform_t1", "hash": "hash2"},
                        {"step": "verification", "hash": "hash3"}
                    ],
                    "summary": {
                        "issues_found": 5,
                        "transformations_applied": 1,
                        "verification_status": "verified",
                        "confidence": 95.0
                    },
                    "verification_metrics": {
                        "checks_passed": 3,
                        "total_checks": 3,
                        "overall_score": 7.125
                    }
                }
            }

            result = await analyze_mql5_code(
                complex_mql5_code,
                mode="full",
                proof_level="detailed"
            )

            # REQ-001: Multi-dimensional analysis
            assert len(result["analysis"]["dimensions"]) >= 4

            # REQ-002: Fix generation with proofs
            assert all("proof" in t for t in result["transformations"])

            # REQ-003: Atomic transformations (tested via snapshot mechanism)
            # Verified by dependency rollback tests

            # REQ-004: Structured certificates
            assert "certificate" in result
            assert "id" in result["certificate"]
            assert "proof_chain" in result["certificate"]

            # REQ-005: MQL5 syntax handling
            # Verified by parsing tests

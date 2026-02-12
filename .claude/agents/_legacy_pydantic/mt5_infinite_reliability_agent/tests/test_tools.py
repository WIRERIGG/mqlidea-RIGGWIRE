"""
Tool validation tests for MT5 Infinite Reliability Agent.
Tests each tool function independently.
"""

import pytest
import hashlib
import json
from datetime import datetime

# Import tool functions
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mt5_infinite_reliability_agent.tools import (
    parse_mql5_code,
    analyze_code_quality,
    apply_code_transformation,
    verify_code_correctness,
    create_proof_certificate,
    TransformationRollback
)


class TestParseMQL5:
    """Test MQL5 code parsing functionality."""

    def test_parse_simple_code(self, simple_mql5_code):
        """Test parsing simple MQL5 code."""
        result = parse_mql5_code(simple_mql5_code)

        assert "ast" in result
        assert "stats" in result
        assert "patterns" in result
        assert "hash" in result

        # Check AST structure
        assert "functions" in result["ast"]
        assert "variables" in result["ast"]
        assert "OnInit" in result["ast"]["functions"]
        assert "OnTick" in result["ast"]["functions"]

    def test_parse_complex_code(self, complex_mql5_code):
        """Test parsing complex MQL5 code with multiple patterns."""
        result = parse_mql5_code(complex_mql5_code)

        # Check statistics
        assert result["stats"]["function_count"] == 2
        assert result["stats"]["line_count"] > 30

        # Check patterns detected
        assert result["patterns"]["loops"] >= 1
        assert result["patterns"]["conditions"] >= 3
        assert result["patterns"]["indicators"] >= 3

    def test_parse_extracts_functions(self):
        """Test function extraction."""
        code = """
        void OnInit() { }
        void OnDeinit() { }
        int OnTick() { return 0; }
        double CalculateMA(int period) { return 0.0; }
        """
        result = parse_mql5_code(code)

        functions = result["ast"]["functions"]
        assert "OnInit" in functions
        assert "OnDeinit" in functions
        assert "OnTick" in functions
        assert "CalculateMA" in functions

    def test_parse_extracts_variables(self):
        """Test variable extraction."""
        code = """
        input int MAPeriod = 14;
        input double LotSize = 0.1;
        static int counter;
        extern bool UseStopLoss;
        """
        result = parse_mql5_code(code)

        variables = result["ast"]["variables"]
        assert "MAPeriod" in variables
        assert "LotSize" in variables
        assert "counter" in variables
        assert "UseStopLoss" in variables

    def test_parse_generates_hash(self, simple_mql5_code):
        """Test code hash generation."""
        result1 = parse_mql5_code(simple_mql5_code)
        result2 = parse_mql5_code(simple_mql5_code)

        # Same code should produce same hash
        assert result1["hash"] == result2["hash"]

        # Different code should produce different hash
        result3 = parse_mql5_code(simple_mql5_code + "\n// comment")
        assert result1["hash"] != result3["hash"]


class TestAnalyzeCodeQuality:
    """Test code quality analysis functionality."""

    def test_analyze_all_dimensions(self, sample_parsed_code):
        """Test analysis across all 4 dimensions."""
        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="low"
        )

        assert "dimensions" in result
        assert "complexity" in result["dimensions"]
        assert "memory" in result["dimensions"]
        assert "security" in result["dimensions"]
        assert "robustness" in result["dimensions"]

        # Each dimension should have score and issues
        for dim_name, dim_data in result["dimensions"].items():
            assert "score" in dim_data
            assert "issues" in dim_data
            assert isinstance(dim_data["score"], (int, float))
            assert isinstance(dim_data["issues"], list)

    def test_analyze_complexity_dimension(self):
        """Test complexity analysis specifically."""
        parsed_code = {
            "stats": {"function_count": 25, "variable_count": 10, "line_count": 500},
            "patterns": {"loops": 5, "conditions": 15, "indicators": 2}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["complexity"],
            threshold="medium"
        )

        # Should detect high function count
        complexity_issues = result["dimensions"]["complexity"]["issues"]
        assert any("function count" in issue["message"].lower() for issue in complexity_issues)

    def test_analyze_memory_dimension(self):
        """Test memory safety analysis."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 100},
            "patterns": {"loops": 15, "conditions": 5, "indicators": 2}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["memory"],
            threshold="low"
        )

        # Should detect multiple loops (potential memory issues)
        memory_issues = result["dimensions"]["memory"]["issues"]
        assert len(memory_issues) > 0

    def test_analyze_security_dimension(self):
        """Test security analysis."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 100},
            "patterns": {"loops": 2, "conditions": 5, "indicators": 8}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["security"],
            threshold="low"
        )

        # Should detect multiple indicators (input validation concerns)
        security_issues = result["dimensions"]["security"]["issues"]
        assert len(security_issues) > 0

    def test_analyze_robustness_dimension(self):
        """Test robustness analysis."""
        parsed_code = {
            "stats": {"function_count": 5, "variable_count": 10, "line_count": 100},
            "patterns": {"loops": 2, "conditions": 5, "indicators": 3}
        }

        result = analyze_code_quality(
            parsed_code,
            dimensions=["robustness"],
            threshold="low"
        )

        # Should always suggest error handling
        robustness_issues = result["dimensions"]["robustness"]["issues"]
        assert len(robustness_issues) > 0

    def test_severity_threshold_filtering(self, sample_parsed_code):
        """Test that severity threshold filters issues correctly."""
        # Get all issues with low threshold
        result_low = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="low"
        )

        # Get filtered issues with high threshold
        result_high = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="high"
        )

        # High threshold should return fewer or equal issues
        assert result_high["issues_found"] <= result_low["issues_found"]

    def test_overall_score_calculation(self, sample_parsed_code):
        """Test overall score calculation."""
        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory"],
            threshold="low"
        )

        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 10

    def test_severity_breakdown(self, sample_parsed_code):
        """Test severity breakdown structure."""
        result = analyze_code_quality(
            sample_parsed_code,
            dimensions=["complexity", "memory", "security", "robustness"],
            threshold="low"
        )

        assert "severity_breakdown" in result
        breakdown = result["severity_breakdown"]
        assert "critical" in breakdown
        assert "high" in breakdown
        assert "medium" in breakdown
        assert "low" in breakdown

        # All counts should be non-negative integers
        for severity, count in breakdown.items():
            assert isinstance(count, int)
            assert count >= 0


class TestCodeTransformation:
    """Test code transformation functionality."""

    def test_transform_with_issues(self, simple_mql5_code):
        """Test applying transformations with issues."""
        issues = [
            {
                "dimension": "complexity",
                "severity": "medium",
                "message": "Test issue",
                "fix_suggestion": "Test fix"
            }
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"auto_format": True, "create_backup": True}
        )

        assert "success" in result
        assert "transformations" in result
        assert "fixed_code" in result
        assert "snapshot" in result
        assert len(result["transformations"]) > 0

    def test_transform_creates_backup(self, simple_mql5_code):
        """Test that transformation creates backup snapshot."""
        issues = [{"dimension": "test", "severity": "low", "message": "test", "fix_suggestion": "test"}]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": True}
        )

        assert result["snapshot"] == simple_mql5_code

    def test_transform_without_backup(self, simple_mql5_code):
        """Test transformation without backup."""
        issues = [{"dimension": "test", "severity": "low", "message": "test", "fix_suggestion": "test"}]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"create_backup": False}
        )

        assert result["snapshot"] is None

    def test_transform_limits_issues(self, simple_mql5_code):
        """Test that transformation limits number of issues processed."""
        # Create 20 issues
        issues = [
            {
                "dimension": f"test_{i}",
                "severity": "low",
                "message": f"Issue {i}",
                "fix_suggestion": f"Fix {i}"
            }
            for i in range(20)
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"auto_format": True}
        )

        # Should only process top 10
        assert len(result["transformations"]) <= 10

    def test_transform_tracks_applied_count(self, simple_mql5_code):
        """Test applied and failed transformation counts."""
        issues = [
            {"dimension": "test", "severity": "medium", "message": "test1", "fix_suggestion": "fix1"},
            {"dimension": "test", "severity": "medium", "message": "test2", "fix_suggestion": "fix2"}
        ]

        result = apply_code_transformation(
            simple_mql5_code,
            issues,
            {"auto_format": True}
        )

        assert "applied_count" in result
        assert "failed_count" in result
        assert result["applied_count"] + result["failed_count"] == len(result["transformations"])


class TestVerifyCodeCorrectness:
    """Test code verification functionality."""

    def test_verify_simple_transformation(self, simple_mql5_code):
        """Test verification of simple transformation."""
        transformations = [
            {"issue_id": "test1", "applied": True}
        ]

        result = verify_code_correctness(
            simple_mql5_code,
            simple_mql5_code + "\n// Comment",
            transformations
        )

        assert "verified" in result
        assert "checks" in result
        assert "confidence" in result
        assert isinstance(result["verified"], bool)
        assert len(result["checks"]) > 0

    def test_verify_syntax_preservation(self, simple_mql5_code):
        """Test syntax preservation check."""
        result = verify_code_correctness(
            simple_mql5_code,
            simple_mql5_code,
            []
        )

        # Find syntax preservation check
        syntax_check = next(
            (c for c in result["checks"] if c["name"] == "syntax_preservation"),
            None
        )
        assert syntax_check is not None
        assert syntax_check["passed"]

    def test_verify_function_signatures(self):
        """Test function signature preservation."""
        original = "void OnInit() { } void OnTick() { }"
        transformed = "void OnInit() { int x = 0; } void OnTick() { }"

        result = verify_code_correctness(original, transformed, [])

        func_check = next(
            (c for c in result["checks"] if c["name"] == "function_signature_preservation"),
            None
        )
        assert func_check is not None
        assert func_check["passed"]

    def test_verify_detects_removed_functions(self):
        """Test detection of removed functions."""
        original = "void OnInit() { } void OnTick() { }"
        transformed = "void OnInit() { }"

        result = verify_code_correctness(original, transformed, [])

        func_check = next(
            (c for c in result["checks"] if c["name"] == "function_signature_preservation"),
            None
        )
        assert func_check is not None
        assert not func_check["passed"]

    def test_verify_transformation_application(self):
        """Test transformation application verification."""
        transformations = [
            {"applied": True},
            {"applied": True}
        ]

        result = verify_code_correctness("code", "code", transformations)

        trans_check = next(
            (c for c in result["checks"] if c["name"] == "transformation_application"),
            None
        )
        assert trans_check is not None
        assert trans_check["passed"]

    def test_verify_confidence_calculation(self, simple_mql5_code):
        """Test confidence score calculation."""
        result = verify_code_correctness(
            simple_mql5_code,
            simple_mql5_code,
            [{"applied": True}]
        )

        assert 0 <= result["confidence"] <= 100

    def test_verify_includes_timestamp(self, simple_mql5_code):
        """Test that verification includes timestamp."""
        result = verify_code_correctness(
            simple_mql5_code,
            simple_mql5_code,
            []
        )

        assert "timestamp" in result
        # Should be valid ISO format
        datetime.fromisoformat(result["timestamp"])


class TestProofCertificate:
    """Test proof certificate generation."""

    def test_generate_basic_certificate(self, sample_analysis_result):
        """Test basic certificate generation."""
        transformations = [
            {"issue_id": "test1", "applied": True}
        ]
        verification = {
            "verified": True,
            "checks": [{"passed": True}],
            "confidence": 95.0
        }

        result = create_proof_certificate(
            sample_analysis_result,
            transformations,
            verification,
            {"format": "json"}
        )

        assert "certificate" in result
        cert = result["certificate"]
        assert "id" in cert
        assert "timestamp" in cert
        assert "proof_chain" in cert
        assert "summary" in cert

    def test_certificate_has_valid_structure(self, sample_analysis_result):
        """Test certificate structure completeness."""
        result = create_proof_certificate(
            sample_analysis_result,
            [],
            {"verified": True, "checks": [], "confidence": 100},
            {"format": "json"}
        )

        cert = result["certificate"]
        assert "version" in cert
        assert "verification_metrics" in cert
        assert cert["version"] == "1.0"

    def test_certificate_proof_chain(self, sample_analysis_result):
        """Test proof chain generation."""
        transformations = [
            {"issue_id": "test1", "applied": True},
            {"issue_id": "test2", "applied": True}
        ]
        verification = {"verified": True, "checks": [], "confidence": 90}

        result = create_proof_certificate(
            sample_analysis_result,
            transformations,
            verification,
            {"format": "json"}
        )

        proof_chain = result["certificate"]["proof_chain"]
        assert len(proof_chain) > 0
        # Should have analysis, transformations, and verification
        assert any(p["step"] == "analysis" for p in proof_chain)
        assert any(p["step"] == "verification" for p in proof_chain)

    def test_certificate_id_uniqueness(self, sample_analysis_result):
        """Test certificate ID uniqueness."""
        result1 = create_proof_certificate(
            sample_analysis_result,
            [],
            {"verified": True, "checks": [], "confidence": 100},
            {"format": "json"}
        )

        result2 = create_proof_certificate(
            sample_analysis_result,
            [{"issue_id": "new", "applied": True}],
            {"verified": True, "checks": [], "confidence": 100},
            {"format": "json"}
        )

        # Different inputs should produce different IDs
        assert result1["certificate"]["id"] != result2["certificate"]["id"]

    def test_certificate_json_format(self, sample_analysis_result):
        """Test JSON format output."""
        result = create_proof_certificate(
            sample_analysis_result,
            [],
            {"verified": True, "checks": [], "confidence": 100},
            {"format": "json"}
        )

        assert "formatted_output" in result
        # Should be valid JSON
        parsed = json.loads(result["formatted_output"])
        assert "id" in parsed

    def test_certificate_markdown_format(self, sample_analysis_result):
        """Test Markdown format output."""
        result = create_proof_certificate(
            sample_analysis_result,
            [],
            {"verified": True, "checks": [], "confidence": 100},
            {"format": "markdown"}
        )

        assert "formatted_output" in result
        md = result["formatted_output"]
        assert "# Code Reliability Certificate" in md
        assert "Certificate ID" in md
        assert "Proof Chain" in md

    def test_certificate_summary(self, sample_analysis_result):
        """Test certificate summary data."""
        result = create_proof_certificate(
            sample_analysis_result,
            [{"issue_id": "t1", "applied": True}],
            {"verified": True, "checks": [{"passed": True}], "confidence": 95},
            {"format": "json"}
        )

        summary = result["certificate"]["summary"]
        assert "issues_found" in summary
        assert "transformations_applied" in summary
        assert "verification_status" in summary
        assert "confidence" in summary
        assert summary["verification_status"] in ["verified", "unverified"]

    def test_certificate_verification_metrics(self, sample_analysis_result):
        """Test verification metrics in certificate."""
        verification = {
            "verified": True,
            "checks": [{"passed": True}, {"passed": True}, {"passed": False}],
            "confidence": 66.6
        }

        result = create_proof_certificate(
            sample_analysis_result,
            [],
            verification,
            {"format": "json"}
        )

        metrics = result["certificate"]["verification_metrics"]
        assert "checks_passed" in metrics
        assert "total_checks" in metrics
        assert metrics["checks_passed"] == 2
        assert metrics["total_checks"] == 3


class TestTransformationRollback:
    """Test rollback functionality."""

    def test_rollback_initialization(self, simple_mql5_code):
        """Test rollback manager initialization."""
        rollback = TransformationRollback(simple_mql5_code)
        assert rollback.snapshot == simple_mql5_code
        assert len(rollback.transformations_applied) == 0

    def test_rollback_record_transformation(self, simple_mql5_code):
        """Test recording transformations."""
        rollback = TransformationRollback(simple_mql5_code)
        trans = {"issue_id": "test1", "applied": True}
        rollback.record_transformation(trans)

        assert len(rollback.transformations_applied) == 1
        assert rollback.transformations_applied[0] == trans

    def test_rollback_restore(self, simple_mql5_code):
        """Test rollback to original code."""
        rollback = TransformationRollback(simple_mql5_code)
        rollback.record_transformation({"issue_id": "t1"})
        rollback.record_transformation({"issue_id": "t2"})

        restored = rollback.rollback()
        assert restored == simple_mql5_code
        assert len(rollback.transformations_applied) == 0

    def test_rollback_commit(self, simple_mql5_code):
        """Test committing transformations."""
        rollback = TransformationRollback(simple_mql5_code)
        rollback.record_transformation({"issue_id": "t1"})
        rollback.commit()

        assert rollback.snapshot is None

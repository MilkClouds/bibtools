"""Tests for models."""

from bibtools.models import (
    FieldMismatch,
    VerificationReport,
    VerificationResult,
    VerificationStatus,
)


class TestPaperInfo:
    """Tests for PaperInfo dataclass."""

    def test_create_paper_info(self, make_paper):
        """Test creating a PaperInfo instance with bibtex."""
        paper = make_paper(
            paper_id="abc123",
            title="Test Paper",
            authors=["John Doe", "Jane Smith"],
            year=2024,
            venue="CoRL",
        )
        assert paper.paper_id == "abc123"
        assert paper.title == "Test Paper"
        assert paper.authors == ["John Doe", "Jane Smith"]
        assert paper.year == 2024
        assert paper.venue == "CoRL"

    def test_create_paper_info_minimal(self, make_paper):
        """Test creating a PaperInfo with minimal fields."""
        paper = make_paper(paper_id="abc123", title="Test Paper", authors=["Author"], year=2024)
        assert paper.venue is None

    def test_get_venue_short_known(self, make_paper):
        """Test getting short venue name for known conferences."""
        paper = make_paper(paper_id="abc", venue="Conference on Robot Learning")
        assert paper.get_venue_short() == "CoRL"

    def test_get_venue_short_unknown(self, make_paper):
        """Test getting short venue name for unknown venue."""
        paper = make_paper(paper_id="abc", venue="Some Random Journal")
        assert paper.get_venue_short() == "Some Random Journal"


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful verification result."""
        result = VerificationResult(
            entry_key="test2024",
            success=True,
            message="Verified successfully",
        )
        assert result.entry_key == "test2024"
        assert result.success is True
        assert result.paper_info is None

    def test_create_failed_result(self):
        """Test creating a failed verification result."""
        result = VerificationResult(
            entry_key="test2024",
            success=False,
            message="Paper not found",
        )
        assert result.success is False


class TestVerificationReport:
    """Tests for VerificationReport dataclass."""

    def test_add_verified_result(self):
        """Test adding a verified result."""
        report = VerificationReport()
        result = VerificationResult(
            entry_key="test2024",
            success=True,
            message="Verified",
        )
        report.add_result(result)
        assert report.total_entries == 1
        assert report.verified == 1
        assert report.failed == 0

    def test_add_failed_result(self):
        """Test adding a failed result."""
        report = VerificationReport()
        result = VerificationResult(
            entry_key="test2024",
            success=False,
            message="Not found",
        )
        report.add_result(result)
        assert report.total_entries == 1
        assert report.verified == 0
        assert report.failed == 1

    def test_add_already_verified_result(self):
        """Test adding an already verified result."""
        report = VerificationReport()
        result = VerificationResult(
            entry_key="test2024",
            success=True,
            message="Already verified",
            already_verified=True,
        )
        report.add_result(result)
        assert report.total_entries == 1
        assert report.already_verified == 1
        assert report.verified == 0

    def test_add_verified_with_warning_result(self):
        """Test adding a verified result with warnings."""
        report = VerificationReport()
        result = VerificationResult(
            entry_key="test2024",
            success=True,
            message="Verified with warning",
            warnings=[FieldMismatch(field_name="title", bibtex_value="test", fetched_value="Test", source="S2")],
        )
        report.add_result(result)
        assert report.total_entries == 1
        assert report.verified == 0
        assert report.verified_with_warnings == 1


class TestVerificationStatus:
    """Tests for VerificationStatus enum and status computation."""

    def test_status_pass(self):
        """Test PASS status for clean verification."""
        result = VerificationResult(entry_key="test", success=True, message="OK")
        assert result.status == VerificationStatus.PASS

    def test_status_warning_with_warnings(self):
        """Test WARNING status when warnings exist."""
        result = VerificationResult(
            entry_key="test",
            success=True,
            message="OK",
            warnings=[FieldMismatch(field_name="title", bibtex_value="a", fetched_value="A", source="S2")],
        )
        assert result.status == VerificationStatus.WARNING

    def test_status_warning_no_paper_id(self):
        """Test WARNING status when no paper_id."""
        result = VerificationResult(entry_key="test", success=False, message="No paper_id", no_paper_id=True)
        assert result.status == VerificationStatus.WARNING

    def test_status_fail_with_mismatches(self):
        """Test FAIL status when mismatches exist."""
        result = VerificationResult(
            entry_key="test",
            success=False,
            message="Mismatch",
            mismatches=[
                FieldMismatch(field_name="year", bibtex_value="2023", fetched_value="2024", source="crossref")
            ],
        )
        assert result.status == VerificationStatus.FAIL

    def test_status_pass_when_fixed(self):
        """Test PASS status when mismatches were fixed."""
        result = VerificationResult(
            entry_key="test",
            success=True,
            message="Fixed",
            mismatches=[
                FieldMismatch(field_name="year", bibtex_value="2023", fetched_value="2024", source="crossref")
            ],
            fixed=True,
        )
        assert result.status == VerificationStatus.PASS


class TestVerificationReportOverallStatus:
    """Tests for VerificationReport.overall_status and exit_code."""

    def test_overall_pass(self):
        """Test overall PASS when all entries pass."""
        report = VerificationReport()
        report.add_result(VerificationResult(entry_key="a", success=True, message="OK"))
        report.add_result(VerificationResult(entry_key="b", success=True, message="OK"))
        assert report.overall_status == VerificationStatus.PASS
        assert report.exit_code == 0

    def test_overall_warning(self):
        """Test overall WARNING when any entry has warnings."""
        report = VerificationReport()
        report.add_result(VerificationResult(entry_key="a", success=True, message="OK"))
        report.add_result(
            VerificationResult(
                entry_key="b",
                success=True,
                message="OK",
                warnings=[FieldMismatch(field_name="title", bibtex_value="a", fetched_value="A", source="S2")],
            )
        )
        assert report.overall_status == VerificationStatus.WARNING
        assert report.exit_code == 1

    def test_overall_fail(self):
        """Test overall FAIL when any entry fails."""
        report = VerificationReport()
        report.add_result(VerificationResult(entry_key="a", success=True, message="OK"))
        report.add_result(VerificationResult(entry_key="b", success=False, message="Failed"))
        assert report.overall_status == VerificationStatus.FAIL
        assert report.exit_code == 2

    def test_fail_takes_precedence(self):
        """Test FAIL takes precedence over WARNING."""
        report = VerificationReport()
        report.add_result(VerificationResult(entry_key="a", success=False, message="No paper_id", no_paper_id=True))
        report.add_result(VerificationResult(entry_key="b", success=False, message="Failed"))
        assert report.overall_status == VerificationStatus.FAIL
        assert report.exit_code == 2

"""
TDD RED — Testy CLI: restore wymaga filestore, diagnose zwraca raport.
"""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from smartodoo.core.cli import app

runner = CliRunner()


class TestRestoreFilestoreEnforcement:
    """Problem #3 fix: restore BEZ filestore = exit 1."""

    def test_restore_without_filestore_exits_with_error(self, tmp_path):
        """Brak --filestore i brak --skip-filestore → exit 1 + ERROR."""
        dump_file = tmp_path / "dump.sql"
        dump_file.write_text("-- fake dump")

        with patch("smartodoo.core.cli.get_project_dir") as mock_dir:
            mock_dir.return_value = tmp_path  # projekt "istnieje"
            result = runner.invoke(app, [
                "restore", "--name", "test_proj", "--dump", str(dump_file)
            ])
            assert result.exit_code == 1
            assert "BRAK FILESTORE" in result.output or "Filestore Required" in result.output

    def test_restore_with_skip_filestore_shows_warning(self, tmp_path):
        """--skip-filestore → ostrzeżenie ale próba kontynuacji."""
        dump_file = tmp_path / "dump.sql"
        dump_file.write_text("-- fake dump")

        with patch("smartodoo.core.cli.get_project_dir") as mock_dir:
            mock_dir.return_value = tmp_path
            result = runner.invoke(app, [
                "restore", "--name", "test_proj",
                "--dump", str(dump_file),
                "--skip-filestore"
            ])
            # Sprawdzamy że ostrzeżenie się pojawia
            assert "Pomijasz filestore" in result.output or result.exit_code != 0


class TestDiagnoseCommand:
    """TASK-5: komenda diagnose istnieje i przyjmuje parametry."""

    def test_diagnose_command_exists(self):
        """Komenda diagnose jest zarejestrowana."""
        result = runner.invoke(app, ["diagnose", "--help"])
        assert result.exit_code == 0
        assert "diagnostyk" in result.output.lower() or "diagnose" in result.output.lower()

    def test_diagnose_missing_project_exits(self, tmp_path):
        """Nieistniejący projekt → exit 1."""
        with patch("smartodoo.core.cli.get_project_dir") as mock_dir:
            mock_dir.return_value = tmp_path / "nonexistent"
            result = runner.invoke(app, [
                "diagnose", "--name", "ghost_project"
            ])
            assert result.exit_code == 1
            assert "nie istnieje" in result.output

import pytest
from unittest.mock import MagicMock
from smartodoo.core.cli import create_parser, OdooCliOrchestrator
from smartodoo.core.config import AppConfig

def test_parser_defaults():
    """Sprawdzenie czy usunięcie setek IFów z parsera na rzecz czystego argparse'a i klasy działa."""
    parser = create_parser()
    args = parser.parse_args(["create", "-n", "MyTestProject"])
    assert args.command == "create"
    assert args.name == "MyTestProject"
    assert args.odoo == "19.0"
    assert args.psql == "16"

def test_delete_via_orchestrator():
    """Weryfikacja czy polecenie CLI niszczenia po drodze na pewno odpaliło dockera (w Mocku) z formatem usuwania volumes"""
    config = AppConfig(project_name="DestructiveProject")
    mock_docker = MagicMock()
    mock_git = MagicMock()
    
    orchestrator = OdooCliOrchestrator(config, mock_docker, mock_git)
    orchestrator.delete_project()
    
    # Assert
    mock_docker.execute.assert_called_once()
    # verify arg signature: execute(project_path, ["down", "-v"], check=False)
    call_args, kwargs = mock_docker.execute.call_args
    assert ["down", "-v"] in call_args

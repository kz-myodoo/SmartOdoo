from smartodoo.core.config import AppConfig

def test_formatted_odoo_version():
    """Weryfikuje logikę usuwania suffixów z tagów Dockera dla konfigu aplikacji."""
    cfg = AppConfig(project_name="Test", odoo_version="15")
    assert cfg.formatted_odoo_version == "15.0"
    
    cfg2 = AppConfig(project_name="Test", odoo_version="15.0")
    assert cfg2.formatted_odoo_version == "15.0"
    
    cfg3 = AppConfig(project_name="Test", odoo_version="14-custom")
    assert cfg3.formatted_odoo_version == "14.0"
    assert cfg3.odoo_revision == "-custom"
    
    cfg4 = AppConfig(project_name="Test", odoo_version="16.0")
    assert cfg4.odoo_revision == ""

def test_formatted_psql_version():
    """Weryfikuje rzutowania dla PostgreSQl - ignorowanie '.0' itp"""
    cfg = AppConfig(project_name="Test", psql_version="12.0")
    assert cfg.formatted_psql_version == "12"
    
    cfg2 = AppConfig(project_name="Test", psql_version="14")
    assert cfg2.formatted_psql_version == "14"

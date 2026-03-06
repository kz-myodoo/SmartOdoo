from dataclasses import dataclass
import re

@dataclass(frozen=True)
class AppConfig:
    project_name: str
    odoo_version: str = "19.0"
    psql_version: str = "16"
    addons_url: str = ""
    branch: str = ""
    enterprise: bool = False
    
    @property
    def formatted_odoo_version(self) -> str:
        """
        Zwraca główny wycinek wersji np '19.0' naprawiając braki np z samego '19'.
        """
        val = self.odoo_version.split('-')[0]
        if re.match(r'^\d+$', val):
            return f"{val}.0"
        return val

    @property
    def odoo_revision(self) -> str:
        """
        Zwraca resztę tagu za minusem (rewizję) z wejścia -custom .
        """
        if '-' in self.odoo_version:
            return f"-{self.odoo_version.split('-', 1)[1]}"
        return ""

    @property
    def formatted_psql_version(self) -> str:
        """
        Odrzuca niepotrzebne '12.0' dla psql pozostawiając samą '12'.
        """
        return self.psql_version[:-2] if self.psql_version.endswith(".0") else self.psql_version

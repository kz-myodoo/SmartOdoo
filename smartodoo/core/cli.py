import typer
import shutil
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smartodoo.core.config import AppConfig
from smartodoo.core.env_builder import EnvBuilder
from smartodoo.core.docker_ops import DockerOps, DockerOpsError
from smartodoo.core.db_ops import DbOps, DbOpsError
from smartodoo.core.filestore import FilestoreManager, FilestoreError
from smartodoo.core.docker_hub import DockerHubFetcher
from smartodoo.core.health_check import HealthChecker

app = typer.Typer(name="so", help="Narzędzie CLI do zarządzania środowiskami SmartOdoo", no_args_is_help=True)
console = Console()

def get_project_dir(name: str) -> Path:
    return Path.home() / "Dokumenty" / "DockerProjects" / name

@app.command("create")
def create_project(
    name: str = typer.Option(..., "--name", "-n", help="Nazwa projektu"),
    odoo: str = typer.Option("16.0", "--odoo", "-o", help="Wersja Odoo"),
    psql: str = typer.Option("15", "--psql", "-p", help="Wersja PostgreSQL"),
    addons: str = typer.Option("", "--addons", help="URL do pobrania custom addons"),
    enterprise: bool = typer.Option(False, "--enterprise", help="Klonuj Odoo Enterprise")
):
    """Tworzy nowy projekt Odoo ze zdefiniowanymi parametrami i poprawnie skonfigurowanymi plikami .env"""
    console.print(Panel(f"[bold cyan]Tworzenie projektu {name}...[/]", border_style="cyan"))
    
    config = AppConfig(project_name=name, odoo_version=odoo, psql_version=psql, addons_url=addons, enterprise=enterprise)
    project_dir = get_project_dir(name)
    env_builder = EnvBuilder(config, project_dir)
    
    with console.status("[bold green]Generowanie środowiska...[/]"):
        env_builder.write_env()
        console.print("[green]✔[/] Wygenerowano .env i strukturę projektu.")
        
    ops = DockerOps(project_dir)
    try:
        ops.compose_up()
        console.print("[bold green]✔ Kontenery podniesione![/]")
    except DockerOpsError as e:
        console.print(f"[bold red]Błąd podczas uruchamiania kontenerów![/] {e}")

@app.command("restore")
def restore_project(
    name: str = typer.Option(..., "--name", "-n", help="Nazwa projektu do którego wprowadzamy backup"),
    dump: str = typer.Option(..., "--dump", help="Ścieżka do dump.sql zrzutu z innej bazy"),
    filestore: str = typer.Option(None, "--filestore", help="Ścieżka do katalogu filestore. WYMAGANE przy pełnym restore!"),
    db: str = typer.Option("odoo", "--db", help="Docelowa nazwa bazy do stworzenia"),
    skip_filestore: bool = typer.Option(False, "--skip-filestore", help="Świadomie pomijam filestore (NIE ZALECANE)")
):
    """Przywraca zrzuconą bazę SQL do pracującego postgresa i odtwarza filestore (wymagane!)."""
    project_dir = get_project_dir(name)
    if not project_dir.exists():
        console.print(f"[bold red]Rozszerzenie nie istnieje. Projekt {name} jest nieosiągalny![/]")
        raise typer.Exit(1)
    
    # === POSTMORTEM FIX: Filestore MUSI być podany ===
    if not filestore and not skip_filestore:
        console.print(Panel(
            "[bold red]⚠ BRAK FILESTORE![/bold red]\n\n"
            "Restore BEZ filestore = [yellow]500 Internal Server Error[/] na web assets.\n"
            "Tabela ir_attachment będzie referencjować pliki, które nie istnieją.\n\n"
            "[dim]Użyj:[/]\n"
            "  --filestore <ścieżka>     podaj katalog filestore\n"
            "  --skip-filestore          pomiń świadomie (NIE ZALECANE)",
            title="🔥 Filestore Required", border_style="red"
        ))
        raise typer.Exit(1)
    
    if skip_filestore:
        console.print("[bold yellow]⚠ Pomijasz filestore — web assets mogą nie działać![/]")
        
    console.print(f"[bold yellow]Rozpoczynanie rutyny Restore dla projektu [white]{name}[/] -> Baza: [white]{db}[/]...[/]")
    
    ops = DockerOps(project_dir)
    
    db_cont = f"{name}_db_1"
    odoo_cont = f"{name}_web_1"
    
    db_manager = DbOps(ops, db_cont)
    fs_manager = FilestoreManager(ops, odoo_cont)
    
    with console.status("[bold magenta]Importowanie dumpa do psql...[/]"):
        try:
            res = db_manager.restore_database(Path(dump), db, "odoo")
            console.print(f"[green]✔[/] {res}")
        except DbOpsError as e:
            console.print(f"[red]✕ Błąd w DbOps:{e}[/]")
            raise typer.Exit(1)
            
    if filestore:
        with console.status("[bold blue]Wgrywanie filestore + nadpisywanie uprawnień odoo:odoo...[/]"):
            try:
                res2 = fs_manager.restore_filestore(Path(filestore), db)
                console.print(f"[green]✔[/] {res2}")
            except FilestoreError as e:
                console.print(f"[red]✕ Błąd w FSOps:{e}[/]")
                raise typer.Exit(1)
                
    console.print("[bold green]✨ Pomyślnie zrestorowano bazę i assets![/]")

@app.command("diagnose")
def diagnose_project(
    name: str = typer.Option(..., "--name", "-n", help="Nazwa projektu"),
    db: str = typer.Option("odoo", "--db", help="Nazwa bazy do sprawdzenia"),
    db_port: int = typer.Option(5432, "--db-port", help="Port hosta mapowany na PostgreSQL"),
    odoo_port: int = typer.Option(8069, "--odoo-port", help="Port hosta mapowany na Odoo")
):
    """Uruchamia pełną diagnostykę środowiska — sieć, porty, registry, filestore."""
    project_dir = get_project_dir(name)
    if not project_dir.exists():
        console.print(f"[bold red]Projekt {name} nie istnieje![/]")
        raise typer.Exit(1)
    
    ops = DockerOps(project_dir)
    odoo_cont = f"{name}_web_1"
    db_cont = f"{name}_db_1"
    
    checker = HealthChecker(ops, odoo_cont, db_cont)
    
    console.print(Panel(f"[bold cyan]🔍 Diagnostyka projektu {name}[/]", border_style="cyan"))
    
    with console.status("[bold green]Uruchamianie 4 checków zdrowia...[/]"):
        report = checker.run_all(db_name=db, ports=[db_port, odoo_port])
    
    table = Table("Check", "Status", "Szczegóły")
    for check in report.checks:
        icon = "✔" if check.passed else "✕"
        color = "green" if check.passed else "red"
        table.add_row(check.name, f"[{color}]{icon}[/]", check.detail)
    
    console.print(table)
    
    if report.all_passed:
        console.print(f"\n[bold green]✨ Wszystkie checki przeszły! ({report.summary()})[/]")
    else:
        console.print(f"\n[bold red]⚠ Wykryto problemy! ({report.summary()})[/]")
        raise typer.Exit(1)

@app.command("stop")
def stop_project(name: str = typer.Option(..., "--name", "-n", help="Nazwa projektu")):
    """Zatrzymuje kontenery"""
    project_dir = get_project_dir(name)
    ops = DockerOps(project_dir)
    with console.status("[yellow]Zatrzymywanie...[/]"):
        ops.compose_stop()
        console.print("[green]✔ Projekt został zatrzymany.[/]")

@app.command("list")
def list_projects():
    """Listuje zaalokowane projekty"""
    base = Path.home() / "Dokumenty" / "DockerProjects"
    table = Table("Projekt", "Status Env")
    for d in base.iterdir():
        if d.is_dir():
            has_env = "✓" if (d / ".env").exists() else "✕"
            table.add_row(d.name, has_env)
    console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()

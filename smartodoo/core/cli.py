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
        # docker-compose template is filled in reality by some templates folder or string
        # Tutaj wywołalibyśmy env_builder.write_docker_compose z poprawnym szablonem
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
    filestore: str = typer.Option(None, "--filestore", help="Ścieżka do katalogu filestore (opcjonalnie)"),
    db: str = typer.Option("odoo", "--db", help="Docelowa nazwa bazy do stworzenia")
):
    """Przywraca zrzucona bazę SQL do pracującego postgresa i opcjonalnie odtwarza asety filestore."""
    project_dir = get_project_dir(name)
    if not project_dir.exists():
        console.print(f"[bold red]Rozszerzenie nie istnieje. Projekt {name} jest nieosiągalny![/]")
        raise typer.Exit(1)
        
    console.print(f"[bold yellow]Rozpoczynanie rutyny Restore dla projektu [white]{name}[/] -> Baza: [white]{db}[/]...[/]")
    
    ops = DockerOps(project_dir)
    
    # Próbujemy znaleźć faktyczne nazwy kontenerów dla Dockera (zazwyczaj <project>_db_1 etc., tu używamy patternów)
    # W pełnej implementacji nazwy kontenerów pochodziły by z AppConfig/z baz.
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

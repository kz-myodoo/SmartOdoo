#!/usr/bin/env python3
"""
Skrypt przekierowujący, pełniący funkcję zachowania kompatybilności wstecznej CLI.
Zamiast 600+ linijek spaghetti kodu, wywołuje dedykowaną bibliotekę w najnowszych standardach.
"""
import sys

def main():
    try:
        if len(sys.argv) == 1:
            from rich.prompt import Prompt
            from rich.console import Console
            console = Console()
            console.print("\n[bold cyan]✨ Witaj w SmartOdoo! ✨[/bold cyan]")
            console.print("Środowisko wykryło brak podanych komend startowych.")
            console.print("Wybierz, w jakim trybie chcesz pracować z oprogramowaniem:\n")
            console.print("[1] 💻 [bold]Klasyczny Terminal (CLI)[/bold] - polecenia tekstowe")
            console.print("[2] 🎨 [bold magenta]Premium GUI (Dark Mode)[/bold magenta] - widok okienkowy")
            
            wybór = Prompt.ask("\nTwój wybór", choices=["1", "2"], default="2")
            
            if wybór == "2":
                # Import the GUI engine inside to avoid loading custom-Tkinter if user doesn't want it!
                from smartodoo.gui.app import run_gui
                sys.exit(run_gui())
            else:
                # Wymusza flagę help by wyświetlić jak korzystać z the CLI
                sys.argv.append("--help")
                
        from smartodoo.core.cli import main as cli_main
        sys.exit(cli_main())
    except ImportError as e:
        print(f"Brak zainstalowanej aplikacji lub brakującego modułu (np. customtkinter). \nUżyj: pip install -e . \nBłąd: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

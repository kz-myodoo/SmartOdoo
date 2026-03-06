#!/usr/bin/env python3
"""
Skrypt przekierowujący, pełniący funkcję zachowania kompatybilności wstecznej CLI.
Zamiast 600+ linijek spaghetti kodu, wywołuje dedykowaną bibliotekę w najnowszych standardach.
"""
import sys

def main():
    try:
        from smartodoo.core.cli import main as cli_main
        sys.exit(cli_main())
    except ImportError as e:
        print(f"Brak zainstalowanej aplikacji smartodoo. Użyj: pip install -e . \nBłąd: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import customtkinter as ctk
from tkinter import messagebox
from smartodoo.core.config import AppConfig
from smartodoo.core.docker_manager import DockerManager
from smartodoo.core.git_manager import GitManager
from smartodoo.core.cli import OdooCliOrchestrator
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SmartOdooApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartOdoo - Premium Environment Builder")
        self.geometry("600x550")
        self.resizable(False, False)

        # Header
        self.label_title = ctk.CTkLabel(self, text="Konfigurator Projektu Odoo", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=(20, 10))
        
        self.label_subtitle = ctk.CTkLabel(self, text="Skonfiguruj wiodący projekt przy użyciu natywnych opcji Dockera", text_color="gray")
        self.label_subtitle.pack(pady=(0, 20))

        # Main Frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10, padx=40, fill="both", expand=True)

        # Nazwa projektu (Name)
        self.label_name = ctk.CTkLabel(self.frame, text="1. Nazwa folderu i środowiska projektu:", anchor="w")
        self.label_name.pack(pady=(20, 5), padx=20, fill="x")
        self.entry_name = ctk.CTkEntry(self.frame, placeholder_text="np. WspanialySklep")
        self.entry_name.pack(pady=(0, 15), padx=20, fill="x")

        # Wersja Odoo
        self.label_odoo = ctk.CTkLabel(self.frame, text="2. Wersja Odoo (Tag):", anchor="w")
        self.label_odoo.pack(pady=(5, 5), padx=20, fill="x")
        self.combo_odoo = ctk.CTkComboBox(self.frame, values=["19.0", "18.0", "17.0", "16.0", "15.0"])
        self.combo_odoo.set("19.0")
        self.combo_odoo.pack(pady=(0, 15), padx=20, fill="x")

        # Wersja PSQL
        self.label_psql = ctk.CTkLabel(self.frame, text="3. Baza PostgreSQL:", anchor="w")
        self.label_psql.pack(pady=(5, 5), padx=20, fill="x")
        self.combo_psql = ctk.CTkComboBox(self.frame, values=["16", "15", "14", "13", "12"])
        self.combo_psql.set("16")
        self.combo_psql.pack(pady=(0, 15), padx=20, fill="x")

        # Flagi Switch
        self.switch_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.switch_frame.pack(pady=10, padx=20, fill="x")

        self.switch_enterprise = ctk.CTkSwitch(self.switch_frame, text="Pobierz Enterprise (Git Clone)")
        self.switch_enterprise.pack(side="left", padx=(0, 20))

        self.entry_addons = ctk.CTkEntry(self.switch_frame, placeholder_text="URL dla Extra Addons (Opcjonalnie)", width=200)
        self.entry_addons.pack(side="right", fill="x", expand=True)

        # Przycisk tworzenia
        self.btn_create = ctk.CTkButton(self, text="🚀 Uruchom Budowanie", font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.on_create)
        self.btn_create.pack(pady=20, padx=40, fill="x")

        # Przycisk POMOC (Helper dla the UX)
        self.btn_help = ctk.CTkButton(self, text="❔ Instrukcja GUI", width=120, fg_color="transparent", border_width=1, text_color="gray", command=self.show_help)
        self.btn_help.pack(side="bottom", pady=10)

    def show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Instrukcja Obsługi SmartOdoo GUI")
        help_window.geometry("500x350")
        help_window.resizable(False, False)
        
        # Otwórz the okno na samym the przodzie the aplikacji
        help_window.attributes("-topmost", True)
        help_window.grab_set()

        help_text = (
            "🚀 SmartOdoo Premium Builder - Pomoc\n\n"
            "Interfejs ten generuje dla The Ciebie dedykowane pliki .env oraz the docker-compose.yml.\n\n"
            "Kroki:\n"
            "1. Nazwa Folderu - To the ścieżka The lokalna (np. SklepZoologiczny), The w niej będą żyły The bazy Odoo.\n"
            "2. Wersja Odoo - Opcje (15-19) zostaną the wciągnięte z DockerHuba the w biegu ułamka the sekundy.\n"
            "3. Flaga 'Pobierz Enterprise' - Zaciąga the komercyjne kody Enterprise the poprzez mechanizm GITA The w podfolder.\n\n"
            "💡 Wszystko odbywa się bezpiecznie pod maską klasy The Dependency Injection. The Żaden the proces na głównym oknie the nie zamrozi the widoku."
        )

        label = ctk.CTkLabel(help_window, text=help_text, justify="left", wraplength=450)
        label.pack(padx=20, pady=20)
        
        btn_close = ctk.CTkButton(help_window, text="Zrozumiałem", command=help_window.destroy)
        btn_close.pack(pady=10)

    def on_create(self):
        project_name = self.entry_name.get().strip()
        if not project_name:
            messagebox.showwarning("Błąd walidacji", "Nazwa projektu jest wymagana!")
            return

        odoo_version = self.combo_odoo.get()
        psql_version = self.combo_psql.get()
        is_enterprise = self.switch_enterprise.get() == 1
        addons_url = self.entry_addons.get().strip() or None

        self.btn_create.configure(state="disabled", text="⏳ Trwa budowanie środowiska w tle...")
        
        # Odoo orchestrator freezes console, run it inside thread
        threading.Thread(target=self._run_orchestrator, args=(project_name, odoo_version, psql_version, addons_url, is_enterprise), daemon=True).start()

    def _run_orchestrator(self, name, odoo, psql, addons, enterprise):
        try:
            config = AppConfig(
                project_name=name,
                odoo_version=odoo,
                postgres_version=psql,
                addons_repo=addons,
                is_enterprise=enterprise
            )
            docker_manager = DockerManager()
            git_manager = GitManager()
            orchestrator = OdooCliOrchestrator(config, docker_manager, git_manager)

            # Execution
            orchestrator.create_project()

            self.after(0, self._show_success)
        except Exception as e:
            self.after(0, self._show_error, str(e))
        finally:
            self.after(0, lambda: self.btn_create.configure(state="normal", text="🚀 Uruchom Budowanie"))

    def _show_success(self):
        messagebox.showinfo("Sukończenie Operacji", "Aplikacja zaplanowana w folderze DockerProjects.\nZajrzyj do docelowych plików!")

    def _show_error(self, message):
        messagebox.showerror("Wystąpił nieoczekiwany wyjątek procesów terminala", message)

def run_gui():
    app = SmartOdooApp()
    app.mainloop()

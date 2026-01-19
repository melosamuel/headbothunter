import customtkinter as ctk
import webbrowser
import threading
from tkinter import messagebox

from .core.file_manager import FileManager
from .core.data_manager import DataManager
from .core.settings import DATA_FILE
from Scraper.bot import RPA

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- PALETTE ---
BG_COLOR = "#1c1c1c"
CARD_COLOR = "#2b2b2b"
PRIMARY_COLOR = "#42195e"
TEXT_COLOR = "#ffffff"
TEXT_SUBTLE = "#a0a0a0"
ACCENT_GREEN = "#238636"
ACCENT_RED = "#da3633"
TITLE = "HeadBot Hunter"

class HeadBotHunter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("900x650")
        self.configure(fg_color=BG_COLOR)

        self.file_manager = FileManager(DATA_FILE)
        self.data = self.file_manager.load()
        self.current_job = []

        self.setup_ui()
        self.check_initial_config()

    def setup_ui(self):
        self.header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=PRIMARY_COLOR)
        self.header.pack(fill="x", side="top")
        
        self.lbl_logo = ctk.CTkLabel(self.header, text="Job Hunter", font=("Roboto", 24, "bold"), text_color="white")
        self.lbl_logo.pack(side="left", padx=20, pady=20)

        self.btn_manage = ctk.CTkButton(self.header, text="Manage Companies", command=self.open_management_modal, 
                                      fg_color="transparent", border_width=1, border_color="white", text_color="white",
                                      hover_color="#5a2d7a", width=150)
        self.btn_manage.pack(side="right", padx=20)

        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.btn_search = ctk.CTkButton(self.action_frame, text="Find Jobs", command=self.start_scraping_thread,
                                    height=45, corner_radius=8, font=("Roboto", 15, "bold"),
                                    fg_color="white", text_color=PRIMARY_COLOR, hover_color="#e0e0e0")
        self.btn_search.pack(fill="x")

        self.spinner = ctk.CTkProgressBar(self, mode="indeterminate", width=400, progress_color=PRIMARY_COLOR)
        
        self.error_label = ctk.CTkLabel(self, text="", text_color="#ff5555", font=("Roboto", 12))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="Feed", label_text_color=TEXT_SUBTLE)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def check_initial_config(self):
        if not self.data.get("companies"):
            self.open_management_modal(first_time=True)

    def start_scraping_thread(self):
        self.clear_cards()
        self.error_label.pack_forget()
        self.btn_search.configure(state="disabled", text="Searching...")

        self.spinner.pack(pady=10)
        self.spinner.start()

        thread = threading.Thread(target=self.run_scraping_logic)
        thread.daemon = True
        thread.start()

    def run_scraping_logic(self):
        found_jobs = []
        errors = []

        companies = self.data.get("companies", [])
        
        for company in companies:
            try:
                jobs = RPA(company["name"]).scrape_stone()
                for j in jobs:
                    j["company_name"] = company["name"]
                    found_jobs.append(j)
            except Exception as e:
                errors.append(f"{company['name']}: {str(e)}")
                continue

        self.after(0, lambda: self.finish_scraping(found_jobs, errors))

    def finish_scraping(self, found_jobs, errors):
        self.spinner.stop()
        self.spinner.pack_forget()
        self.btn_search.configure(state="normal", text="Find Jobs")

        if errors:
            self.error_label.configure(text=f"Errors: {'; '.join(errors)}")
            self.error_label.pack(pady=5, before=self.scroll_frame)

        for job in found_jobs:
            data_manager = DataManager(job['title'], job['date']) 
            if not data_manager.is_banned():
                self.create_job_card(job)

    def create_job_card(self, job):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color="#3a3a3a")
        card.pack(fill="x", pady=8)

        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=job["company_name"].upper(), font=("Roboto", 11), text_color=TEXT_SUBTLE, anchor="w")\
            .grid(row=0, column=0, padx=15, pady=(15, 0), sticky="ew")

        ctk.CTkLabel(card, text=job["title"], font=("Roboto", 16, "bold"), text_color="white", anchor="w", wraplength=700)\
            .grid(row=1, column=0, padx=15, pady=(5, 5), sticky="ew")
        
        desc_text = job["desc"][:120] + "..." if len(job["desc"]) > 120 else job["desc"]
        ctk.CTkLabel(card, text=desc_text, font=("Roboto", 12), text_color="#bdbdbd", anchor="w", justify="left")\
            .grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        ctk.CTkButton(btn_frame, text="Apply", command=lambda: webbrowser.open(job["link"]), 
                      fg_color=ACCENT_GREEN, hover_color="#2ea043", width=120).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="Ban Title", command=lambda: self.ban_job(job['title'], 'title', card),
                      fg_color="transparent", border_width=1, border_color=ACCENT_RED, text_color=ACCENT_RED,
                      hover_color="#3b2222", width=120).pack(side="right")

    def clear_cards(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def ban_job(self, value, type_, card_widget):
        if type_ == 'title':
            self.data.setdefault("banned_titles", []).append(value)
        else:
            self.data.setdefault("banned_dates", []).append(value)

        self.file_manager.save(self.data)
        
        card_widget.destroy()
        print(f"{type_.capitalize()} blocked successfully!")

    def open_management_modal(self, first_time=False):
        modal = ctk.CTkToplevel(self)
        modal.title("Manage Companies")
        modal.geometry("500x500")
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="Company Name:").pack(pady=(20, 5))
        entry_name = ctk.CTkEntry(modal, width=300)
        entry_name.pack(pady=5)

        ctk.CTkLabel(modal, text="Job URL:").pack(pady=5)
        entry_url = ctk.CTkEntry(modal, width=300)
        entry_url.pack(pady=5)

        ctk.CTkLabel(modal, text="Saved Companies:").pack(pady=(20, 5))
        txt_display = ctk.CTkTextbox(modal, width=400, height=150)
        txt_display.pack(pady=5)
        
        def refresh_list():
            txt_display.configure(state="normal")
            txt_display.delete("0.0", "end")
            self.data = self.file_manager.load()
            if "companies" in self.data:
                for comp in self.data["companies"]:
                    txt_display.insert("end", f"• {comp['name']} \n  {comp['url']}\n\n")
            txt_display.configure(state="disabled")

        refresh_list()

        def add_company():
            name = entry_name.get()
            url = entry_url.get()

            if name and url:
                self.data.setdefault("companies", []).append({"name": name, "url": url})
                self.file_manager.save(self.data)
                
                refresh_list()
                
                entry_name.delete(0, 'end')
                entry_url.delete(0, 'end')
                if first_time: modal.destroy()

        ctk.CTkButton(modal, text="Save Companies", command=add_company, fg_color=PRIMARY_COLOR).pack(pady=20)

        if first_time:
            modal.protocol("WM_DELETE_WINDOW", lambda: messagebox.showwarning("Warning", "Add at least one company!"))

if __name__ == "__main__":
    app = HeadBotHunter()
    app.mainloop()
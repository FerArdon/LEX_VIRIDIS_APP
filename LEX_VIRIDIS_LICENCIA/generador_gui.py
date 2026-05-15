"""
LEX VIRIDIS — Generador de Licencias v2.0
Interfaz gráfica moderna (estilo Windows 11) para generar y validar licencias.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import json
from license_system import LicenseManager

# ── Paleta de colores ──────────────────────────────────────────────────────────
PRIMARY      = "#006666"
PRIMARY_DARK = "#004d4d"
ACCENT       = "#0097a7"
SUCCESS      = "#2e7d32"
WARNING      = "#e65100"
ERROR_COLOR  = "#c62828"
SURFACE      = "#f5f5f5"
BORDER       = "#e0e0e0"
TEXT_PRI     = "#1a1a1a"
TEXT_SEC     = "#666666"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Descripción por tipo de licencia ─────────────────────────────────────────
TYPE_INFO = {
    "PRUEBA":     ("15 días",   "Para evaluación institucional."),
    "MENSUAL":    ("30 días",   "Renovación mensual."),
    "SEMESTRAL":  ("180 días",  "Renovación semestral. Ahorro del 20%."),
    "ANUAL":      ("365 días",  "Renovación anual. Ahorro del 35%."),
    "PERMANENTE": ("Sin límite","Licencia vitalicia. Pago único."),
}


class GeneradorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LEX VIRIDIS — Generador de Licencias")
        self.geometry("780x680")
        self.minsize(720, 600)
        self.resizable(True, True)
        self._set_icon()

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        self.after(100, self._on_type_change)   # poblar hint inicial

    # ── Icono (silencioso si no existe) ───────────────────────────────────────
    def _set_icon(self):
        try:
            from pathlib import Path
            ico = Path(__file__).parent.parent / "assets" / "lexviridis.ico"
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    # ── Encabezado ─────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=0, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="LEX VIRIDIS",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color="white"
        ).pack(side="left", padx=(0, 12))

        sep = ctk.CTkFrame(inner, width=2, height=32, fg_color="#339999", corner_radius=1)
        sep.pack(side="left", padx=8)

        ctk.CTkLabel(
            inner, text="Generador de Licencias",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="#cce8e8"
        ).pack(side="left")

    # ── Pestañas ───────────────────────────────────────────────────────────────
    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=SURFACE,
            segmented_button_fg_color=BORDER,
            segmented_button_selected_color=PRIMARY,
            segmented_button_selected_hover_color=PRIMARY_DARK,
            segmented_button_unselected_color=BORDER,
            segmented_button_unselected_hover_color="#d5d5d5",
            text_color=TEXT_PRI,
            text_color_disabled=TEXT_SEC,
            corner_radius=0,
        )
        self.tabs.pack(fill="both", expand=True, padx=0, pady=0)

        self.tabs.add("  Generar Licencia  ")
        self.tabs.add("  Validar Licencia  ")

        self._build_generate_tab(self.tabs.tab("  Generar Licencia  "))
        self._build_validate_tab(self.tabs.tab("  Validar Licencia  "))

    # ── Tab: Generar ───────────────────────────────────────────────────────────
    def _build_generate_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # ── Sección: Datos del cliente ───────────────────────────────────────
        self._section_label(scroll, "Datos del Cliente")

        ctk.CTkLabel(scroll, text="Nombre o institución *",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(fill="x", pady=(4, 2))
        self.entry_client = ctk.CTkEntry(
            scroll, placeholder_text="Ej: FEMA — Ing. Juan Pérez",
            height=38, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 13),
            border_color=BORDER, border_width=1,
        )
        self.entry_client.pack(fill="x", pady=(0, 14))

        # ── Sección: Tipo de licencia ────────────────────────────────────────
        self._section_label(scroll, "Tipo de Licencia")

        type_row = ctk.CTkFrame(scroll, fg_color="transparent")
        type_row.pack(fill="x", pady=(4, 0))

        self.type_var = ctk.StringVar(value="ANUAL")
        self.type_seg = ctk.CTkSegmentedButton(
            type_row,
            values=["PRUEBA", "MENSUAL", "SEMESTRAL", "ANUAL", "PERMANENTE"],
            variable=self.type_var,
            command=self._on_type_change,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=BORDER,
            selected_color=PRIMARY,
            selected_hover_color=PRIMARY_DARK,
            unselected_color=BORDER,
            height=36,
            corner_radius=8,
        )
        self.type_seg.pack(fill="x")

        # Hint del tipo
        self.hint_frame = ctk.CTkFrame(
            scroll, fg_color=("#e8f4f4", "#1a3030"), corner_radius=8
        )
        self.hint_frame.pack(fill="x", pady=(8, 14))

        self.lbl_hint_duration = ctk.CTkLabel(
            self.hint_frame, text="",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=PRIMARY, anchor="w"
        )
        self.lbl_hint_duration.pack(anchor="w", padx=14, pady=(10, 2))

        self.lbl_hint_desc = ctk.CTkLabel(
            self.hint_frame, text="",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_SEC, anchor="w"
        )
        self.lbl_hint_desc.pack(anchor="w", padx=14, pady=(0, 10))

        # ── Sección: Asientos ────────────────────────────────────────────────
        self._section_label(scroll, "Número de Activaciones (PCs)")

        seats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        seats_row.pack(fill="x", pady=(4, 14))

        self.seats_var = ctk.IntVar(value=1)
        for val, lbl in [(1, "1 PC"), (2, "2 PCs"), (3, "3 PCs"), (5, "5 PCs"), (0, "Ilimitado")]:
            ctk.CTkRadioButton(
                seats_row, text=lbl, variable=self.seats_var, value=val,
                font=ctk.CTkFont("Segoe UI", 12),
                fg_color=PRIMARY, hover_color=PRIMARY_DARK,
            ).pack(side="left", padx=(0, 18))

        # ── Fecha de emisión (solo informativo) ──────────────────────────────
        today = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")
        ctk.CTkLabel(
            scroll, text=f"Fecha de emisión: {today}",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=TEXT_SEC, anchor="w"
        ).pack(anchor="w", pady=(0, 16))

        # ── Botón generar ────────────────────────────────────────────────────
        ctk.CTkButton(
            scroll, text="  Generar Licencia",
            command=self._generate,
            fg_color=PRIMARY, hover_color=PRIMARY_DARK,
            height=44, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
        ).pack(fill="x", pady=(0, 20))

        # ── Resultado ────────────────────────────────────────────────────────
        self._section_label(scroll, "Licencia Generada")

        self.result_box = ctk.CTkTextbox(
            scroll, height=100, corner_radius=8,
            font=ctk.CTkFont("Consolas", 11),
            fg_color=("#f0f8f0", "#1a2a1a"),
            border_color=BORDER, border_width=1,
            wrap="word", state="disabled",
        )
        self.result_box.pack(fill="x", pady=(4, 8))

        # Info de la licencia generada
        self.result_info = ctk.CTkLabel(
            scroll, text="",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SEC, anchor="w", justify="left"
        )
        self.result_info.pack(anchor="w", pady=(0, 10))

        # Botones acción resultado
        action_row = ctk.CTkFrame(scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 16))

        self.btn_copy = ctk.CTkButton(
            action_row, text="Copiar al portapapeles",
            command=self._copy_license,
            fg_color="transparent", border_width=1, border_color=PRIMARY,
            text_color=PRIMARY, hover_color=("#e0f0f0", "#1a3a3a"),
            height=36, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
            state="disabled",
        )
        self.btn_copy.pack(side="left", padx=(0, 10))

        self.btn_save = ctk.CTkButton(
            action_row, text="Guardar en archivo .txt",
            command=self._save_to_file,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=TEXT_SEC, hover_color=("#e8e8e8", "#2a2a2a"),
            height=36, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 12),
            state="disabled",
        )
        self.btn_save.pack(side="left")

        self._generated_key = ""

    # ── Tab: Validar ───────────────────────────────────────────────────────────
    def _build_validate_tab(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=16)

        self._section_label(frame, "Clave de Licencia a Validar")

        ctk.CTkLabel(frame, text="Pega la clave completa en el campo de abajo:",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=TEXT_SEC, anchor="w").pack(anchor="w", pady=(4, 6))

        self.entry_validate = ctk.CTkTextbox(
            frame, height=90, corner_radius=8,
            font=ctk.CTkFont("Consolas", 11),
            border_color=BORDER, border_width=1,
            wrap="word",
        )
        self.entry_validate.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(
            frame, text="  Validar Licencia",
            command=self._validate,
            fg_color=ACCENT, hover_color="#00838f",
            height=44, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
        ).pack(fill="x", pady=(0, 20))

        self._section_label(frame, "Resultado de la Validación")

        self.validate_result = ctk.CTkFrame(
            frame, fg_color=SURFACE, corner_radius=10,
            border_color=BORDER, border_width=1,
        )
        self.validate_result.pack(fill="x", pady=(6, 0))

        self.lbl_val_status = ctk.CTkLabel(
            self.validate_result, text="Sin resultado aún.",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=TEXT_SEC, anchor="w"
        )
        self.lbl_val_status.pack(anchor="w", padx=16, pady=(14, 4))

        self.lbl_val_detail = ctk.CTkLabel(
            self.validate_result, text="",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=TEXT_SEC, anchor="w", justify="left"
        )
        self.lbl_val_detail.pack(anchor="w", padx=16, pady=(0, 14))

    # ── Status bar ─────────────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=BORDER, corner_radius=0, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        hw = LicenseManager.get_hardware_id()
        ctk.CTkLabel(
            bar, text=f"Hardware ID de este equipo: {hw}",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=TEXT_SEC
        ).pack(side="left", padx=14)

        ctk.CTkLabel(
            bar, text="LEX VIRIDIS v2.0",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=TEXT_SEC
        ).pack(side="right", padx=14)

    # ── Helpers UI ─────────────────────────────────────────────────────────────
    def _section_label(self, parent, text: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(6, 4))
        ctk.CTkLabel(
            row, text=text,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=TEXT_PRI, anchor="w"
        ).pack(side="left")
        ctk.CTkFrame(row, height=1, fg_color=BORDER).pack(
            side="left", fill="x", expand=True, padx=(10, 0), pady=6
        )

    # ── Lógica ──────────────────────────────────────────────────────────────────
    def _on_type_change(self, *_):
        t = self.type_var.get()
        dur, desc = TYPE_INFO.get(t, ("—", ""))
        self.lbl_hint_duration.configure(text=f"Duración: {dur}")
        self.lbl_hint_desc.configure(text=desc)

    def _generate(self):
        client = self.entry_client.get().strip()
        if not client:
            self._flash_error("Ingresa el nombre del cliente antes de continuar.")
            return

        license_type = self.type_var.get()
        seats = self.seats_var.get()

        try:
            key = LicenseManager.generate_license(license_type, client, seats)
        except Exception as e:
            self._flash_error(f"Error al generar: {e}")
            return

        self._generated_key = key

        # Mostrar en caja
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", key)
        self.result_box.configure(state="disabled")

        # Info resumen
        dur, _ = TYPE_INFO.get(license_type, ("—", ""))
        seats_label = "Ilimitado" if seats == 0 else f"{seats} PC(s)"
        exp = (datetime.datetime.now() + datetime.timedelta(
            days=LicenseManager.LICENSE_TYPES[license_type]
        )).strftime("%d/%m/%Y")
        self.result_info.configure(
            text=f"Cliente: {client}   |   Tipo: {license_type}   |   "
                 f"Duración: {dur}   |   Vence: {exp}   |   Asientos: {seats_label}",
            text_color=SUCCESS
        )

        # Habilitar botones
        self.btn_copy.configure(state="normal")
        self.btn_save.configure(state="normal")

        self._set_status(f"✓ Licencia {license_type} generada para «{client}»")

    def _copy_license(self):
        if not self._generated_key:
            return
        self.clipboard_clear()
        self.clipboard_append(self._generated_key)
        self._set_status("✓ Clave copiada al portapapeles")

    def _save_to_file(self):
        if not self._generated_key:
            return
        client_safe = self.entry_client.get().strip().replace(" ", "_")[:30]
        default_name = f"Licencia_{self.type_var.get()}_{client_safe}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Archivo de texto", "*.txt")],
            title="Guardar licencia"
        )
        if not path:
            return
        try:
            exp = (datetime.datetime.now() + datetime.timedelta(
                days=LicenseManager.LICENSE_TYPES[self.type_var.get()]
            )).strftime("%d/%m/%Y")
            seats = self.seats_var.get()
            seats_label = "Ilimitado" if seats == 0 else str(seats)
            content = (
                f"LEX VIRIDIS — Licencia de Uso\n"
                f"{'='*50}\n"
                f"Cliente:     {self.entry_client.get().strip()}\n"
                f"Tipo:        {self.type_var.get()}\n"
                f"Asientos:    {seats_label}\n"
                f"Vencimiento: {exp}\n"
                f"Emitida:     {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"{'='*50}\n\n"
                f"CLAVE DE LICENCIA:\n{self._generated_key}\n"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._set_status(f"✓ Guardado en: {path}")
        except Exception as e:
            self._flash_error(f"Error al guardar: {e}")

    def _validate(self):
        key = self.entry_validate.get("1.0", "end").strip()
        if not key:
            self.lbl_val_status.configure(
                text="Ingresa una clave para validar.", text_color=TEXT_SEC
            )
            self.lbl_val_detail.configure(text="")
            return

        result = LicenseManager.validate_license(key, check_hardware=False)

        if result.get("valid"):
            self.validate_result.configure(border_color=SUCCESS)
            self.lbl_val_status.configure(
                text=f"✓ LICENCIA VÁLIDA — {result['type']}",
                text_color=SUCCESS,
                font=ctk.CTkFont("Segoe UI", 13, "bold")
            )
            seats = result.get("max_seats", 1)
            seats_label = "Ilimitado" if seats == 0 else str(seats)
            self.lbl_val_detail.configure(
                text=(
                    f"Cliente:     {result.get('client', '—')}\n"
                    f"Vence:       {result.get('expires', '—')}   "
                    f"({result.get('days_left', 0)} días restantes)\n"
                    f"Asientos:    {seats_label}"
                ),
                text_color=TEXT_PRI
            )
            self._set_status("✓ Licencia válida")
        else:
            self.validate_result.configure(border_color=ERROR_COLOR)
            self.lbl_val_status.configure(
                text=f"✗ LICENCIA INVÁLIDA",
                text_color=ERROR_COLOR,
                font=ctk.CTkFont("Segoe UI", 13, "bold")
            )
            self.lbl_val_detail.configure(
                text=result.get("error", "Error desconocido."),
                text_color=ERROR_COLOR
            )
            self._set_status("✗ Licencia inválida o expirada")

    def _set_status(self, msg: str):
        # Actualizar el primer label del status bar
        try:
            for w in self.winfo_children():
                if isinstance(w, ctk.CTkFrame) and w.cget("corner_radius") == 0:
                    children = w.winfo_children()
                    if children:
                        children[0].configure(text=msg)
                        break
        except Exception:
            pass

    def _flash_error(self, msg: str):
        messagebox.showerror("Error", msg, parent=self)


if __name__ == "__main__":
    app = GeneradorApp()
    app.mainloop()

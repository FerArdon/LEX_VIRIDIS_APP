"""
LEX VIRIDIS - Breadcrumb Bar Component
Sistema de navegación por niveles (Migas de Pan).
"""

import customtkinter as ctk
from lexviridis.design_system_ctk import Colors, Typography

class BreadcrumbBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=50, fg_color="transparent", **kwargs)
        self.route = []
        self.labels = []
        self.separators = []

    def set_route(self, route_list):
        """
        Limpia y dibuja la nueva ruta.
        Ejemplo: route_list = ["Inicio", "Buscador"]
        """
        # Limpiar widgets previos
        for widget in self.winfo_children():
            widget.destroy()
        
        self.route = route_list
        self.labels = []
        
        for i, item in enumerate(self.route):
            # Separador (excepto el primero)
            if i > 0:
                sep = ctk.CTkLabel(
                    self, 
                    text=" › ", 
                    font=Typography.body(),
                    text_color=Colors.TEXT_SECONDARY
                )
                sep.pack(side="left")
            
            # Label del ítem
            is_last = (i == len(self.route) - 1)
            font = Typography.bold() if is_last else Typography.body()
            color = Colors.PRIMARY if is_last else Colors.TEXT_SECONDARY
            
            lbl = ctk.CTkLabel(
                self, 
                text=item, 
                font=font,
                text_color=color
            )
            lbl.pack(side="left")
            self.labels.append(lbl)

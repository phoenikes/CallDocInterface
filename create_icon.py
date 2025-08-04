"""
Icon-Generator für die CallDoc-SQLHK Synchronisierungs-Anwendung

Dieses Skript erstellt ein Icon für die Anwendung mit einem medizinischen Symbol
und der Darstellung einer Synchronisierung zwischen zwei Systemen.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Erstellt ein Icon für die CallDoc-SQLHK Synchronisierungs-Anwendung"""
    
    # Größen für verschiedene Icon-Versionen
    sizes = [16, 32, 48, 64, 128, 256]
    
    # Farben
    background_color = (41, 128, 185)  # Blau
    accent_color = (231, 76, 60)       # Rot
    text_color = (255, 255, 255)       # Weiß
    
    icons = []
    
    for size in sizes:
        # Neues Bild mit transparentem Hintergrund erstellen
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Hintergrund (abgerundetes Quadrat)
        padding = size // 10
        draw.rectangle(
            [(padding, padding), (size - padding, size - padding)],
            fill=background_color,
            outline=None,
            width=0
        )
        
        # Medizinisches Symbol (vereinfachtes Kreuz)
        cross_size = size // 2
        cross_x = (size - cross_size) // 2
        cross_y = (size - cross_size) // 4
        
        line_width = max(1, size // 16)
        
        # Horizontale Linie
        draw.rectangle(
            [(cross_x, cross_y + cross_size // 3), 
             (cross_x + cross_size, cross_y + cross_size // 3 + line_width)],
            fill=text_color
        )
        
        # Vertikale Linie
        draw.rectangle(
            [(cross_x + cross_size // 2 - line_width // 2, cross_y), 
             (cross_x + cross_size // 2 + line_width // 2, cross_y + cross_size // 1.5)],
            fill=text_color
        )
        
        # Synchronisierungssymbol (zwei Pfeile im Kreis)
        sync_radius = size // 4
        sync_center_x = size // 2
        sync_center_y = size - sync_radius - padding
        
        # Kreis
        draw.ellipse(
            [(sync_center_x - sync_radius, sync_center_y - sync_radius),
             (sync_center_x + sync_radius, sync_center_y + sync_radius)],
            outline=accent_color,
            width=max(1, size // 32)
        )
        
        # Pfeile (vereinfacht für kleine Icons)
        arrow_size = sync_radius // 2
        
        # Pfeil 1 (links nach rechts)
        draw.line(
            [(sync_center_x - arrow_size, sync_center_y),
             (sync_center_x + arrow_size // 2, sync_center_y)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        # Pfeilspitze 1
        draw.line(
            [(sync_center_x + arrow_size // 2, sync_center_y),
             (sync_center_x, sync_center_y - arrow_size // 2)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        draw.line(
            [(sync_center_x + arrow_size // 2, sync_center_y),
             (sync_center_x, sync_center_y + arrow_size // 2)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        # Pfeil 2 (rechts nach links)
        draw.line(
            [(sync_center_x + arrow_size // 2, sync_center_y - arrow_size // 2),
             (sync_center_x - arrow_size // 2, sync_center_y - arrow_size // 2)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        # Pfeilspitze 2
        draw.line(
            [(sync_center_x - arrow_size // 2, sync_center_y - arrow_size // 2),
             (sync_center_x, sync_center_y - arrow_size)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        draw.line(
            [(sync_center_x - arrow_size // 2, sync_center_y - arrow_size // 2),
             (sync_center_x - arrow_size, sync_center_y - arrow_size // 2)],
            fill=text_color,
            width=max(1, size // 32)
        )
        
        # Für größere Icons: Buchstaben C und S für CallDoc und SQLHK
        if size >= 48:
            letter_size = size // 6
            
            # C für CallDoc (links)
            draw.text(
                (size // 4 - letter_size // 2, size // 2),
                "C",
                fill=text_color,
                font=None
            )
            
            # S für SQLHK (rechts)
            draw.text(
                (3 * size // 4 - letter_size // 2, size // 2),
                "S",
                fill=text_color,
                font=None
            )
        
        icons.append(img)
    
    # Speichern als ICO-Datei
    icon_path = os.path.join("resources", "app_icon.ico")
    icons[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=icons[1:])
    
    print(f"Icon erstellt und gespeichert unter: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()

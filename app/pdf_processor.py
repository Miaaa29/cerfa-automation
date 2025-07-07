from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.page_width, self.page_height = A4
    
    def fill_cerfa(self, pdf_data: bytes, data) -> bytes:
        """
        Remplit le CERFA 13757 avec positionnement précis
        """
        try:
            logger.info("Génération du PDF avec positionnement corrigé")
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Coordonnées ajustées pour un meilleur alignement
            coordinates = {
                'nom_prenom': (160, 720),      # Après "Je soussigné(e),"
                'adresse': (125, 698),         # Ligne adresse
                'cp_ville': (125, 680),        # Code postal + ville
                'marque': (205, 520),          # Après "Marque :"
                'immatriculation': (325, 485), # Numéro immatriculation
                'lieu_signature': (150, 200),  # "Fait à"
                'date_signature': (350, 200)   # Date
            }
            
            # Police et taille
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0, 0, 0)  # Texte noir
            
            # Remplir les champs
            if data.nom_prenom:
                c.drawString(coordinates['nom_prenom'][0], coordinates['nom_prenom'][1], data.nom_prenom)
            
            if data.adresse:
                c.drawString(coordinates['adresse'][0], coordinates['adresse'][1], data.adresse)
            
            if data.cp_ville:
                cp, ville = self.parse_cp_ville(data.cp_ville)
                c.drawString(coordinates['cp_ville'][0], coordinates['cp_ville'][1], f"{cp} {ville}")
                c.drawString(coordinates['cp_ville'][0] + 200, coordinates['cp_ville'][1], "France")
            
            if data.marque_modele:
                c.drawString(coordinates['marque'][0], coordinates['marque'][1], data.marque_modele)
            
            if data.immatriculation:
                c.drawString(coordinates['immatriculation'][0], coordinates['immatriculation'][1], data.immatriculation)
            
            # Date et lieu
            from datetime import datetime
            today = datetime.now()
            c.drawString(coordinates['lieu_signature'][0], coordinates['lieu_signature'][1], "Chartres")
            c.drawString(coordinates['date_signature'][0], coordinates['date_signature'][1], today.strftime('%d/%m/%Y'))
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            raise Exception(f"Erreur génération PDF: {str(e)}")
    
    def parse_cp_ville(self, cp_ville: str) -> tuple:
        if not cp_ville:
            return "", ""
        parts = cp_ville.split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return cp_ville, ""

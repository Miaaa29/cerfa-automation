from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
import io
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.page_width, self.page_height = A4
    
    def fill_cerfa(self, pdf_data: bytes, data) -> bytes:  # ✅ Bon nom de méthode
        """
        Remplit le CERFA 13757 en superposant le texte sur le PDF original
        """
        try:
            logger.info("Remplissage du PDF original avec superposition")
            
            # Lire le PDF original
            original_pdf = PdfReader(io.BytesIO(pdf_data))
            writer = PdfWriter()
            
            # Créer le calque de texte
            text_layer = self._create_text_layer(data)
            text_pdf = PdfReader(io.BytesIO(text_layer))
            
            # Superposer le texte sur chaque page
            for page_num in range(len(original_pdf.pages)):
                original_page = original_pdf.pages[page_num]
                
                # Superposer le texte si c'est la première page
                if page_num == 0 and len(text_pdf.pages) > 0:
                    original_page.merge_page(text_pdf.pages[0])
                
                writer.add_page(original_page)
            
            # Générer le PDF final
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            raise Exception(f"Erreur génération PDF: {str(e)}")
    
    def _create_text_layer(self, data):
        """Crée un calque transparent avec le texte"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Police et couleur
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0, 0, 0)  # Noir
        
        # SECTION MANDANT - Coordonnées ajustées
        if data.nom_prenom:
            # Après "Je soussigné(e),"
            c.drawString(160, 720, data.nom_prenom)
        
        if data.adresse:
            # Ligne "domicilié(e) à :"
            c.drawString(125, 698, data.adresse)
        
        if data.cp_ville:
            # Code postal et ville
            cp, ville = self.parse_cp_ville(data.cp_ville)
            c.drawString(125, 680, f"{cp} {ville}")
            # Pays
            c.drawString(325, 680, "France")
        
        # SECTION VÉHICULE
        if data.marque_modele:
            # Après "Marque :"
            c.drawString(205, 520, data.marque_modele)
        
        if data.immatriculation:
            # Après "Numéro d'immatriculation :"
            c.drawString(325, 485, data.immatriculation)
        
        # SECTION SIGNATURE
        from datetime import datetime
        today = datetime.now()
        
        # "Fait à"
        c.drawString(150, 200, "Chartres")
        
        # Date
        c.drawString(350, 200, today.strftime('%d/%m/%Y'))
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def parse_cp_ville(self, cp_ville: str) -> tuple:
        """Parse le code postal et la ville"""
        if not cp_ville:
            return "", ""
        parts = cp_ville.split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return cp_ville, ""

import io
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
from typing import Optional

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
    
    def fill_cerfa_13757(self, data, pdf_bytes: bytes):
        """
        Remplit le CERFA 13757 avec les données mappées
        """
        try:
            # Lire le PDF original
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            
            # Créer un overlay avec les données
            overlay_buffer = self._create_overlay(data)
            overlay_reader = PdfReader(overlay_buffer)
            
            # Fusionner chaque page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                
                # Ajouter l'overlay sur la première page
                if page_num == 0 and len(overlay_reader.pages) > 0:
                    page.merge_page(overlay_reader.pages[0])
                
                pdf_writer.add_page(page)
            
            # Générer le PDF final
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
            # Fallback: créer un PDF simple
            return self._create_simple_pdf(data)
    
    def _create_overlay(self, data):
        """
        Créer un overlay transparent avec les données
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Positions approximatives pour le CERFA 13757
        # Ces positions peuvent être ajustées selon le PDF réel
        
        # Mandant - NOM PRÉNOM
        if data.nom_prenom:
            c.setFont("Helvetica", 10)
            c.drawString(150, 700, data.nom_prenom)  # Position à ajuster
        
        # Mandant - Adresse
        if data.adresse:
            c.setFont("Helvetica", 10)
            c.drawString(150, 670, data.adresse)  # Position à ajuster
        
        # Mandant - Code postal + Ville
        if data.cp_ville:
            c.setFont("Helvetica", 10)
            cp, ville = self.parse_cp_ville(data.cp_ville)
            c.drawString(150, 640, cp)  # Code postal
            c.drawString(250, 640, ville)  # Ville
        
        # Véhicule - Marque
        if data.marque_modele:
            c.setFont("Helvetica", 10)
            c.drawString(150, 500, data.marque_modele)  # Position à ajuster
        
        # Véhicule - Immatriculation
        if data.immatriculation:
            c.setFont("Helvetica", 10)
            c.drawString(150, 450, data.immatriculation)  # Position à ajuster
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _create_simple_pdf(self, data):
        """
        Créer un PDF simple en cas d'erreur
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Titre
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 750, "CERFA 13757*03 - MANDAT POUR FORMALITÉS D'IMMATRICULATION")
        
        # Section Mandant
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 700, "MANDANT:")
        
        c.setFont("Helvetica", 10)
        y_position = 680
        
        if data.nom_prenom:
            c.drawString(70, y_position, f"NOM, PRÉNOM: {data.nom_prenom}")
            y_position -= 20
        
        if data.adresse:
            c.drawString(70, y_position, f"Adresse: {data.adresse}")
            y_position -= 20
        
        if data.cp_ville:
            c.drawString(70, y_position, f"Code postal, Commune: {data.cp_ville}")
            y_position -= 20
        
        # Pays par défaut
        c.drawString(70, y_position, "Pays: France")
        y_position -= 40
        
        # Section Véhicule
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "VÉHICULE CONCERNÉ:")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        if data.marque_modele:
            c.drawString(70, y_position, f"Marque: {data.marque_modele}")
            y_position -= 20
        
        if data.immatriculation:
            c.drawString(70, y_position, f"Numéro d'immatriculation: {data.immatriculation}")
            y_position -= 20
        
        # Section obligation d'assurance
        y_position -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_position, "IMPORTANT:")
        y_position -= 15
        c.setFont("Helvetica", 9)
        c.drawString(50, y_position, "Je suis informé(e) que pour circuler avec ce véhicule")
        y_position -= 12
        c.drawString(50, y_position, "je suis dans l'obligation de l'assurer préalablement")
        y_position -= 12
        c.drawString(50, y_position, "(articles L. 324-1 et L. 324-2 du code de la route).")
        
        # Date et signature
        y_position -= 40
        c.setFont("Helvetica", 10)
        c.drawString(50, y_position, "Fait à: _________________, le: ___/___/______")
        y_position -= 40
        c.drawString(50, y_position, "Signature:")
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    def parse_cp_ville(self, cp_ville: str) -> tuple:
        """
        Sépare le code postal et la ville
        Exemple: "75001 Paris" -> ("75001", "Paris")
        """
        if not cp_ville:
            return "", ""
        
        parts = cp_ville.split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return cp_ville, ""

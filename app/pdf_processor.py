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
    
    def fill_cerfa_13757(self, data):
        """
        Remplit le CERFA 13757 avec les données mappées
        """
        try:
            # Créer un PDF avec les données
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
            
            # Case opposition
            y_position -= 60
            c.setFont("Helvetica", 8)
            c.drawString(50, y_position, "☐ Je m'oppose à la réutilisation de mes données personnelles")
            y_position -= 10
            c.drawString(50, y_position, "à des fins de prospection commerciale")
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF: {str(e)}")
            raise Exception(f"Erreur génération PDF: {str(e)}")
    
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

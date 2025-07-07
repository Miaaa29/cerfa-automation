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
            logger.info("Génération du PDF avec positionnement optimisé")
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Position de base (en partant du bas de la page)
            base_y = self.page_height - 80*mm  # Position du premier champ
            
            # SECTION MANDANT (Je soussigné)
            if data.nom_prenom:
                # Nom et prénom - position après "Je soussigné(e),"
                c.setFont("Helvetica", 10)
                c.drawString(55*mm, base_y, data.nom_prenom)
            
            # Adresse complète
            if data.adresse:
                # Adresse - ligne "domicilié(e) à :"
                address_y = base_y - 12*mm
                c.drawString(45*mm, address_y, data.adresse)
                
                # Code postal et ville sur la ligne suivante
                if data.cp_ville:
                    cp, ville = self.parse_cp_ville(data.cp_ville)
                    cp_ville_y = address_y - 6*mm
                    c.drawString(45*mm, cp_ville_y, f"{cp} {ville}")
                    # Pays à droite
                    c.drawString(140*mm, cp_ville_y, "France")
            
            # SECTION MANDATAIRE (donne mandat à)
            # Laisser vide car c'est le professionnel qui recevra le mandat
            
            # SECTION VÉHICULE
            vehicle_y = base_y - 50*mm  # Position section véhicule
            
            if data.marque_modele:
                # Marque - après "Marque :"
                c.drawString(70*mm, vehicle_y, data.marque_modele)
            
            if data.immatriculation:
                # Numéro d'immatriculation - après "Numéro d'immatriculation :"
                immat_y = vehicle_y - 12*mm
                c.drawString(120*mm, immat_y, data.immatriculation)
            
            # Section signature
            signature_y = base_y - 140*mm
            
            # Date par défaut (aujourd'hui)
            from datetime import datetime
            today = datetime.now()
            
            # "Fait à" et date
            c.drawString(50*mm, signature_y, "Chartres")  # Exemple de ville
            c.drawString(140*mm, signature_y, f"{today.strftime('%d/%m/%Y')}")
            
            # Finaliser le PDF
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

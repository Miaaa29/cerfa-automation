from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        """Initialize PDF processor with default settings"""
        self.default_font_size = 10
        self.default_font_name = "Helvetica"
        
    def detect_form_fields(self, pdf_bytes):
        """🎯 Détecte tous les champs de formulaire dans le PDF"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            fields_info = {
                "has_fields": False,
                "count": 0,
                "fields": []
            }
            
            logger.info("🔍 Analyse des champs de formulaire...")
            
            # Vérifier s'il y a un AcroForm
            if "/AcroForm" in reader.trailer["/Root"]:
                acro_form = reader.trailer["/Root"]["/AcroForm"]
                logger.info("✅ AcroForm détecté")
                
                if "/Fields" in acro_form:
                    fields = acro_form["/Fields"]
                    fields_info["has_fields"] = True
                    fields_info["count"] = len(fields)
                    
                    logger.info(f"📋 {len(fields)} champs trouvés")
                    
                    for i, field in enumerate(fields):
                        try:
                            field_obj = field.get_object()
                            field_name = field_obj.get("/T", f"Champ_{i}")
                            field_type = field_obj.get("/FT", "Inconnu")
                            field_value = field_obj.get("/V", "")
                            
                            # Décoder le nom si c'est en bytes
                            if hasattr(field_name, 'decode'):
                                field_name = field_name.decode('utf-8', errors='ignore')
                            
                            field_info = {
                                "name": str(field_name),
                                "type": str(field_type),
                                "value": str(field_value),
                                "index": i
                            }
                            
                            fields_info["fields"].append(field_info)
                            logger.info(f"  [{i}] {field_name} ({field_type})")
                            
                        except Exception as field_error:
                            logger.warning(f"⚠️ Erreur champ {i}: {field_error}")
                            
                else:
                    logger.info("❌ Pas de champs dans AcroForm")
            else:
                logger.info("❌ Pas d'AcroForm dans le PDF")
                
            return fields_info
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse champs: {e}")
            return {
                "has_fields": False, 
                "count": 0, 
                "fields": [], 
                "error": str(e)
            }
    
    def fill_form_fields(self, pdf_bytes, data):
        """🎯 Remplit les champs de formulaire existants"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            
            # Mapping des champs (à adapter selon les noms réels)
            field_mapping = {
                # Données personnelles
                "nom_prenom": data.nom_prenom or "",
                "nom": data.nom_prenom or "",
                "prenom": data.nom_prenom or "",
                "adresse": data.adresse or "",
                "cp_ville": data.cp_ville or "",
                "date_naissance": data.date_naissance or "",
                "ville_naissance": data.ville_naissance or "",
                "mail": data.mail or "",
                "telephone": data.telephone or "",
                
                # Données véhicule
                "immatriculation": data.immatriculation or "",
                "date_1er_immatriculation": data.date_1er_immatriculation or "",
                "marque_modele": data.marque_modele or "",
                "numero_formule": data.numero_formule or "",
                
                # Variantes possibles des noms de champs
                "Nom prenom": data.nom_prenom or "",
                "Adresse": data.adresse or "",
                "CP VILLE": data.cp_ville or "",
                "Date de naissance": data.date_naissance or "",
                "Ville de naissance": data.ville_naissance or "",
                "Mail": data.mail or "",
                "Telephone": data.telephone or "",
                "Immatriculation": data.immatriculation or "",
                "Date 1er immatriculation": data.date_1er_immatriculation or "",
                "Marque modele": data.marque_modele or "",
                "Numero de formule": data.numero_formule or "",
            }
            
            # Copier les pages
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                writer.add_page(page)
            
            # Remplir les champs
            if "/AcroForm" in reader.trailer["/Root"]:
                for page_num in range(len(writer.pages)):
                    writer.update_page_form_field_values(
                        writer.pages[page_num], 
                        field_mapping
                    )
                    
            logger.info("✅ Champs de formulaire remplis")
            
            # Générer le PDF
            output = io.BytesIO()
            writer.write(output)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Erreur remplissage champs: {e}")
            # Fallback vers la méthode overlay
            return self.fill_cerfa_overlay(pdf_bytes, data)
    
    def fill_cerfa_overlay(self, pdf_bytes, data):
        """🎯 Méthode overlay (position fixe) en fallback"""
        try:
            # Positions des champs sur le CERFA (à ajuster selon votre PDF)
            positions = {
                "nom_prenom": (95, 710),
                "adresse": (95, 690),
                "cp_ville": (95, 670),
                "date_naissance": (95, 650),
                "ville_naissance": (95, 630),
                "mail": (95, 610),
                "telephone": (95, 590),
                "immatriculation": (95, 570),
                "date_1er_immatriculation": (95, 550),
                "marque_modele": (95, 530),
                "numero_formule": (95, 510)
            }
            
            # Créer un overlay avec les données
            overlay_buffer = io.BytesIO()
            overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=A4)
            
            # Ajouter les textes
            overlay_canvas.setFont("Helvetica", 10)
            
            if data.nom_prenom:
                overlay_canvas.drawString(positions["nom_prenom"][0], positions["nom_prenom"][1], data.nom_prenom)
            if data.adresse:
                overlay_canvas.drawString(positions["adresse"][0], positions["adresse"][1], data.adresse)
            if data.cp_ville:
                overlay_canvas.drawString(positions["cp_ville"][0], positions["cp_ville"][1], data.cp_ville)
            if data.date_naissance:
                overlay_canvas.drawString(positions["date_naissance"][0], positions["date_naissance"][1], data.date_naissance)
            if data.ville_naissance:
                overlay_canvas.drawString(positions["ville_naissance"][0], positions["ville_naissance"][1], data.ville_naissance)
            if data.mail:
                overlay_canvas.drawString(positions["mail"][0], positions["mail"][1], data.mail)
            if data.telephone:
                overlay_canvas.drawString(positions["telephone"][0], positions["telephone"][1], data.telephone)
            if data.immatriculation:
                overlay_canvas.drawString(positions["immatriculation"][0], positions["immatriculation"][1], data.immatriculation)
            if data.date_1er_immatriculation:
                overlay_canvas.drawString(positions["date_1er_immatriculation"][0], positions["date_1er_immatriculation"][1], data.date_1er_immatriculation)
            if data.marque_modele:
                overlay_canvas.drawString(positions["marque_modele"][0], positions["marque_modele"][1], data.marque_modele)
            if data.numero_formule:
                overlay_canvas.drawString(positions["numero_formule"][0], positions["numero_formule"][1], data.numero_formule)
            
            overlay_canvas.save()
            overlay_buffer.seek(0)
            
            # Fusionner avec le PDF original
            original_pdf = PdfReader(io.BytesIO(pdf_bytes))
            overlay_pdf = PdfReader(overlay_buffer)
            
            writer = PdfWriter()
            
            # Fusionner la première page
            original_page = original_pdf.pages[0]
            overlay_page = overlay_pdf.pages[0]
            original_page.merge_page(overlay_page)
            writer.add_page(original_page)
            
            # Ajouter les autres pages s'il y en a
            for i in range(1, len(original_pdf.pages)):
                writer.add_page(original_pdf.pages[i])
            
            # Générer le PDF final
            output = io.BytesIO()
            writer.write(output)
            
            logger.info("✅ PDF généré avec méthode overlay")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Erreur méthode overlay: {e}")
            raise Exception(f"Erreur lors de la génération du PDF: {str(e)}")
    
    def fill_cerfa(self, pdf_bytes, data):
        """🎯 Méthode principale : essaie d'abord les champs, puis l'overlay"""
        try:
            # Vérifier s'il y a des champs de formulaire
            fields_info = self.detect_form_fields(pdf_bytes)
            
            if fields_info["has_fields"]:
                logger.info("🎯 Utilisation des champs de formulaire")
                return self.fill_form_fields(pdf_bytes, data)
            else:
                logger.info("🎯 Utilisation de la méthode overlay")
                return self.fill_cerfa_overlay(pdf_bytes, data)
                
        except Exception as e:
            logger.error(f"❌ Erreur fill_cerfa: {e}")
            raise Exception(f"Erreur lors du remplissage: {str(e)}")

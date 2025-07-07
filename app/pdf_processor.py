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
                            logger.info(f"   📝 Champ {i}: {field_name} ({field_type})")
                            
                        except Exception as e:
                            logger.error(f"❌ Erreur champ {i}: {e}")
                            
                else:
                    logger.info("❌ Pas de champs dans AcroForm")
            else:
                logger.info("❌ Pas d'AcroForm dans le PDF")
                
            return fields_info
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse champs: {e}")
            return {"has_fields": False, "count": 0, "fields": [], "error": str(e)}
    
    def fill_form_fields(self, pdf_bytes, data):
        """🎯 Remplit les champs natifs du PDF"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            
            # Mapping des données vers les champs du PDF
            field_mapping = {
                # Vous devrez adapter ces noms selon les vrais noms des champs
                "nom_prenom": data.nom_prenom,
                "adresse": data.adresse,
                "cp_ville": data.cp_ville,
                "date_naissance": data.date_naissance,
                "ville_naissance": data.ville_naissance,
                "mail": data.mail,
                "telephone": data.telephone,
                "immatriculation": data.immatriculation,
                "date_1er_immatriculation": data.date_1er_immatriculation,
                "marque_modele": data.marque_modele,
                "numero_formule": data.numero_formule
            }
            
            # Remplir les champs
            for page in reader.pages:
                if "/Annots" in page:
                    for annot in page["/Annots"]:
                        annotation = annot.get_object()
                        if "/T" in annotation:
                            field_name = str(annotation["/T"])
                            if field_name in field_mapping and field_mapping[field_name]:
                                annotation.update({"/V": field_mapping[field_name]})
                
                writer.add_page(page)
            
            # Générer le PDF
            output = io.BytesIO()
            writer.write(output)
            
            logger.info("✅ PDF généré avec champs de formulaire")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Erreur remplissage champs: {e}")
            raise Exception(f"Erreur lors du remplissage des champs: {str(e)}")
    
    def fill_cerfa_overlay(self, pdf_bytes, data):
        """🎯 Remplit le CERFA avec VOS coordonnées exactes"""
        try:
            logger.info("🎯 Génération du PDF avec overlay - VOS coordonnées")
            
            # Créer le calque overlay
            overlay_buffer = io.BytesIO()
            overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=A4)
            overlay_canvas.setFont("Helvetica", 10)
            
            # 🎯 VOS COORDONNÉES EXACTES
            if data.nom_prenom:
                overlay_canvas.drawString(268, 684, data.nom_prenom)
                logger.info(f"✅ Nom/Prénom: {data.nom_prenom} -> (268, 684)")
            
            if data.adresse:
                overlay_canvas.drawString(443, 633, data.adresse)
                logger.info(f"✅ Adresse: {data.adresse} -> (443, 633)")
            
            if data.cp_ville:
                overlay_canvas.drawString(287, 591, data.cp_ville)
                logger.info(f"✅ CP/Ville: {data.cp_ville} -> (287, 591)")
            
            if data.marque_modele:
                overlay_canvas.drawString(243, 420, data.marque_modele)
                logger.info(f"✅ Marque/Modèle: {data.marque_modele} -> (243, 420)")
            
            if data.immatriculation:
                overlay_canvas.drawString(305, 324, data.immatriculation)
                logger.info(f"✅ Immatriculation: {data.immatriculation} -> (305, 324)")
            
            # 🎯 AJOUT DES AUTRES CHAMPS (estimés)
            if data.date_naissance:
                overlay_canvas.drawString(200, 650, data.date_naissance)
                logger.info(f"✅ Date naissance: {data.date_naissance} -> (200, 650)")
            
            if data.ville_naissance:
                overlay_canvas.drawString(350, 650, data.ville_naissance)
                logger.info(f"✅ Ville naissance: {data.ville_naissance} -> (350, 650)")
            
            if data.mail:
                overlay_canvas.drawString(200, 610, data.mail)
                logger.info(f"✅ Mail: {data.mail} -> (200, 610)")
            
            if data.telephone:
                overlay_canvas.drawString(200, 570, data.telephone)
                logger.info(f"✅ Téléphone: {data.telephone} -> (200, 570)")
            
            if data.date_1er_immatriculation:
                overlay_canvas.drawString(200, 380, data.date_1er_immatriculation)
                logger.info(f"✅ Date 1ère immat: {data.date_1er_immatriculation} -> (200, 380)")
            
            if data.numero_formule:
                overlay_canvas.drawString(200, 340, data.numero_formule)
                logger.info(f"✅ Numéro formule: {data.numero_formule} -> (200, 340)")
            
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
            
            logger.info("✅ PDF généré avec overlay - VOS coordonnées")
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
                logger.info("🎯 Utilisation de la méthode overlay avec VOS coordonnées")
                return self.fill_cerfa_overlay(pdf_bytes, data)
                
        except Exception as e:
            logger.error(f"❌ Erreur fill_cerfa: {e}")
            raise Exception(f"Erreur lors du remplissage: {str(e)}")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import json
import logging
from .pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CERFA 13757 Automation", version="1.0.0")

class CerfaData(BaseModel):
    nom_prenom: Optional[str] = None
    adresse: Optional[str] = None
    cp_ville: Optional[str] = None
    date_naissance: Optional[str] = None
    ville_naissance: Optional[str] = None
    mail: Optional[str] = None
    telephone: Optional[str] = None
    immatriculation: Optional[str] = None
    date_1er_immatriculation: Optional[str] = None
    marque_modele: Optional[str] = None
    numero_formule: Optional[str] = None

    @classmethod
    def from_n8n_data(cls, data: dict):
        """Convertit les données de n8n vers notre modèle"""
        return cls(
            nom_prenom=data.get("Nom prenom"),
            adresse=data.get("Adresse"),
            cp_ville=data.get("CP VILLE"),
            date_naissance=data.get("Date de naissance"),
            ville_naissance=data.get("Ville de naissance"),
            mail=data.get("Mail"),
            telephone=data.get("Telephone"),
            immatriculation=data.get("Immatriculation "),  # Attention à l'espace
            date_1er_immatriculation=data.get("Date 1er immatriculation"),
            marque_modele=data.get("Marque modele"),
            numero_formule=data.get("Numero de formule")
        )

@app.get("/")
async def root():
    return {"message": "CERFA 13757 Automation API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cerfa-automation"}

@app.post("/fill-cerfa")
async def fill_cerfa(
    pdf_file: UploadFile = File(...),
    data: str = Form(...)
):
    """
    Remplit le CERFA 13757 avec les données reçues de n8n
    Reçoit: PDF vierge + données JSON
    """
    try:
        logger.info(f"Réception du fichier: {pdf_file.filename}")
        logger.info(f"Données reçues: {data}")
        
        # Vérifier que c'est un PDF
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
        
        # Lire le PDF
        pdf_bytes = await pdf_file.read()
        logger.info(f"PDF lu: {len(pdf_bytes)} bytes")
        
        # Parser les données JSON
        try:
            json_data = json.loads(data)
            if isinstance(json_data, list) and len(json_data) > 0:
                json_data = json_data[0]  # Prendre le premier élément
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Format JSON invalide")
        
        # Mapper les données
        cerfa_data = CerfaData.from_n8n_data(json_data)
        logger.info(f"Données mappées: {cerfa_data}")
        
        # Traiter le PDF
        processor = PDFProcessor()
        filled_pdf_bytes = processor.fill_cerfa(pdf_bytes, cerfa_data)
        
        # Retourner le PDF rempli
        return StreamingResponse(
            io.BytesIO(filled_pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cerfa_13757_rempli.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/test-mapping")
async def test_mapping(raw_data: List[dict]):
    """
    Test le mapping des données sans générer le PDF
    """
    try:
        if not raw_data or len(raw_data) == 0:
            raise HTTPException(status_code=400, detail="Aucune donnée reçue")
        
        data = CerfaData.from_n8n_data(raw_data[0])
        
        return {
            "mapping_reussi": True,
            "donnees_mappees": {
                "mandant_nom": data.nom_prenom,
                "mandant_adresse": data.adresse,
                "mandant_cp_ville": data.cp_ville,
                "vehicule_marque": data.marque_modele,
                "vehicule_immatriculation": data.immatriculation
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du test mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/detect-fields")
async def detect_fields(pdf_file: UploadFile = File(...)):
    """
    🎯 NOUVELLE ROUTE : Détecte les champs de formulaire dans le PDF
    """
    try:
        logger.info(f"Analyse des champs pour: {pdf_file.filename}")
        
        # Vérifier que c'est un PDF
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
        
        # Lire le PDF
        pdf_bytes = await pdf_file.read()
        logger.info(f"PDF lu: {len(pdf_bytes)} bytes")
        
        # Analyser les champs
        processor = PDFProcessor()
        fields_info = processor.detect_form_fields(pdf_bytes)
        
        return {
            "filename": pdf_file.filename,
            "has_form_fields": fields_info["has_fields"],
            "fields_count": fields_info["count"],
            "fields_list": fields_info["fields"]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

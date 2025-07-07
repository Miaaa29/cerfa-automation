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
            immatriculation=data.get("Immatriculation "),
            date_1er_immatriculation=data.get("Date 1er immatriculation"),
            marque_modele=data.get("Marque modele"),
            numero_formule=data.get("Numero de formule")
        )

@app.get("/")
async def root():
    return {"message": "CERFA 13757 Automation API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cerfa-automation"}

@app.post("/fill-cerfa")
async def fill_cerfa_endpoint(
    pdf_file: UploadFile = File(...),
    data: str = Form(...)
):
    """
    Endpoint pour remplir le CERFA 13757
    """
    try:
        logger.info("Début du traitement du CERFA")
        
        # Lire le fichier PDF
        pdf_bytes = await pdf_file.read()
        logger.info(f"PDF reçu: {len(pdf_bytes)} bytes")
        
        # Parser les données JSON
        try:
            json_data = json.loads(data)
            if isinstance(json_data, list) and json_data:
                form_data = json_data[0]
            else:
                form_data = json_data
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            raise HTTPException(status_code=400, detail=f"Format JSON invalide: {str(e)}")
        
        # Convertir en objet CerfaData
        cerfa_data = CerfaData.from_n8n_data(form_data)
        logger.info(f"Données converties: {cerfa_data.dict()}")
        
        # Traiter le PDF
        processor = PDFProcessor()
        pdf_content = processor.fill_cerfa(pdf_bytes, cerfa_data)  # ✅ Nom corrigé
        
        # Retourner le PDF rempli
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cerfa_13757_rempli.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/test-mapping")
async def test_mapping(data: List[dict]):
    """
    Endpoint pour tester le mapping des données
    """
    try:
        results = []
        for item in data:
            cerfa_data = CerfaData.from_n8n_data(item)
            results.append({
                "original": item,
                "mapped": cerfa_data.dict()
            })
        
        return {"mapping_results": results}
        
    except Exception as e:
        logger.error(f"Erreur test mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

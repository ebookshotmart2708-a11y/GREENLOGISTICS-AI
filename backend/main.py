"""
GREENLOGISTICS AI - Backend API
API para análisis de documentos logísticos usando Claude AI.
Versión simplificada y corregida - SIN errores de 'proxies'
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import anthropic
import os
from dotenv import load_dotenv
import tempfile
import PyPDF2
import asyncio
from typing import Optional
import logging
from datetime import datetime

# ==================== CONFIGURACIÓN ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="GREENLOGISTICS AI API",
    description="API para análisis inteligente de documentos de logística internacional",
    version="3.0.0"
)

# Permitir conexiones desde tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Inicializar cliente Anthropic CORRECTAMENTE (sin 'proxies')
client = None
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "sk-ant-tu_clave_aqui":
    try:
        # ✅ FORMA CORRECTA - Solo la API key
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Cliente Anthropic inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando Anthropic: {e}")
        client = None
else:
    logger.info("Modo demo activado")

# ==================== PROMPT DE IA ====================

SYSTEM_PROMPT = """Eres GREENLOGISTICS AI, un asesor digital senior especializado en logística internacional.

REGLAS:
1. Responde en el idioma especificado (ES, EN, FR, DE)
2. Solo usa información del documento proporcionado
3. No inventes datos
4. Si algo no está especificado, dilo claramente

ANÁLISIS OBLIGATORIO:
1. Comprensión de la operación
2. Diagnóstico de riesgos (logísticos, aduaneros, fiscales, ambientales)
3. Recomendaciones estratégicas
4. Plan de acción

Sé conciso y profesional. Tu valor está en insights accionables."""

# ==================== FUNCIONES ====================

def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de PDF."""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error PDF: {str(e)}")

async def process_uploaded_file(file: UploadFile) -> str:
    """Procesa archivo subido."""
    document_text = ""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        if file.filename.lower().endswith('.pdf'):
            document_text = extract_text_from_pdf(tmp_path)
        else:
            document_text = content.decode('utf-8', errors='ignore')
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    return document_text

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "service": "GREENLOGISTICS AI API",
        "version": "3.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze (POST)"
        }
    }

@app.get("/api/health")
async def health_check():
    """Endpoint de salud - MUY IMPORTANTE"""
    return {
        "status": "healthy",
        "service": "GREENLOGISTICS AI API",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "ai_available": client is not None
    }

@app.post("/api/analyze")
async def analyze_document(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language: str = Form("ES")
):
    """
    Analiza documentos logísticos.
    """
    try:
        # 1. Obtener texto
        document_text = ""
        if file:
            document_text = await process_uploaded_file(file)
        elif text:
            document_text = text.strip()
        else:
            raise HTTPException(status_code=400, detail="Proporcione archivo o texto")
        
        if not document_text:
            raise HTTPException(status_code=400, detail="Documento vacío")
        
        logger.info(f"Documento: {len(document_text)} chars, idioma: {language}")
        
        # 2. Si no hay API key, devolver demo
        if client is None:
            return JSONResponse({
                "success": True,
                "analysis": f"""
📊 GREENLOGISTICS AI - DEMO
Documento analizado: {len(document_text)} caracteres
Idioma: {language}

💡 Este es el modo demostración. Para análisis con IA real:
1. Configure ANTHROPIC_API_KEY en Render.com
2. La aplicación se actualizará automáticamente
3. Podrá analizar documentos con Claude AI

🔗 Backend funcionando correctamente en Render.
                """,
                "metadata": {"mode": "demo"}
            })
        
        # 3. Llamar a Claude AI
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.1,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Idioma: {language}\n\nDocumento:\n{document_text}"
            }]
        )
        
        # 4. Retornar resultado
        return JSONResponse({
            "success": True,
            "analysis": response.content[0].text,
            "metadata": {
                "model": "claude-3-haiku",
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== INICIAR ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

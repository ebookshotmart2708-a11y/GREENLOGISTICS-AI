"""
GREENLOGISTICS AI - Backend API
API principal para análisis de documentos logísticos usando Claude AI.
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

# ==================== CONFIGURACIÓN INICIAL ====================

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Inicializar aplicación FastAPI
app = FastAPI(
    title="GREENLOGISTICS AI API",
    description="API para análisis inteligente de documentos de logística internacional",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS (permite comunicación desde tu frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: ["https://tudominio.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verificar API key de Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY no encontrada en variables de entorno")
    # No lanzamos error para permitir modo demo

# Inicializar cliente de Anthropic (Claude) si hay API key
client = None
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "sk-ant-tu_clave_aqui":
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Cliente Anthropic inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando Anthropic: {e}")
        client = None

# ==================== PROMPT DE GREENLOGISTICS AI ====================

SYSTEM_PROMPT = """Eres GREENLOGISTICS AI, un asesor digital senior especializado en logística internacional, aduanas, fiscalidad y operaciones comerciales sostenibles alineadas con la UE.

════════════════════════════════════
LENGUAJE DE SALIDA (OBLIGATORIO)
════════════════════════════════════
- El usuario especificará el idioma (ES, EN, FR, DE).
- Responde ESTRICTAMENTE en ese idioma.

════════════════════════════════════
REGLA DE PRIMACÍA DOCUMENTAL (ABSOLUTA)
════════════════════════════════════
- El texto proporcionado es la ÚNICA fuente de verdad.
- NO uses información de conversaciones anteriores.
- NO inventes ubicaciones, productos o escenarios.
- Si algo no está en el documento: "[Elemento] no especificado".

════════════════════════════════════
VALIDACIÓN PREVIA AL ANÁLISIS
════════════════════════════════════
ANTES de analizar, DECLARA:

[CONTEXTO DOCUMENTAL]
1. PRODUCTO: [Ej: "Manzanas frescas - PERECEDERO/AGRÍCOLA"]
2. ORIGEN: [Ciudad, País] o "NO ESPECIFICADO"
3. DESTINO: [Ciudad, País] o "NO ESPECIFICADO"
4. OPERACIÓN: [Intra-UE / Importación Extra-UE / Exportación Extra-UE / Desconocida]
5. DATOS FALTANTES: [Listar: Incoterm, transporte, valor, peso, etc.]

════════════════════════════════════
FLUJO DE ANÁLISIS (OBLIGATORIO)
════════════════════════════════════
SIGUE ESTA SECUENCIA EXACTA:

1. COMPRENSIÓN DE LA OPERACIÓN
   - Resumen ejecutivo
   - Partes involucradas
   - Complejidad (Baja/Media/Alta)

2. DIAGNÓSTICO DE RIESGOS
   - Logísticos (tiempos, manipulación)
   - Aduaneros/Regulatorios (documentación, certificados)
   - Fiscales (IVA, aranceles)
   - Ambientales (CO2, packaging)

3. EVALUACIÓN DE ESCENARIOS
   - Escenario Base (según datos)
   - Escenario Optimizado (recomendaciones)
   - Comparativa cuando sea posible estimar

4. RECOMENDACIÓN ESTRATÉGICA
   - Mejor opción operativa
   - Justificación riesgo/costo/sostenibilidad

5. PLAN DE ACCIÓN
   - Inmediato (48h)
   - Preparatorio (1-2 semanas)
   - Estratégico (1-3 meses)

════════════════════════════════════
INSIGHT DEL ASESOR (POR SECCIÓN)
════════════════════════════════════
- Máximo 3 frases por sección
- Tono profesional y directo
- Enfocado en lo que más importa para la decisión

════════════════════════════════════
REGISTRO DE DECISIÓN
════════════════════════════════════
Resumir en 4 puntos:
- Escenario elegido y por qué
- Riesgos aceptados
- Acciones diferidas
- Siguiente revisión recomendada

════════════════════════════════════
PROHIBICIONES EXPLÍCITAS
════════════════════════════════════
- NO asumas Incoterms no especificados
- NO asumas modos de transporte no especificados
- Para cálculos estimados, DECLARA la fórmula y supuestos
- Esto es soporte para decisiones, NO ejecución
"""

# ==================== FUNCIONES AUXILIARES ====================

def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de un archivo PDF."""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        logger.info(f"PDF procesado: {len(text)} caracteres extraídos")
    except Exception as e:
        logger.error(f"Error extrayendo texto de PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error leyendo PDF: {str(e)}")
    return text.strip()

def extract_text_from_txt(file_path: str) -> str:
    """Extrae texto de un archivo TXT."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        logger.info(f"TXT procesado: {len(text)} caracteres")
        return text
    except Exception as e:
        logger.error(f"Error leyendo TXT: {e}")
        raise HTTPException(status_code=400, detail=f"Error leyendo archivo de texto: {str(e)}")

async def process_uploaded_file(file: UploadFile) -> str:
    """Procesa un archivo subido y extrae su texto."""
    document_text = ""
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Extraer texto según tipo de archivo
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith('.pdf'):
            document_text = extract_text_from_pdf(tmp_path)
        elif filename_lower.endswith(('.txt', '.doc', '.docx')):
            document_text = extract_text_from_txt(tmp_path)
        else:
            # Intentar leer como texto plano
            document_text = content.decode('utf-8', errors='ignore')
            logger.info(f"Archivo genérico procesado: {len(document_text)} caracteres")
        
        if not document_text.strip():
            raise HTTPException(status_code=400, detail="El documento está vacío o no se pudo extraer texto")
            
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    return document_text

def get_demo_response(document_text: str, language: str) -> dict:
    """Genera una respuesta de demostración cuando no hay API key."""
    return {
        "success": True,
        "analysis": f"""
🌍 GREENLOGISTICS AI - ANÁLISIS DE DEMOSTRACIÓN

📋 CONTEXTO DOCUMENTAL (MODO DEMO):
• Documento recibido: {len(document_text)} caracteres
• Idioma de análisis: {language}
• Modo: Demostración (API key no configurada)

🔍 COMPRENSIÓN DE LA OPERACIÓN:
Documento detectado correctamente. Para un análisis real con IA:
1. Configura ANTHROPIC_API_KEY en Render.com
2. Recarga la aplicación
3. Sube un documento real de logística

💡 INSIGHT DEL ASESOR:
Esta demostración muestra la arquitectura funcional. El siguiente paso es integrar Claude AI para análisis de:
• Clasificación arancelaria automática
• Optimización de Incoterms
• Evaluación de riesgos aduaneros
• Cálculo de huella de carbono

✅ PLAN DE ACCIÓN:
1. INMEDIATO: Configurar API key en variables de entorno
2. PREPARATORIO: Probar con documentos reales de exportación
3. ESTRATÉGICO: Conectar con bases de datos de aranceles

📊 REGISTRO DE DECISIÓN:
• Escenario: Modo demostración activado
• Justificación: API key pendiente de configuración
• Riesgo: Análisis limitado a funcionalidad básica
• Siguiente: Configurar integración completa con Claude AI
""",
        "metadata": {
            "mode": "demo",
            "chars_processed": len(document_text),
            "language": language,
            "model": "none",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }

# ==================== ENDPOINTS DE LA API ====================

@app.get("/")
async def root():
    """Endpoint raíz - Información de la API."""
    return {
        "service": "GREENLOGISTICS AI API",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/api/docs",
        "health_check": "/api/health",
        "analyze_endpoint": "/api/analyze (POST)",
        "api_key_configured": ANTHROPIC_API_KEY is not None and ANTHROPIC_API_KEY != "sk-ant-tu_clave_aqui"
    }

@app.get("/api/health")
async def health_check():
    """Endpoint de verificación de salud."""
    return {
        "status": "healthy",
        "service": "GREENLOGISTICS AI API",
        "version": "2.0.0",
        "ai_available": client is not None,
        "timestamp": "2024-01-01T00:00:00Z"  # En producción usar datetime.now().isoformat()
    }

@app.post("/api/analyze")
async def analyze_document(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language: str = Form("ES")
):
    """
    Endpoint principal para analizar documentos logísticos.
    
    Acepta:
    - Archivo (PDF/TXT/DOC) o 
    - Texto directo
    
    Devuelve análisis estructurado por GREENLOGISTICS AI.
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        document_text = ""
        
        # 1. Obtener texto del documento
        if file:
            logger.info(f"Procesando archivo: {file.filename}, tipo: {file.content_type}")
            document_text = await process_uploaded_file(file)
        elif text:
            logger.info(f"Procesando texto directo: {len(text)} caracteres")
            document_text = text.strip()
        else:
            raise HTTPException(
                status_code=400, 
                detail="Debe proporcionar un archivo (file) o texto (text)"
            )
        
        if not document_text:
            raise HTTPException(status_code=400, detail="El documento está vacío")
        
        logger.info(f"Documento listo para análisis: {len(document_text)} caracteres, idioma: {language}")
        
        # 2. Si no hay cliente Anthropic configurado, devolver demo
        if client is None:
            logger.warning("Cliente Anthropic no disponible, usando modo demo")
            return JSONResponse(get_demo_response(document_text, language))
        
        # 3. Preparar mensaje para Claude
        user_message = f"""IDIOMA DE SALIDA: {language}

DOCUMENTO PARA ANALIZAR:
{document_text}

INSTRUCCIÓN: Analiza este documento siguiendo EL FLUJO COMPLETO especificado en el SYSTEM PROMPT.
"""
        
        # 4. Llamar a Claude API
        logger.info("Enviando solicitud a Claude API...")
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Modelo económico y rápido
            max_tokens=4000,
            temperature=0.1,  # Baja temperatura para respuestas consistentes
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # 5. Calcular tiempo de procesamiento
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # 6. Retornar análisis
        result = {
            "success": True,
            "analysis": response.content[0].text,
            "metadata": {
                "tokens_used": response.usage.input_tokens,
                "model": "claude-3-haiku-20240307",
                "language": language,
                "processing_time_seconds": round(processing_time, 2),
                "document_chars": len(document_text),
                "api_mode": "production"
            }
        }
        
        logger.info(f"Análisis completado en {processing_time:.2f}s, tokens: {response.usage.input_tokens}")
        return JSONResponse(result)
        
    except anthropic.APIError as e:
        logger.error(f"Error de API de Anthropic: {e}")
        raise HTTPException(
            status_code=502, 
            detail=f"Error en el servicio de IA: {str(e)}"
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP que ya manejamos
        raise
    except Exception as e:
        logger.error(f"Error interno inesperado: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )

# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo local
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
    🚀 GREENLOGISTICS AI API Iniciando...
    🌐 URL: http://{host}:{port}
    📚 Documentación: http://{host}:{port}/api/docs
    🩺 Health Check: http://{host}:{port}/api/health
    🔑 API Key configurada: {ANTHROPIC_API_KEY is not None and ANTHROPIC_API_KEY != "sk-ant-tu_clave_aqui"}
    """)
    
    uvicorn.run(app, host=host, port=port)

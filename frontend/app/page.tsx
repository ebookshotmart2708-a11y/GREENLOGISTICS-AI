'use client';

import { useState, useRef } from 'react';
import { Upload, FileText, Globe, AlertCircle, CheckCircle, Copy, Trash2 } from 'lucide-react';

export default function Home() {
  const [documentText, setDocumentText] = useState('');
  const [language, setLanguage] = useState('ES');
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const [apiStatus, setApiStatus] = useState<'unknown' | 'healthy' | 'unhealthy'>('unknown');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // URL de tu backend - IMPORTANTE: Cambia esta URL
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://greenlogistics-backend.onrender.com';

  // Verificar estado del backend
  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      if (response.ok) {
        setApiStatus('healthy');
        return true;
      }
    } catch (error) {
      setApiStatus('unhealthy');
    }
    return false;
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    
    // Leer archivo como texto
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setDocumentText(text);
    };
    reader.readAsText(file);
  };

  const handleAnalyze = async () => {
    if (!documentText.trim()) {
      alert('Por favor, sube un documento o ingresa texto para analizar.');
      return;
    }

    setLoading(true);
    setAnalysis('');

    const formData = new FormData();
    formData.append('text', documentText);
    formData.append('language', language);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        setAnalysis(data.analysis);
      } else {
        throw new Error(data.detail || 'Análisis fallido');
      }
    } catch (error) {
      console.error('Error:', error);
      setAnalysis(`❌ Error al analizar el documento:\n${error instanceof Error ? error.message : 'Error desconocido'}\n\n⚠️ Verifica:\n1. Que tu backend esté funcionando\n2. Que tengas configurada ANTHROPIC_API_KEY en Render\n3. Que la URL ${API_URL} sea correcta`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = () => {
    navigator.clipboard.writeText(documentText);
    alert('Texto copiado al portapapeles');
  };

  const handleCopyAnalysis = () => {
    navigator.clipboard.writeText(analysis);
    alert('Análisis copiado al portapapeles');
  };

  const handleClearAll = () => {
    setDocumentText('');
    setAnalysis('');
    setFileName('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Verificar backend al cargar
  useState(() => {
    checkBackendHealth();
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50 p-4 md:p-8">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">
              <span className="text-green-600">GREENLOGISTICS</span> AI
            </h1>
            <p className="text-gray-600 mt-2">
              Asesoría inteligente en logística internacional, aduanas y sostenibilidad
            </p>
            <div className="flex items-center gap-2 mt-3">
              <div className={`w-3 h-3 rounded-full ${apiStatus === 'healthy' ? 'bg-green-500' : apiStatus === 'unhealthy' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
              <span className="text-sm text-gray-600">
                Backend: {apiStatus === 'healthy' ? 'Conectado' : apiStatus === 'unhealthy' ? 'Desconectado' : 'Verificando...'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-full shadow-sm">
            <Globe className="w-5 h-5 text-green-600" />
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent border-none focus:outline-none text-gray-700"
            >
              <option value="ES">🇪🇸 Español</option>
              <option value="EN">🇬🇧 English</option>
              <option value="FR">🇫🇷 Français</option>
              <option value="DE">🇩🇪 Deutsch</option>
            </select>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        {/* Panel de entrada */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
              <FileText className="w-6 h-6 text-green-600" />
              Documento a Analizar
            </h2>
            {fileName && (
              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                📄 {fileName}
              </span>
            )}
          </div>

          {/* Área de subida de archivos */}
          <div className="mb-6">
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-green-500 transition-colors">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">
                Arrastra y suelta tu documento aquí, o haz clic para seleccionar
              </p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,.txt,.doc,.docx"
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-block bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors cursor-pointer"
              >
                Seleccionar Archivo
              </label>
              <p className="text-sm text-gray-500 mt-3">
                Formatos soportados: PDF, TXT, DOC, DOCX
              </p>
            </div>
          </div>

          {/* Área de texto */}
          <div className="mb-6">
            <label className="block text-gray-700 mb-2 font-medium">
              O pega el texto directamente:
            </label>
            <div className="relative">
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                placeholder="Pega aquí el contenido de tu factura comercial, packing list, contrato de transporte, conocimiento de embarque, o cualquier documento relacionado con el envío internacional..."
                className="w-full h-64 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none font-mono text-sm"
                spellCheck="false"
              />
              {documentText && (
                <button
                  onClick={handleCopyText}
                  className="absolute top-3 right-3 p-2 text-gray-500 hover:text-green-600 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Copiar texto"
                >
                  <Copy className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Contadores y botón de análisis */}
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-gray-600">
              <span className="font-medium">{documentText.length}</span> caracteres | 
              <span className="font-medium ml-2">{documentText.split(/\s+/).filter(Boolean).length}</span> palabras
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleClearAll}
                className="px-5 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
                disabled={loading}
              >
                <Trash2 className="w-4 h-4" />
                Limpiar Todo
              </button>
              <button
                onClick={handleAnalyze}
                disabled={loading || !documentText.trim()}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analizando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Analizar Documento
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Panel de resultados */}
        {analysis && (
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-blue-600" />
                Análisis Profesional GREENLOGISTICS AI
              </h2>
              <button
                onClick={handleCopyAnalysis}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                Copiar Análisis
              </button>
            </div>
            
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
              <pre className="whitespace-pre-wrap font-sans text-gray-800 leading-relaxed text-sm md:text-base">
                {analysis}
              </pre>
            </div>
            
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">¿Qué sigue?</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                  <h4 className="font-medium text-green-800 mb-1">1. Revisa los riesgos</h4>
                  <p className="text-sm text-green-700">Identifica las alertas críticas en aduanas y regulaciones.</p>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                  <h4 className="font-medium text-blue-800 mb-1">2. Implementa el plan</h4>
                  <p className="text-sm text-blue-700">Sigue el plan de acción inmediato y preparatorio.</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
                  <h4 className="font-medium text-purple-800 mb-1">3. Valida profesionalmente</h4>
                  <p className="text-sm text-purple-700">Este análisis es de soporte. Consulta a un especialista.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Info del backend */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <h3 className="font-medium text-blue-800 mb-2">Información del Backend</h3>
          <p className="text-sm text-blue-700">
            URL del API: <code className="bg-blue-100 px-2 py-1 rounded font-mono">{API_URL}</code>
          </p>
          <p className="text-sm text-blue-700 mt-1">
            Estado: <span className={`font-medium ${apiStatus === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
              {apiStatus === 'healthy' ? '✅ Conectado' : '❌ Desconectado'}
            </span>
          </p>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto mt-12 pt-8 border-t border-gray-200 text-center text-gray-600 text-sm">
        <p>
          <strong>GREENLOGISTICS AI</strong> • MVP para validación • 
          Este es un sistema de soporte a decisiones, no sustituye asesoría profesional.
        </p>
        <p className="mt-2">
          Backend: Render.com | Frontend: Vercel.com | IA: Anthropic Claude
        </p>
      </footer>
    </div>
  );
}

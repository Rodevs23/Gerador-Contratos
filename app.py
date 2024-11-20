import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Save, Tag } from 'lucide-react';

const TemplateEditor = () => {
  const [selectedTexts, setSelectedTexts] = useState([]);
  const [showNamePrompt, setShowNamePrompt] = useState(false);
  const [selectedRange, setSelectedRange] = useState(null);
  
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection.toString().trim()) return;

    const range = selection.getRangeAt(0);
    setSelectedRange(range);
    setShowNamePrompt(true);
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header */}
      <div className="bg-[#005B96] p-8 rounded-lg mb-6 text-center">
        <img 
          src="/api/placeholder/200/80" 
          alt="Consult Contabilidade" 
          className="mx-auto mb-4 bg-white p-2 rounded"
        />
        <h1 className="text-2xl font-bold text-white">Criar Modelo de Contrato</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Documento Original */}
        <Card className="p-6">
          <div className="relative">
            <div className="absolute top-2 right-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
              Selecione o texto para marcar como variável
            </div>
            
            {/* Documento com texto selecionável */}
            <div 
              className="font-serif space-y-4 mt-12 cursor-text select-text"
              onMouseUp={handleTextSelection}
            >
              <h3 className="text-center font-bold mb-6">
                CONTRATO DE PRESTAÇÃO DE SERVIÇOS CONTÁBEIS
              </h3>
              
              <p className="text-justify leading-relaxed">
                Por este instrumento particular de Contrato de Prestação de Serviços Contábeis que 
                fazem entre si, de um lado, BGE TRANSPORTES EIRELI, com sede na cidade de Cambé, 
                Estado do Paraná, na Av Jose Bonifácio, nº 3401...
              </p>
            </div>

            {/* Pop-up para nomear variável */}
            {showNamePrompt && (
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-2xl border w-96">
                <div className="mb-4">
                  <h4 className="text-lg font-semibold text-gray-700 mb-2">
                    Texto Selecionado:
                  </h4>
                  <div className="bg-blue-50 p-2 rounded text-sm">
                    {selectedRange?.toString()}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome da Variável:
                  </label>
                  <input
                    type="text"
                    className="w-full p-2 border rounded"
                    placeholder="Ex: RAZAO_SOCIAL"
                    autoFocus
                    onChange={(e) => e.target.value = e.target.value.toUpperCase()}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <button 
                    className="px-4 py-2 border rounded text-gray-600"
                    onClick={() => setShowNamePrompt(false)}
                  >
                    Cancelar
                  </button>
                  <button 
                    className="px-4 py-2 bg-blue-600 text-white rounded"
                    onClick={() => {
                      // Adicionar à lista de variáveis
                      setSelectedTexts([...selectedTexts, {
                        text: selectedRange.toString(),
                        variableName: document.querySelector('input').value,
                      }]);
                      setShowNamePrompt(false);
                    }}
                  >
                    Confirmar
                  </button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Painel de Variáveis */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-6 flex items-center gap-2">
            <Tag className="w-5 h-5" />
            Variáveis Marcadas
          </h2>

          {selectedTexts.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Selecione trechos do texto para marcar como variáveis
            </div>
          ) : (
            <div className="space-y-4">
              {selectedTexts.map((item, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg border">
                  <div className="text-sm text-gray-600 mb-1">Texto Original:</div>
                  <div className="bg-blue-50 p-2 rounded mb-2 text-sm">
                    {item.text}
                  </div>
                  <div className="text-sm text-gray-600 mb-1">Será substituído por:</div>
                  <div className="font-mono text-blue-600 bg-blue-50 p-2 rounded text-sm">
                    #{item.variableName}#
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button className="px-6 py-2 bg-[#005B96] text-white rounded-lg hover:bg-[#004b7a] flex items-center gap-2">
              <Save className="w-4 h-4" />
              Salvar Modelo
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default TemplateEditor;

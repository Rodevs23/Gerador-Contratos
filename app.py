import streamlit as st
from docx import Document
import pandas as pd
import os
from datetime import datetime
import io
import json

# Configuração da página
st.set_page_config(
    page_title="Sistema de Contratos - Consult Contabilidade",
    page_icon="📄",
    layout="wide"
)

# Estilo personalizado com as cores da Consult
st.markdown("""
    <style>
    /* Cores corporativas */
    :root {
        --primary-color: #005B96;
        --secondary-color: #6497B1;
    }
    
    .header {
        background-color: var(--primary-color);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .selected-text {
        background-color: #e3f2fd;
        padding: 2px 5px;
        border-radius: 3px;
        cursor: pointer;
    }
    
    .variable-tag {
        background-color: #005B96;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

# Função para carregar/criar banco de modelos
def load_models():
    if 'models.json' not in os.listdir():
        with open('models.json', 'w') as f:
            json.dump([], f)
    with open('models.json', 'r') as f:
        return json.load(f)

def main():
    st.markdown("""
        <div class="header">
            <img src="logo.png" style="max-width: 200px; margin-bottom: 1rem;">
            <h1>Sistema de Contratos</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Menu principal com botões ao invés de sidebar
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        if st.button("📝 Criar Modelo", use_container_width=True):
            st.session_state.page = "create_model"
    with col2:
        if st.button("📄 Gerar Contrato", use_container_width=True):
            st.session_state.page = "generate_contract"
    
    # Inicializar estado da sessão se necessário
    if 'page' not in st.session_state:
        st.session_state.page = "create_model"
        
    # Mostrar página apropriada
    if st.session_state.page == "create_model":
        show_model_creation()
    else:
        show_contract_generation()

def show_model_creation():
    st.subheader("Criar Novo Modelo de Contrato")
    
    # Upload do arquivo
    uploaded_file = st.file_uploader("Selecione o arquivo do contrato (.docx)", type=['docx'])
    
    if uploaded_file:
        # Carregar documento
        doc = Document(uploaded_file)
        doc_text = []
        
        # Extrair texto do documento
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                doc_text.append(paragraph.text)
        
        # Mostrar texto do documento
        st.markdown("### Selecione os textos que serão variáveis")
        st.info("Clique no texto para marcar como variável")
        
        # Área do documento com textos selecionáveis
        for i, text in enumerate(doc_text):
            # Criar elementos clicáveis
            if st.button(f"{text}", key=f"text_{i}", help="Clique para marcar como variável"):
                # Abrir modal para definir nome da variável
                with st.form(f"variable_form_{i}"):
                    st.write("Texto selecionado:", text)
                    variable_name = st.text_input("Nome da variável:").upper()
                    if st.form_submit_button("Confirmar"):
                        # Salvar variável
                        if 'variables' not in st.session_state:
                            st.session_state.variables = []
                        st.session_state.variables.append({
                            'text': text,
                            'variable': variable_name,
                            'position': i
                        })
                        st.success(f"Variável {variable_name} adicionada!")
        
        # Mostrar variáveis definidas
        if 'variables' in st.session_state and st.session_state.variables:
            st.markdown("### Variáveis Definidas")
            for var in st.session_state.variables:
                st.markdown(f"**{var['text']}** → #{var['variable']}#")
        
        # Botão para salvar modelo
        if st.button("💾 Salvar Modelo"):
            model_name = st.text_input("Nome do modelo:")
            if model_name:
                # Salvar modelo
                models = load_models()
                models.append({
                    'name': model_name,
                    'file': uploaded_file.name,
                    'file_content': uploaded_file.getvalue(),
                    'variables': st.session_state.variables,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                with open('models.json', 'w') as f:
                    json.dump(models, f)
                st.success("Modelo salvo com sucesso!")

def show_contract_generation():
    st.subheader("Gerar Novo Contrato")
    
    # Carregar modelos disponíveis
    models = load_models()
    
    if not models:
        st.warning("Nenhum modelo cadastrado. Por favor, crie um modelo primeiro.")
        return
    
    # Selecionar modelo
    model_names = [m['name'] for m in models]
    selected_model = st.selectbox("Selecione o modelo:", model_names)
    
    # Encontrar modelo selecionado
    model = next(m for m in models if m['name'] == selected_model)
    
    # Criar formulário com campos dinâmicos
    with st.form("contract_form"):
        st.subheader("Preencha as informações")
        
        # Valores para substituição
        values = {}
        col1, col2 = st.columns(2)
        
        for i, var in enumerate(model['variables']):
            with col1 if i % 2 == 0 else col2:
                values[var['variable']] = st.text_input(
                    var['variable'].replace('_', ' ').title(),
                    help=f"Texto original: {var['text']}"
                )
        
        if st.form_submit_button("Gerar Contrato"):
            try:
                # Carregar documento original
                doc = Document(io.BytesIO(model['file_content']))
                
                # Substituir variáveis
                for paragraph in doc.paragraphs:
                    for var in model['variables']:
                        if var['text'] in paragraph.text:
                            paragraph.text = paragraph.text.replace(
                                var['text'],
                                values[var['variable']]
                            )
                
                # Salvar documento modificado
                output = io.BytesIO()
                doc.save(output)
                output.seek(0)
                
                # Oferecer download
                st.download_button(
                    label="📥 Download do Contrato",
                    data=output,
                    file_name=f"contrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.success("Contrato gerado com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao gerar contrato: {str(e)}")

if __name__ == "__main__":
    main()

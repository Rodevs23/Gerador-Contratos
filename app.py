import streamlit as st
from docx import Document
import io
import json
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Sistema de Contratos - Consult",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo personalizado
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .element-container {
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #005B96;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #004b7a;
    }
    .marked-text {
        background-color: #e3f2fd;
        padding: 2px 5px;
        border-radius: 3px;
        cursor: pointer;
    }
    .variable-input {
        margin-top: 1rem;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Funções auxiliares
def load_or_create_data():
    if 'models.json' not in os.listdir():
        with open('models.json', 'w') as f:
            json.dump({'models': []}, f)
    with open('models.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('models.json', 'w') as f:
        json.dump(data, f)

def main():
    # Header com logo da Consult
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.jpg", width=300)

    # Menu principal com botões
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Criar Modelo de Contrato", use_container_width=True):
            st.session_state.page = "create"
    with col2:
        if st.button("📄 Preencher Contrato", use_container_width=True):
            st.session_state.page = "fill"

    if 'page' not in st.session_state:
        st.session_state.page = "create"

    # Separador visual
    st.markdown("---")

    # Mostrar página apropriada
    if st.session_state.page == "create":
        show_create_model()
    else:
        show_fill_contract()

def show_create_model():
    st.header("Criar Modelo de Contrato")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo do contrato (.docx)", 
        type=['docx'],
        help="Upload do arquivo do contrato em formato Word (.docx)"
    )

    if uploaded_file:
        # Carregar documento
        doc_bytes = uploaded_file.read()
        doc = Document(io.BytesIO(doc_bytes))

        # Mostrar conteúdo do documento
        st.markdown("### 1. Selecione os textos que serão variáveis")
        st.info("Clique no texto para definir como variável")

        # Armazenar variáveis na sessão
        if 'variables' not in st.session_state:
            st.session_state.variables = []

        # Processar parágrafos
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                # Criar botão para cada parágrafo
                if st.button(f"{paragraph.text}", key=f"p_{i}"):
                    with st.expander("Definir Variável", expanded=True):
                        with st.form(f"var_form_{i}"):
                            st.write("**Texto selecionado:**")
                            st.code(paragraph.text)
                            var_name = st.text_input(
                                "Nome da variável:",
                                max_chars=30
                            ).upper()
                            if st.form_submit_button("Confirmar"):
                                new_var = {
                                    'text': paragraph.text,
                                    'variable': var_name,
                                    'position': i
                                }
                                st.session_state.variables.append(new_var)
                                st.success(f"Variável {var_name} adicionada!")
                                st.experimental_rerun()

        # Mostrar variáveis marcadas
        if st.session_state.variables:
            st.markdown("### 2. Variáveis Definidas")
            for var in st.session_state.variables:
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.code(f"{var['text']} → #{var['variable']}#")
                with col3:
                    if st.button("🗑️", key=f"del_{var['variable']}"):
                        st.session_state.variables.remove(var)
                        st.experimental_rerun()

            # Salvar modelo
            with st.form("save_model"):
                st.markdown("### 3. Salvar Modelo")
                model_name = st.text_input("Nome do modelo:")
                if st.form_submit_button("💾 Salvar Modelo"):
                    if model_name:
                        data = load_or_create_data()
                        new_model = {
                            'name': model_name,
                            'file': uploaded_file.name,
                            'content': doc_bytes,
                            'variables': st.session_state.variables,
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        data['models'].append(new_model)
                        save_data(data)
                        st.success("✅ Modelo salvo com sucesso!")
                        # Limpar estado
                        st.session_state.variables = []
                        st.experimental_rerun()

def show_fill_contract():
    st.header("Preencher Contrato")
    
    # Carregar modelos
    data = load_or_create_data()
    models = data.get('models', [])

    if not models:
        st.warning("⚠️ Nenhum modelo cadastrado. Por favor, crie um modelo primeiro.")
        return

    # Selecionar modelo
    selected_model_name = st.selectbox(
        "Selecione o modelo:",
        options=[m['name'] for m in models]
    )

    # Encontrar modelo selecionado
    model = next(m for m in models if m['name'] == selected_model_name)

    # Formulário de preenchimento
    with st.form("fill_contract"):
        st.subheader("Dados do Contrato")
        
        # Criar campos para cada variável
        values = {}
        col1, col2 = st.columns(2)
        
        for i, var in enumerate(model['variables']):
            with col1 if i % 2 == 0 else col2:
                values[var['variable']] = st.text_input(
                    var['variable'].replace('_', ' ').title(),
                    help=f"Original: {var['text']}"
                )

        # Botão de geração
        if st.form_submit_button("📄 Gerar Contrato"):
            try:
                # Carregar documento
                doc = Document(io.BytesIO(model['content']))
                
                # Substituir variáveis
                for var in model['variables']:
                    for paragraph in doc.paragraphs:
                        if var['text'] in paragraph.text:
                            paragraph.text = paragraph.text.replace(
                                var['text'],
                                values[var['variable']]
                            )
                
                # Gerar arquivo
                output = io.BytesIO()
                doc.save(output)
                output.seek(0)
                
                # Botão de download
                st.download_button(
                    label="⬇️ Download do Contrato",
                    data=output,
                    file_name=f"contrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.success("✅ Contrato gerado com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar contrato: {str(e)}")

if __name__ == "__main__":
    main()

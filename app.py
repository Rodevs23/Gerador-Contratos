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
)

# Estilo personalizado
st.markdown("""
    <style>
    /* Cores Consult */
    :root {
        --primary-color: #005B96;
        --secondary-color: #6497B1;
    }
    
    /* Estilo geral */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    /* Estilo para texto marcado */
    .marked-text {
        background-color: #e3f2fd;
        padding: 2px 5px;
        border-radius: 3px;
    }
    
    /* Header personalizado */
    .header {
        padding: 2rem;
        background-color: var(--primary-color);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Funções auxiliares
def load_or_create_models():
    if 'models.json' not in os.listdir():
        with open('models.json', 'w') as f:
            json.dump({'models': []}, f)
    with open('models.json', 'r') as f:
        return json.load(f)

def save_model(model_data):
    data = load_or_create_models()
    data['models'].append(model_data)
    with open('models.json', 'w') as f:
        json.dump(data, f)

def main():
    # Header com logo
    st.markdown("""
        <div class="header">
            <img src="logo.png" style="max-width: 200px; margin-bottom: 1rem;">
            <h1>Sistema de Contratos</h1>
        </div>
    """, unsafe_allow_html=True)

    # Menu principal com botões
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Criar Modelo", use_container_width=True):
            st.session_state.page = "create"
    with col2:
        if st.button("📄 Preencher Contrato", use_container_width=True):
            st.session_state.page = "fill"

    # Inicializar estado da página
    if 'page' not in st.session_state:
        st.session_state.page = "create"

    # Mostrar página apropriada
    if st.session_state.page == "create":
        show_create_model()
    else:
        show_fill_contract()

def show_create_model():
    st.header("Criar Modelo de Contrato")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo do contrato (.docx)", 
        type=['docx']
    )

    if uploaded_file:
        # Ler documento
        doc = Document(uploaded_file)
        
        # Inicializar variáveis na sessão se necessário
        if 'variables' not in st.session_state:
            st.session_state.variables = []
        
        # Interface de marcação
        st.markdown("### Selecione o texto para criar variáveis")
        
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                # Mostrar texto com marcações existentes
                display_text = paragraph.text
                for var in st.session_state.variables:
                    if var['text'] in display_text:
                        display_text = display_text.replace(
                            var['text'],
                            f'<span class="marked-text">#{var["variable"]}#</span>'
                        )
                
                # Criar área clicável
                col1, col2 = st.columns([5,1])
                with col1:
                    st.markdown(display_text, unsafe_allow_html=True)
                with col2:
                    if st.button("Marcar", key=f"mark_{i}"):
                        # Popup para definir variável
                        with st.form(key=f"variable_form_{i}"):
                            st.write("**Texto selecionado:**")
                            st.code(paragraph.text)
                            var_name = st.text_input(
                                "Nome da variável:",
                                key=f"var_input_{i}"
                            ).upper()
                            
                            if st.form_submit_button("Confirmar"):
                                st.session_state.variables.append({
                                    'text': paragraph.text,
                                    'variable': var_name
                                })
                                st.experimental_rerun()
        
        # Mostrar variáveis definidas
        if st.session_state.variables:
            st.markdown("### Variáveis Definidas")
            for var in st.session_state.variables:
                col1, col2, col3 = st.columns([3,2,1])
                with col1:
                    st.code(f"Texto: {var['text']}")
                with col2:
                    st.code(f"#{var['variable']}#")
                with col3:
                    if st.button("🗑️", key=f"del_{var['variable']}"):
                        st.session_state.variables.remove(var)
                        st.experimental_rerun()
            
            # Salvar modelo
            with st.form("save_model"):
                st.markdown("### Salvar Modelo")
                model_name = st.text_input("Nome do modelo:")
                
                if st.form_submit_button("💾 Salvar"):
                    if model_name:
                        model_data = {
                            'name': model_name,
                            'file': uploaded_file.getvalue(),
                            'variables': st.session_state.variables,
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_model(model_data)
                        st.success("✅ Modelo salvo com sucesso!")
                        st.session_state.variables = []
                        st.experimental_rerun()

def show_fill_contract():
    st.header("Preencher Contrato")
    
    # Carregar modelos disponíveis
    data = load_or_create_models()
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
        st.subheader("Preencha as informações")
        
        # Criar campos para cada variável
        values = {}
        col1, col2 = st.columns(2)
        
        for i, var in enumerate(model['variables']):
            with col1 if i % 2 == 0 else col2:
                values[var['variable']] = st.text_input(
                    var['variable'].replace('_', ' ').title(),
                    help=f"Original: {var['text']}"
                )
        
        if st.form_submit_button("Gerar Contrato"):
            try:
                # Carregar documento
                doc = Document(io.BytesIO(model['file']))
                
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

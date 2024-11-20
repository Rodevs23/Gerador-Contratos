import streamlit as st
from docx import Document
import pandas as pd
import os
from datetime import datetime
import io

# Configuração da página
st.set_page_config(
    page_title="Sistema de Contratos - Consult Contabilidade",
    page_icon="📄",
    layout="wide"
)

# Estilo personalizado
st.markdown("""
    <style>
    /* Cores corporativas */
    :root {
        --primary-color: #005B96;
        --secondary-color: #6497B1;
    }
    
    /* Header */
    .header {
        background-color: var(--primary-color);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    /* Botões */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    /* Cards */
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Função para carregar ou criar banco de modelos
@st.cache_data
def load_templates():
    if 'templates.csv' not in os.listdir():
        df = pd.DataFrame(columns=['nome', 'arquivo', 'variaveis'])
        df.to_csv('templates.csv', index=False)
    return pd.read_csv('templates.csv')

# Função para processar documento
def process_document(doc_bytes, replacements):
    doc = Document(io.BytesIO(doc_bytes))
    
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if f'#{key}#' in paragraph.text:
                paragraph.text = paragraph.text.replace(f'#{key}#', value)
    
    # Também substituir em tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if f'#{key}#' in cell.text:
                        cell.text = cell.text.replace(f'#{key}#', value)
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def main():
    # Header
    st.markdown("""
        <div class="header">
            <h1>Sistema de Contratos - Consult Contabilidade</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Menu principal
    menu = st.sidebar.selectbox(
        "Escolha uma opção",
        ["Gerar Contrato", "Gerenciar Modelos"]
    )
    
    if menu == "Gerar Contrato":
        show_contract_generation()
    else:
        show_template_management()

def show_contract_generation():
    st.subheader("Gerar Novo Contrato")
    
    # Carregar modelos
    df_templates = load_templates()
    if len(df_templates) == 0:
        st.warning("Nenhum modelo cadastrado. Por favor, adicione um modelo primeiro.")
        return
    
    # Seleção do modelo
    template_name = st.selectbox("Selecione o Modelo", df_templates['nome'].tolist())
    
    # Carregar template selecionado
    template = df_templates[df_templates['nome'] == template_name].iloc[0]
    variables = eval(template['variaveis'])
    
    # Formulário de preenchimento
    with st.form("contract_form"):
        st.subheader("Preencha as informações")
        
        # Criar campos dinâmicos
        values = {}
        col1, col2 = st.columns(2)
        
        for i, var in enumerate(variables):
            with col1 if i % 2 == 0 else col2:
                values[var] = st.text_input(var.replace('_', ' ').title())
        
        submitted = st.form_submit_button("Gerar Contrato")
        
        if submitted:
            try:
                # Processar documento
                doc_bytes = template['arquivo'].encode()
                output = process_document(doc_bytes, values)
                
                # Download
                st.download_button(
                    label="📥 Download do Contrato",
                    data=output,
                    file_name=f"contrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.success("Contrato gerado com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao gerar contrato: {str(e)}")

def show_template_management():
    st.subheader("Gerenciar Modelos")
    
    # Mostrar modelos existentes
    st.write("### Modelos Cadastrados")
    df_templates = load_templates()
    if len(df_templates) > 0:
        for _, row in df_templates.iterrows():
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                st.write(row['nome'])
            with col2:
                st.write(f"{len(eval(row['variaveis']))} variáveis")
            with col3:
                st.button("🗑️ Excluir", key=f"del_{row['nome']}")
    
    # Adicionar novo modelo
    st.write("### Adicionar Novo Modelo")
    with st.form("new_template"):
        nome = st.text_input("Nome do Modelo")
        arquivo = st.file_uploader("Arquivo do Modelo (.docx)", type=['docx'])
        variaveis = st.text_area(
            "Variáveis (uma por linha)",
            help="Digite as variáveis que serão substituídas no documento"
        )
        
        submitted = st.form_submit_button("Salvar Modelo")
        
        if submitted and nome and arquivo and variaveis:
            try:
                vars_list = [v.strip() for v in variaveis.split('\n') if v.strip()]
                new_template = pd.DataFrame({
                    'nome': [nome],
                    'arquivo': [arquivo.read()],
                    'variaveis': [str(vars_list)]
                })
                
                df_templates = pd.concat([df_templates, new_template], ignore_index=True)
                df_templates.to_csv('templates.csv', index=False)
                
                st.success("Modelo salvo com sucesso!")
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar modelo: {str(e)}")

if __name__ == "__main__":
    main()

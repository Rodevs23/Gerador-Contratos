import streamlit as st
import json
from pathlib import Path
from docx import Document
import io
import docx
import base64
from docx.shared import Pt, Cm
import re

def read_docx(file):
    """Lê o conteúdo de um arquivo .docx"""
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def save_template(name, content, variables):
    """Salva o template com suas variáveis"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    data = {
        "content": content,
        "variables": variables
    }
    
    with open(template_path / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_templates():
    """Carrega os templates salvos"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    templates = {}
    for file in template_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            templates[file.stem] = json.load(f)
    return templates

def generate_doc_from_template(template_content, variables_values, original_doc):
    """Gera novo documento mantendo a formatação original"""
    doc = Document(original_doc)
    
    # Substituir variáveis no texto
    for paragraph in doc.paragraphs:
        for var_name, var_value in variables_values.items():
            if f"#{var_name}#" in paragraph.text:
                paragraph.text = paragraph.text.replace(f"#{var_name}#", var_value)

    # Salvar em bytes
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    return doc_bytes

def main():
    st.set_page_config(page_title="Gerador de Contratos", layout="wide")

    if "current_content" not in st.session_state:
        st.session_state.current_content = ""
    if "variables" not in st.session_state:
        st.session_state.variables = {}
    if "original_doc" not in st.session_state:
        st.session_state.original_doc = None

    st.title("Gerador de Contratos")

    # Menu lateral para escolher a função
    with st.sidebar:
        option = st.radio(
            "Escolha a função:",
            ["Cadastrar Novo Modelo", "Preencher Contrato"]
        )

    if option == "Cadastrar Novo Modelo":
        st.header("Cadastrar Novo Modelo de Contrato")
        
        # Nome do template
        template_name = st.text_input("Nome do Modelo:", key="template_name")
        
        # Upload do arquivo
        uploaded_file = st.file_uploader("Carregar arquivo do contrato (.docx)", type="docx")
        
        if uploaded_file:
            if "current_content" not in st.session_state or not st.session_state.current_content:
                # Salvar o arquivo original para manter a formatação
                st.session_state.original_doc = uploaded_file
                # Ler o conteúdo do arquivo
                st.session_state.current_content = read_docx(uploaded_file)

            # Exibir texto atual e permitir seleção
            st.subheader("Selecione o texto para criar variáveis:")
            
            # Campo de texto para seleção
            selected_text = st.text_area("Texto do Contrato", 
                                       st.session_state.current_content,
                                       height=400,
                                       key="contract_text")

            # Botão para marcar variável
            col1, col2 = st.columns([2, 1])
            with col1:
                text_to_replace = st.text_input("Texto a ser marcado como variável:")
            with col2:
                if st.button("Marcar como Variável") and text_to_replace:
                    # Solicitar nome da variável
                    var_name = st.text_input("Nome da variável:").upper()
                    if var_name:
                        # Substituir no texto
                        new_content = selected_text.replace(
                            text_to_replace, 
                            f"#{var_name}#"
                        )
                        st.session_state.current_content = new_content
                        st.session_state.variables[var_name] = text_to_replace
                        st.rerun()

            # Exibir variáveis marcadas
            if st.session_state.variables:
                st.subheader("Variáveis Marcadas:")
                for var_name, original_text in st.session_state.variables.items():
                    st.code(f"#{var_name}# = {original_text}")

            # Salvar template
            if st.button("Salvar Modelo", type="primary"):
                if not template_name:
                    st.error("Digite um nome para o modelo!")
                    return
                
                try:
                    save_template(
                        template_name,
                        st.session_state.current_content,
                        list(st.session_state.variables.keys())
                    )
                    # Salvar documento original
                    template_path = Path("templates")
                    st.session_state.original_doc.seek(0)
                    with open(template_path / f"{template_name}_original.docx", "wb") as f:
                        f.write(st.session_state.original_doc.read())
                    
                    st.success("Modelo salvo com sucesso!")
                    # Limpar estado
                    st.session_state.current_content = ""
                    st.session_state.variables = {}
                    st.session_state.original_doc = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {str(e)}")

    else:  # Preencher Contrato
        st.header("Preencher Contrato")
        
        # Carregar templates
        templates = load_templates()
        if not templates:
            st.warning("Nenhum modelo cadastrado. Cadastre um modelo primeiro!")
            return

        # Selecionar template
        template_name = st.selectbox(
            "Selecione o Modelo:",
            options=list(templates.keys())
        )

        if template_name:
            template = templates[template_name]
            
            # Criar duas colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Preencher Dados")
                values = {}
                # Campo para cada variável
                for var in template["variables"]:
                    values[var] = st.text_input(f"{var}:")

                if st.button("Gerar Contrato", type="primary"):
                    # Verificar campos vazios
                    empty_fields = [var for var, val in values.items() if not val.strip()]
                    if empty_fields:
                        st.error("Preencha todos os campos!")
                        return

                    try:
                        # Carregar documento original
                        original_doc_path = Path("templates") / f"{template_name}_original.docx"
                        if not original_doc_path.exists():
                            st.error("Arquivo original do template não encontrado!")
                            return

                        # Gerar novo documento
                        doc_bytes = generate_doc_from_template(
                            template["content"],
                            values,
                            original_doc_path
                        )

                        # Botão de download
                        st.download_button(
                            "⬇️ Baixar Contrato",
                            doc_bytes,
                            file_name=f"contrato_preenchido.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                        st.success("Contrato gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar contrato: {str(e)}")
            
            with col2:
                st.subheader("Prévia do Contrato")
                preview = template["content"]
                for var, val in values.items():
                    preview = preview.replace(f"#{var}#", val if val else f"[{var}]")
                st.text_area("", value=preview, height=400, disabled=True)

if __name__ == "__main__":
    main()

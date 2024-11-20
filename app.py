import streamlit as st
import json
from pathlib import Path
from docx import Document
import io


def read_docx(file):
    """Lê o conteúdo do arquivo .docx"""
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def save_template(name, content, variables, original_file):
    """Salva o template com suas variáveis e o arquivo original"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    data = {
        "content": content,
        "variables": variables
    }
    
    with open(template_path / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    original_file.seek(0)
    with open(template_path / f"{name}.docx", "wb") as f:
        f.write(original_file.read())


def load_templates():
    """Carrega os templates salvos"""
    template_path = Path("templates")
    template_path.mkdir(exist_ok=True)
    
    templates = {}
    for file in template_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            templates[file.stem] = json.load(f)
    return templates


def process_document(template_name, values):
    """Processa o documento substituindo as variáveis"""
    template_path = Path("templates")
    doc = Document(template_path / f"{template_name}.docx")
    
    for paragraph in doc.paragraphs:
        for var_name, value in values.items():
            placeholder = f"#{var_name}#"
            if placeholder in paragraph.text:
                print(f"Encontrado {placeholder} no texto: {paragraph.text}")
                for run in paragraph.runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, str(value))
                        print(f"Substituído em run: {run.text}")
    
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    return doc_bytes


def main():
    st.set_page_config(page_title="Gerador de Contratos", layout="wide")

    # Inicializar estados
    if "current_content" not in st.session_state:
        st.session_state.current_content = ""
    if "variables" not in st.session_state:
        st.session_state.variables = {}
    if "original_file" not in st.session_state:
        st.session_state.original_file = None

    st.title("Gerador de Contratos")

    # Dividir em duas páginas
    page = st.sidebar.radio("Navegação", ["Cadastrar Novo Modelo", "Preencher Contrato"])

    if page == "Cadastrar Novo Modelo":
        st.header("Cadastrar Novo Modelo de Contrato")

        template_name = st.text_input("Nome do Modelo:", key="template_name")
        uploaded_file = st.file_uploader("Carregar arquivo do contrato (.docx)", type="docx")

        if uploaded_file:
            try:
                if not st.session_state.current_content:
                    st.session_state.original_file = uploaded_file
                    st.session_state.current_content = read_docx(uploaded_file)
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {str(e)}")
                return

            # Mostrar o texto carregado
            st.subheader("Texto do Contrato:")
            st.text_area("Conteúdo do contrato:", st.session_state.current_content, height=300, disabled=True)

            st.subheader("Adicionar Variáveis")
            selected_text = st.text_area("Copie e cole a parte do texto a ser substituída:")
            var_name = st.text_input("Nome da variável (sem espaços):").upper()

            if st.button("Adicionar Variável"):
                if selected_text.strip() and var_name.strip():
                    if var_name in st.session_state.variables:
                        st.warning(f"A variável {var_name} já foi adicionada!")
                    else:
                        new_content = st.session_state.current_content.replace(selected_text, f"#{var_name}#")
                        if new_content == st.session_state.current_content:
                            st.error("O texto selecionado não foi encontrado no contrato.")
                        else:
                            st.session_state.current_content = new_content
                            st.session_state.variables[var_name] = selected_text
                            st.success(f"Variável #{var_name}# adicionada com sucesso!")
                else:
                    st.error("Preencha todos os campos antes de adicionar.")

            # Mostrar variáveis adicionadas
            if st.session_state.variables:
                st.subheader("Variáveis Adicionadas:")
                for var_name, original_text in st.session_state.variables.items():
                    st.write(f"**#{var_name}#**: {original_text}")

            # Botão para salvar
            if st.button("Salvar Modelo"):
                if not template_name.strip():
                    st.error("Digite um nome para o modelo!")
                else:
                    try:
                        save_template(
                            template_name,
                            st.session_state.current_content,
                            list(st.session_state.variables.keys()),
                            st.session_state.original_file
                        )
                        st.success("Modelo salvo com sucesso!")
                        st.session_state.current_content = ""
                        st.session_state.variables = {}
                        st.session_state.original_file = None
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {str(e)}")

    elif page == "Preencher Contrato":
        st.header("Preencher Contrato")

        templates = load_templates()
        if not templates:
            st.warning("Nenhum modelo cadastrado. Cadastre um modelo primeiro!")
            return

        template_name = st.selectbox("Selecione o Modelo:", options=list(templates.keys()))

        if template_name:
            template = templates[template_name]

            st.subheader("Preencher Dados")
            values = {}
            for var in template["variables"]:
                values[var] = st.text_input(f"{var}:")

            if st.button("Gerar Contrato"):
                empty_fields = [var for var, val in values.items() if not val.strip()]
                if empty_fields:
                    st.error("Preencha todos os campos!")
                    return

                try:
                    doc_bytes = process_document(template_name, values)
                    st.download_button(
                        "Baixar Contrato",
                        doc_bytes,
                        file_name=f"{template_name}_preenchido.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("Contrato gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao gerar contrato: {str(e)}")


if __name__ == "__main__":
    main()

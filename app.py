def main():
    st.set_page_config(page_title="Gerador de Contratos", layout="wide")

    # Inicializar estados
    if "current_content" not in st.session_state:
        st.session_state.current_content = ""
    if "variables" not in st.session_state:
        st.session_state.variables = {}
    if "original_file" not in st.session_state:
        st.session_state.original_file = None
    if "highlight_mode" not in st.session_state:
        st.session_state.highlight_mode = False

    st.title("Gerador de Contratos")

    with st.sidebar:
        option = st.radio(
            "Escolha a função:",
            ["Cadastrar Novo Modelo", "Preencher Contrato"]
        )

    if option == "Cadastrar Novo Modelo":
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

            st.subheader("Marque as variáveis no texto:")
            st.markdown(f"Modo Marcação: {'🟢 Ativo' if st.session_state.highlight_mode else '🔴 Inativo'}")

            if st.session_state.highlight_mode:
                text = st.text_area(
                    "Texto do contrato:",
                    st.session_state.current_content,
                    height=400,
                    key="contract_text"
                )

                # Seleção de variáveis
                selected_text = st.text_area("Texto Selecionado:", "")
                var_name = st.text_input("Nome da variável:")
                if var_name and selected_text.strip():
                    new_content = st.session_state.current_content.replace(
                        selected_text,
                        f"#{var_name}#"
                    )
                    st.session_state.current_content = new_content
                    st.session_state.variables[var_name] = selected_text
                    st.success(f"Variável #{var_name}# adicionada!")
                    st.experimental_rerun()
            else:
                # Mostrar texto com variáveis marcadas
                content_with_highlights = st.session_state.current_content
                for var_name, text in st.session_state.variables.items():
                    content_with_highlights = content_with_highlights.replace(
                        f"#{var_name}#",
                        f'<span class="variable">#{var_name}#</span>'
                    )
                st.markdown(content_with_highlights, unsafe_allow_html=True)

            # Botão para salvar modelo
            if st.button("💾 Salvar Modelo"):
                if not template_name:
                    st.error("Digite um nome para o modelo!")
                    return
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

    else:  # Preencher Contrato
        st.header("Preencher Contrato")

        templates = load_templates()
        if not templates:
            st.warning("Nenhum modelo cadastrado. Cadastre um modelo primeiro!")
            return

        template_name = st.selectbox(
            "Selecione o Modelo:",
            options=list(templates.keys())
        )

        if template_name:
            template = templates[template_name]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Preencher Dados")
                values = {}
                for var in template["variables"]:
                    values[var] = st.text_input(f"{var}:", placeholder=f"Digite o valor para {var}")

                if st.button("Gerar Contrato"):
                    empty_fields = [var for var, val in values.items() if not val.strip()]
                    if empty_fields:
                        st.error("Preencha todos os campos!")
                        return

                    doc_bytes = process_document(template_name, values)
                    st.download_button(
                        "⬇️ Baixar Contrato",
                        doc_bytes,
                        file_name=f"{template_name}_preenchido.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("Contrato gerado com sucesso!")

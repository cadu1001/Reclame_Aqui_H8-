import streamlit as st
from supabase import create_client

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="Avaliar", page_icon="📝")

@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

st.title("📝 Reclame aqui H8")

# Criamos duas abas para organizar a bagunça
tab1, tab2 = st.tabs(["Avaliar Alguém", "Cadastrar Novo"])

# --- ABA 2: CADASTRAR NOVA PESSOA (Precisamos popular o banco primeiro) ---
with tab2:
    st.header("Cadastrar Novo")
    with st.form("form_cadastro"):
        name = st.text_input("Nome da Pessoa ou Entidade")
        role = st.selectbox("Categoria", ["Professor", "Aluno", "Funcionário", "Lugar/Comida", "Outro"])
        department = st.text_input("Departamento/Curso (Ex: COMP, H8, Reitoria)")
        
        submit_cadastro = st.form_submit_button("Cadastrar")
        
        if submit_cadastro:
            if name:
                # Envia para o Supabase
                try:
                    supabase.table("targets").insert({
                        "name": name, 
                        "role": role, 
                        "department": department
                    }).execute()
                    st.success(f"{name} cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")
            else:
                st.warning("O nome é obrigatório.")

# --- ABA 1: AVALIAR (Onde a mágica acontece) ---
with tab1:
    st.header("Deixe sua opinião")
    
    # Busca a lista de pessoas no banco para preencher o selectbox
    response = supabase.table("targets").select("*").execute()
    targets = response.data
    
    # Cria um dicionário {Nome: ID} para sabermos quem é quem
    if targets:
        target_options = {t['name']: t['id'] for t in targets}
        selected_name = st.selectbox("Quem você quer avaliar? ( Digite para limitar a busca )", list(target_options.keys()))
        selected_id = target_options[selected_name]
        
        with st.form("form_avaliacao"):
            rating = st.slider("Nota", 1, 5, 3)
            comment = st.text_area("Comentário (Seja respeitoso!)")
            submit_review = st.form_submit_button("Enviar Avaliação")
            
            if submit_review:
                try:
                    supabase.table("reviews").insert({
                        "target_id": selected_id,
                        "rating": rating,
                        "comment": comment
                    }).execute()
                    st.success("Avaliação enviada! 🚀")
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")
    else:
        st.info("Ninguém cadastrado ainda. Vá na aba 'Cadastrar Novo Alvo' primeiro!")
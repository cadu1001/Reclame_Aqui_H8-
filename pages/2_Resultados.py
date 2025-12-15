import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Resultados", page_icon="📊", layout="wide")

# --- 1. CONEXÃO ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

st.title("📊 Painel de Avaliações")

# --- 2. BUSCAR DADOS ---
with st.spinner("Atualizando dados..."):
    response_targets = supabase.table("targets").select("*").execute()
    response_reviews = supabase.table("reviews").select("*").execute()

df_targets = pd.DataFrame(response_targets.data)
df_reviews = pd.DataFrame(response_reviews.data)

# --- 3. PROCESSAMENTO ---
if not df_targets.empty and not df_reviews.empty:
    
    # Merge das tabelas (Review + Nome do Alvo)
    df_full = pd.merge(df_reviews, df_targets, left_on="target_id", right_on="id")

    # Filtro de Categoria (Lateral Esquerda)
    # Isso ajuda a limpar a lista se tiver muita gente
    categorias_disponiveis = df_targets["role"].unique()
    categoria_selecionada = st.selectbox(
        "Filtrar Ranking por Categoria:", 
        options=["Todas"] + list(categorias_disponiveis)
    )

    if categoria_selecionada != "Todas":
        df_full = df_full[df_full["role"] == categoria_selecionada]

    # Criação do Ranking
    ranking = df_full.groupby("name").agg({
        "rating": ["mean", "count"],
        "role": "first",
        "department": "first"
    }).reset_index()

    ranking.columns = ["Nome", "Nota Média", "Qtd Avaliações", "Categoria", "Departamento"]
    
    # Ordena por Qtd de avaliações (relevância) e depois por Nota
    ranking = ranking.sort_values(by=["Qtd Avaliações", "Nota Média"], ascending=[False, False])

    # --- 4. EXIBIÇÃO ---
    col_rank, col_detalhes = st.columns([1.2, 0.8]) 

    with col_rank:
        st.subheader(f"🏆 Classificação ({categoria_selecionada})")
        if not ranking.empty:
            # Tabela colorida (Requer matplotlib instalado)
            st.dataframe(
                ranking[["Nome", "Nota Média", "Qtd Avaliações", "Departamento"]].style.format({"Nota Média": "{:.2f}"}).background_gradient(subset=["Nota Média"], cmap="RdYlGn"),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Sem dados nesta categoria.")

    with col_detalhes:
        st.subheader("🔎 Investigar")
        
        if not ranking.empty:
            # --- SIMPLIFICADO: Selectbox direto ---
            # O usuário pode digitar dentro dessa caixa para buscar
            lista_nomes = ranking["Nome"].unique()
            escolha = st.selectbox("Selecione para ver detalhes: (Digite para limitar a busca)", lista_nomes)
            
            # Filtra reviews do escolhido
            filtred_reviews = df_full[df_full["name"] == escolha].sort_values(by="created_at_x", ascending=False)
            
            # Métricas
            m_nota = filtred_reviews["rating"].mean()
            m_qtd = filtred_reviews["rating"].count()
            
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Nota Média", f"{m_nota:.2f}")
            kpi2.metric("Total de Reviews", m_qtd)
            
            st.divider()
            st.write("💬 **Últimos Comentários:**")
            
            for index, row in filtred_reviews.iterrows():
                nota = row['rating']
                icon = "🟢" if nota >= 4 else "🔴" if nota <= 2 else "🟡"
                
                with st.chat_message("user"):
                    st.write(f"**{nota}/5** {icon} — {row['comment']}")
                    
                    # Tentativa de formatar a data
                    try:
                        data_fmt = pd.to_datetime(row['created_at_x']).strftime('%d/%m/%Y')
                        st.caption(f"Em {data_fmt}")
                    except:
                        st.caption("Data desconhecida")
        else:
            st.info("Selecione uma categoria com dados.")

elif df_targets.empty:
    st.warning("Nenhum alvo cadastrado ainda.")
else:
    st.info("Ainda não há avaliações cadastradas.")
# streamlit run app.py --server.port 8502

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import base64
from datetime import datetime, time
import psycopg2

# ---------------- CONFIG ---------------- #

st.set_page_config(
    page_title="Opiniômetro - Relatório",
    page_icon="📈",
)

# ---------------- DATABASE ---------------- #

conexao = psycopg2.connect(
    host=st.secrets["db"]["host"],
    port=6543,  
    database=st.secrets["db"]["name"],
    user=st.secrets["db"]["user"],
    password=st.secrets["db"]["password"],
    sslmode="require"
)

# ---------------- BACKGROUND IMAGE ---------------- #

def set_bg(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        section[data-testid="stMain"] {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-repeat: repeat-y;
            background-position: top center;
        }}

        .block-container {{
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("Logo01.png")

# ---------------- READ FUNCTIONS ---------------- #

def le_funcionarios():
    return pd.read_sql_query("SELECT * FROM funcionario", conexao)

def le_nps():
    return pd.read_sql_query("SELECT nps FROM nps", conexao)

def le_avaliacao_por_nome(nome):
    query = """
        SELECT
            f.nome,
            a.nota_p1,
            a.nota_p2,
            a.nota_p3,
            a.nota_p4,
            a.nota_p5
        FROM funcionario f
        JOIN avaliacao a ON a.id_funcionario = f.id
        WHERE f.nome = %s
    """
    return pd.read_sql_query(query, conexao, params=(nome,))

def le_avaliacoes_por_periodo(inicio, fim):
    """
    inicio and fim must be strings or datetime objects:
    'YYYY-MM-DD HH:MM'
    """

    query = """
        SELECT 
            nota_p1,
            nota_p2,
            nota_p3,
            nota_p4,
            nota_p5
        FROM Avaliacao
        WHERE data_hora BETWEEN %s AND %s
    """

    return pd.read_sql_query(
        query,
        conexao,
        params=(inicio, fim)
    )


# ---------------- UI ---------------- #

st.title("Estatísticas das Avaliações")

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Geral Funcionários",
    "Geral Serviço",
    "Funcionários",
    "Comentários",
    "Índices"
])

# ---------------- FILTER ---------------- #

col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data inicial", value=datetime.today().date())
with col2:
    data_fim = st.date_input("Data final", value=datetime.today().date())

inicio_iso = datetime.combine(data_inicio, time.min)
fim_iso = datetime.combine(data_fim, time.max)

# ================= ABA 1 ================= #

with aba1:
    st.header("Avaliação dos Funcionários")

    notas = le_avaliacoes_por_periodo(inicio_iso, fim_iso)
    notas_fun = notas[["nota_p1", "nota_p2", "nota_p3"]]

    st.dataframe(notas_fun)

    MED_notas_Fun = notas_fun.mean().mean() if not notas_fun.empty else 0

    st.subheader(f"Média Geral: {MED_notas_Fun:.2f}")

    st.subheader("Distribuição das respostas")
    cols = st.columns(3)

    for col, p, t in zip(
        cols,
        ["nota_p1", "nota_p2", "nota_p3"],
        ["Pergunta 1", "Pergunta 2", "Pergunta 3"]
    ):
        with col:
            if not notas_fun.empty:
                counts = notas_fun[p].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.pie(counts, labels=counts.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                ax.set_title(t)
                st.pyplot(fig)

# ================= ABA 2 ================= #

with aba2:
    st.header("Avaliação dos Serviços")

    notas_ser = notas[["nota_p4", "nota_p5"]]
    st.dataframe(notas_ser)

    MED_notas_ser = notas_ser.mean().mean() if not notas_ser.empty else 0
    st.subheader(f"Média Geral: {MED_notas_ser:.2f}")

    cols = st.columns(2)
    for col, p, t in zip(
        cols,
        ["nota_p4", "nota_p5"],
        ["Pergunta 4", "Pergunta 5"]
    ):
        with col:
            if not notas_ser.empty:
                counts = notas_ser[p].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.pie(counts, labels=counts.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                ax.set_title(t)
                st.pyplot(fig)

# ================= ABA 3 ================= #

with aba3:
    funs = le_funcionarios()
    nome = st.selectbox("Selecione o funcionário", funs["nome"])

    dados = le_avaliacao_por_nome(nome)
    notas_ind = dados[["nota_p1", "nota_p2", "nota_p3"]]

    st.dataframe(notas_ind)

    MED_notas = notas_ind.mean().mean() if not notas_ind.empty else 0
    st.subheader(f"Média Geral: {MED_notas:.2f}")

    cols = st.columns(3)
    for col, p, t in zip(
        cols,
        ["nota_p1", "nota_p2", "nota_p3"],
        ["Pergunta 1", "Pergunta 2", "Pergunta 3"]
    ):
        with col:
            if not notas_ind.empty:
                counts = notas_ind[p].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.pie(counts, labels=counts.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                ax.set_title(t)
                st.pyplot(fig)

# ================= ABA 4 ================= #

with aba4:
    st.header("Comentários")

    query = """
        SELECT c.comentario, a.data_hora
        FROM comentario c
        JOIN avaliacao a ON a.id = c.id_avaliacao
        ORDER BY a.data_hora DESC
    """
    comentarios = pd.read_sql_query(query, conexao)
    st.dataframe(comentarios)

# ================= ABA 5 ================= #

with aba5:
    st.header("Índices")

    ISCF = (MED_notas_Fun / 5) * 100
    ISCS = (MED_notas_ser / 5) * 100

    nps_df = le_nps()
    nps_vals = nps_df["nps"].tolist()

    promotores = sum(1 for x in nps_vals if x >= 9)
    detratores = sum(1 for x in nps_vals if x <= 6)
    total = len(nps_vals)

    PLP = ((promotores - detratores) / total) * 100 if total else 0

    st.metric("ISCF", f"{ISCF:.2f}%")
    st.metric("ISCS", f"{ISCS:.2f}%")
    st.metric("PLP", f"{PLP:.2f}%")




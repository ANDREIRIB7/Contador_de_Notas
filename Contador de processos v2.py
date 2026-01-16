import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ================= CONFIGURAÇÕES =================
SENHA_ADMIN = "Progen123"
ARQUIVO = "Nome_nota.csv"

st.set_page_config(page_title="Gestão de Notas Técnicas", layout="wide")

COLABORADORES = {
    "Andrei": "Administrador", "Arthur": "Administrador", "Carla": "Engenheiro(a)",
    "José": "Analista Administrativo", "Lucas": "Engenheiro(a)", "Nadya": "Engenheiro(a)",
    "Pedro": "Engenheiro(a)", "Uiter": "Engenheiro(a)", "Yan": "Engenheiro(a)"
}

# ================= FUNÇÕES =================
def gerar_numero_nota(df_base):
    ano_atual = datetime.now().year
    if df_base.empty:
        return 1, f"0001/{ano_atual}"
    df_ano = df_base[df_base["ano"] == ano_atual].copy()
    if df_ano.empty or df_ano["numero"].isna().all():
        proximo = 1
    else:
        proximo = int(df_ano["numero"].max()) + 1
    return proximo, f"{proximo:04d}/{ano_atual}"

# ================= CARREGAR BASE =================
col_obrig = ["id_nota", "nome_nota", "num_sei", "ano", "numero", "numero_completo", "colaborador", "cargo", "status", "data_criacao", "data_analise", "flag_obrigatorio"]

if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=col_obrig)
    df.to_csv(ARQUIVO, index=False)
else:
    df = pd.read_csv(ARQUIVO)
    df = df.dropna(subset=['nome_nota']) 
    for col in col_obrig:
        if col not in df.columns:
            df[col] = None 
    df["id_nota"] = pd.to_numeric(df["id_nota"], errors="coerce")
    df = df.dropna(subset=['id_nota'])
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")

# ================= INTERFACE =================
st.title("🏛️ Sistema de Gestão de Notas Técnicas")
prox_idx, prox_str = gerar_numero_nota(df)

st.metric(label="🔢 Próximo Número de Série", value=prox_str)
st.divider()

# ================= CADASTRO =================
with st.expander("🆕 Cadastrar Nova nota"):
    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            nome_novo = st.text_input("Nome do Processo / Assunto")
            num_sei_novo = st.text_input("Nº do processo no SEI")
        with c2:
            colab_novo = st.selectbox("Responsável", list(COLABORADORES.keys()))
            flag_novo = st.checkbox("NT com número inicial obrigatório")
        with c3:
            status_novo = st.selectbox("Status Inicial", ["Em elaboração", "Em análise"])
        
        if st.form_submit_button("Registrar Processo"):
            if not nome_novo:
                st.error("O nome é obrigatório.")
            else:
                novo_id = 1 if df.empty else int(df["id_nota"].max()) + 1
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                nova_linha = {"id_nota": novo_id, "nome_nota": nome_novo, "num_sei": num_sei_novo, "flag_obrigatorio": flag_novo, "colaborador": colab_novo, "cargo": COLABORADORES[colab_novo], "status": status_novo, "data_criacao": data_agora, "ano": None, "numero": None, "numero_completo": None, "data_analise": None}
                if status_novo == "Em análise" or flag_novo:
                    num, comp = gerar_numero_nota(df)
                    nova_linha.update({"ano": datetime.now().year, "numero": num, "numero_completo": comp, "data_analise": data_agora})
                df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
                df.to_csv(ARQUIVO, index=False)
                st.success("Registrado!")
                st.rerun()

# ================= EDIÇÃO =================
st.header("✏️ Gerenciar Processos")
if not df.empty:
    opcoes = df.apply(lambda x: f"ID {int(x['id_nota'])} - {x['nome_nota']}", axis=1).tolist()
    sel = st.selectbox("Selecione para editar", ["— Selecione —"] + opcoes)
    if sel != "— Selecione —":
        id_sel = int(sel.split("ID ")[1].split(" -")[0])
        idx = df.index[df['id_nota'] == id_sel][0]
        row = df.loc[idx]
        with st.container(border=True):
            ce1, ce2 = st.columns(2)
            with ce1:
                n_nome = st.text_input("Editar Nome", value=row["nome_nota"])
                n_sei = st.text_input("Editar Nº SEI", value="" if pd.isna(row["num_sei"]) else row["num_sei"])
            with ce2:
                n_status = st.selectbox("Status", ["Em elaboração", "Em análise", "Concluído"], index=["Em elaboração", "Em análise", "Concluído"].index(row["status"]))
                n_flag = st.checkbox("NT com número inicial obrigatório", value=bool(row["flag_obrigatorio"]))
            if st.button("Salvar Alterações"):
                df.at[idx, "nome_nota"], df.at[idx, "num_sei"], df.at[idx, "flag_obrigatorio"], df.at[idx, "status"] = n_nome, n_sei, n_flag, n_status
                if pd.isna(df.at[idx, "numero"]) and (n_status == "Em análise" or n_flag):
                    num, comp = gerar_numero_nota(df)
                    df.at[idx, "ano"], df.at[idx, "numero"], df.at[idx, "numero_completo"], df.at[idx, "data_analise"] = datetime.now().year, num, comp, datetime.now().strftime("%d/%m/%Y %H:%M")
                df.to_csv(ARQUIVO, index=False)
                st.success("Salvo!")
                st.rerun()

# ================= VISÃO GERAL =================
st.divider()
st.header("📊 Painel do Gestor")
if not df.empty:
    st.dataframe(df.sort_values(by=["ano", "numero"], ascending=[False, False]), use_container_width=True, hide_index=True)

# ================= ADMIN =================
st.divider()
st.sidebar.header("⚙️ Administração")

with st.sidebar.expander("🗑️ Excluir Dados"):
    tipo_exclusao = st.radio("O que deseja excluir?", ["Uma Linha", "Base Inteira"])
    
    if tipo_exclusao == "Uma Linha":
        id_para_excluir = st.number_input("Digite o ID da Nota", min_value=1, step=1)
        confirma_um = st.checkbox("Confirmo a exclusão desta linha.")
        senha_um = st.text_input("Senha Admin", type="password", key="senha_um")
        
        if st.button("Excluir Linha"):
            if senha_um == SENHA_ADMIN and confirma_um:
                df = df[df["id_nota"] != id_para_excluir]
                df.to_csv(ARQUIVO, index=False)
                st.success(f"ID {id_para_excluir} removido.")
                st.rerun()
            else:
                st.error("Senha incorreta ou falta de confirmação.")

    else:
        confirma_tudo = st.checkbox("⚠️ CONFIRMO APAGAR TODA A BASE.")
        senha_tudo = st.text_input("Senha Admin", type="password", key="senha_tudo")
        
        if st.button("Zerar Sistema"):
            if senha_tudo == SENHA_ADMIN and confirma_tudo:
                df = pd.DataFrame(columns=df.columns)
                df.to_csv(ARQUIVO, index=False)
                st.success("Base resetada!")
                st.rerun()
            else:
                st.error("Ação negada.")
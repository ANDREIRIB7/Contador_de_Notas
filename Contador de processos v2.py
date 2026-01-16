import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ================= CONFIGURAÇÕES =================
SENHA_ADMIN = "Progen123"
ARQUIVO = "notas.csv"

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
    # Filtra apenas registros que têm ano e número válidos
    df_verificado = df_base[pd.to_numeric(df_base["ano"], errors="coerce").notna()]
    df_ano = df_verificado[df_verificado["ano"].astype(float) == ano_atual].copy()
    if df_ano.empty:
        proximo = 1
    else:
        proximo = int(pd.to_numeric(df_ano["numero"]).max()) + 1
    return proximo, f"{proximo:04d}/{ano_atual}"

# ================= CARREGAR / INICIALIZAR BASE =================
col_obrig = ["id_nota", "nome_nota", "num_sei", "flag_obrigatorio", "ano", "numero", "numero_completo", "colaborador", "cargo", "status", "data_criacao", "data_analise", "publicada"]

if not os.path.exists(ARQUIVO):
    df = pd.DataFrame(columns=col_obrig)
    df.to_csv(ARQUIVO, index=False)
else:
    df = pd.read_csv(ARQUIVO)
    
    # Garante que colunas novas existam sem estragar os IDs
    for col in col_obrig:
        if col not in df.columns:
            df[col] = None 

    # Limpa linhas fantasmas
    df = df.dropna(subset=['nome_nota'], how='all')

    # 🛡️ VACINA CONTRA ID INVÁLIDO:
    # Tenta converter IDs para número. Se der erro (como o 'Não'), vira NaN
    df["id_nota"] = pd.to_numeric(df["id_nota"], errors="coerce")
    
    # Se algum ID ficou inválido, reconstrói a sequência para não travar o sistema
    if df["id_nota"].isna().any():
        df["id_nota"] = range(1, len(df) + 1)
    
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")

# ================= INTERFACE VISUAL =================
st.title("🏛️ Sistema de Gestão de Notas Técnicas")
prox_idx, prox_str = gerar_numero_nota(df)

st.metric(label="🔢 Próximo Número de Série", value=prox_str)
st.divider()

# ================= CADASTRO =================
with st.expander("🆕 Cadastrar Novo Processo"):
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
                nova_linha = {"id_nota": novo_id, "nome_nota": nome_novo, "num_sei": num_sei_novo, "flag_obrigatorio": flag_novo, "colaborador": colab_novo, "cargo": COLABORADORES[colab_novo], "status": status_novo, "data_criacao": data_agora, "ano": None, "numero": None, "numero_completo": None, "data_analise": None, "publicada": "Não"}
                
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
    # Criando lista de opções com proteção total
    opcoes = []
    for _, row_data in df.iterrows():
        id_val = int(row_data['id_nota'])
        nome_val = row_data['nome_nota']
        opcoes.append(f"ID {id_val} - {nome_val}")
    
    sel = st.selectbox("Selecione para editar", ["— Selecione —"] + opcoes)
    
    if sel != "— Selecione —":
        id_sel = int(sel.split("ID ")[1].split(" -")[0])
        idx_lista = df.index[df['id_nota'] == id_sel].tolist()
        
        if idx_lista:
            idx = idx_lista[0]
            row = df.loc[idx]
            with st.container(border=True):
                ce1, ce2 = st.columns(2)
                with ce1:
                    n_nome = st.text_input("Editar Nome", value=row["nome_nota"])
                    n_sei = st.text_input("Editar Nº SEI", value="" if pd.isna(row["num_sei"]) else str(row["num_sei"]))
                with ce2:
                    status_list = ["Em elaboração", "Em análise", "Concluído"]
                    status_atual = row["status"] if row["status"] in status_list else "Em elaboração"
                    n_status = st.selectbox("Status", status_list, index=status_list.index(status_atual))
                    n_flag = st.checkbox("NT com número inicial obrigatório", value=bool(row["flag_obrigatorio"]))
                
                n_publicada = row["publicada"] if pd.notna(row["publicada"]) else "Não"
                if n_status == "Concluído":
                    st.warning("⚠️ Pergunta obrigatória para conclusão:")
                    n_publicada = st.radio("A NOTA SERÁ PUBLICADA?", ["Sim", "Não"], index=0 if n_publicada == "Sim" else 1, horizontal=True)

                if st.button("Salvar Alterações"):
                    df.at[idx, "nome_nota"] = n_nome
                    df.at[idx, "num_sei"] = n_sei
                    df.at[idx, "flag_obrigatorio"] = n_flag
                    df.at[idx, "status"] = n_status
                    df.at[idx, "publicada"] = n_publicada
                    
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
    df_exibicao = df.sort_values(by=["ano", "numero", "id_nota"], ascending=[False, False, False])
    df_final = df_exibicao.rename(columns={
        "id_nota": "ID", "numero_completo": "NÚMERO", "nome_nota": "ASSUNTO",
        "num_sei": "PROCESSO SEI", "status": "STATUS", "publicada": "PUBLICADA?", "colaborador": "RESPONSÁVEL"
    })
    st.dataframe(df_final[["ID", "NÚMERO", "ASSUNTO", "PROCESSO SEI", "STATUS", "PUBLICADA?", "RESPONSÁVEL"]], use_container_width=True, hide_index=True)

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

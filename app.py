import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta


# ======================================================
# CONFIG
# ======================================================

st.set_page_config(layout="wide")
st.title("Scanner CMF e KVO – Diário com autorização semanal e Semanal operacional")


# ======================================================
# FUNÇÕES DE DADOS
# ======================================================

def baixar_dados(ticker, intervalo):
    df = yf.download(
        ticker,
        period="2y",
        interval=intervalo,
        progress=False
    )
    if df is None or df.empty:
        return None

    df = df.rename(columns=str.title)
    return df


# ======================================================
# FILTRO DE TENDÊNCIA (seu padrão)
# ======================================================

def filtros_tendencia(df):

    if len(df) < 80:
        return False

    df = df.copy()

    df["EMA69"] = ta.ema(df["Close"], length=69)

    dmi = ta.adx(
        df["High"],
        df["Low"],
        df["Close"],
        length=14
    )

    df = pd.concat([df, dmi], axis=1)

    if pd.isna(df["EMA69"].iloc[-1]):
        return False

    # Close acima da EMA69
    if df["Close"].iloc[-1] <= df["EMA69"].iloc[-1]:
        return False

    # EMA69 ascendente
    if df["EMA69"].iloc[-1] <= df["EMA69"].iloc[-2]:
        return False

    # D+ acima do D-
    if df["DMP_14"].iloc[-1] <= df["DMN_14"].iloc[-1]:
        return False

    return True


# ======================================================
# AUTORIZAÇÃO SEMANAL PARA ENTRADAS DO DIÁRIO
# ======================================================

def autorizacao_semanal(df_semanal):

    return filtros_tendencia(df_semanal)


# ======================================================
# SETUP CMF – diário
# ======================================================

def setup_cmf(df):

    if len(df) < 30:
        return False

    df = df.copy()

    df["CMF"] = ta.cmf(
        df["High"],
        df["Low"],
        df["Close"],
        df["Volume"],
        length=20
    )

    # gatilho: cruzamento do CMF para cima da linha zero
    if (
        df["CMF"].iloc[-2] <= 0
        and df["CMF"].iloc[-1] > 0
    ):
        return True

    return False


# ======================================================
# SETUP KVO – diário / semanal
# ======================================================

def setup_kvo(df):

    if len(df) < 40:
        return False

    df = df.copy()

    kvo = ta.kvo(
        df["High"],
        df["Low"],
        df["Close"],
        df["Volume"]
    )

    df = pd.concat([df, kvo], axis=1)

    if "KVO_34_55_13" not in df.columns:
        return False

    kvo_col = "KVO_34_55_13"
    sig_col = "KVOs_34_55_13"

    # gatilho: KVO cruza para cima da sua média
    if (
        df[kvo_col].iloc[-2] <= df[sig_col].iloc[-2]
        and df[kvo_col].iloc[-1] > df[sig_col].iloc[-1]
    ):
        return True

    return False


# ======================================================
# INTERFACE
# ======================================================

tickers_txt = st.text_area(
    "Lista de ativos (um por linha – padrão B3, ex: PETR4.SA)",
    height=200
)

if st.button("Rodar scanner"):

    tickers = [
        t.strip().upper()
        for t in tickers_txt.splitlines()
        if t.strip()
    ]

    entradas_diarias = []
    entradas_semanais = []

    for t in tickers:

        try:

            df_d = baixar_dados(t, "1d")
            df_w = baixar_dados(t, "1wk")

            if df_d is None or df_w is None:
                continue

            df_d = df_d.dropna()
            df_w = df_w.dropna()

            # -------------------------------
            # SEMANAL OPERACIONAL
            # -------------------------------

            if filtros_tendencia(df_w):

                if setup_cmf(df_w):
                    entradas_semanais.append({
                        "Ativo": t.replace(".SA", ""),
                        "Setup": "CMF semanal"
                    })

                if setup_kvo(df_w):
                    entradas_semanais.append({
                        "Ativo": t.replace(".SA", ""),
                        "Setup": "KVO semanal"
                    })

            # -------------------------------
            # DIÁRIO COM AUTORIZAÇÃO SEMANAL
            # -------------------------------

            if not autorizacao_semanal(df_w):
                continue

            # aqui entram os gatilhos diários

            if setup_cmf(df_d):
                entradas_diarias.append({
                    "Ativo": t.replace(".SA", ""),
                    "Setup": "CMF diário"
                })

            if setup_kvo(df_d):
                entradas_diarias.append({
                    "Ativo": t.replace(".SA", ""),
                    "Setup": "KVO diário"
                })

        except Exception as e:
            pass

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Entradas no gráfico diário (já autorizadas pelo semanal)")

        if entradas_diarias:
            st.dataframe(
                pd.DataFrame(entradas_diarias),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum sinal diário autorizado.")

    with col2:
        st.subheader("Entradas no gráfico semanal")

        if entradas_semanais:
            st.dataframe(
                pd.DataFrame(entradas_semanais),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum sinal semanal.")


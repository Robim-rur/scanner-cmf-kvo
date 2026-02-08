import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Scanner B3 – Diário autorizado pelo Semanal + Semanal OBV",
    layout="wide"
)

# =====================================================
# LISTAS DE ATIVOS
# =====================================================
acoes_100 = [
    "RRRP3.SA","ALOS3.SA","ALPA4.SA","ABEV3.SA","ARZZ3.SA","ASAI3.SA","AZUL4.SA","B3SA3.SA","BBAS3.SA","BBDC3.SA",
    "BBDC4.SA","BBSE3.SA","BEEF3.SA","BPAC11.SA","BRAP4.SA","BRFS3.SA","BRKM5.SA","CCRO3.SA","CMIG4.SA","CMIN3.SA",
    "COGN3.SA","CPFE3.SA","CPLE6.SA","CRFB3.SA","CSAN3.SA","CSNA3.SA","CYRE3.SA","DXCO3.SA","EGIE3.SA","ELET3.SA",
    "ELET6.SA","EMBR3.SA","ENEV3.SA","ENGI11.SA","EQTL3.SA","EZTC3.SA","FLRY3.SA","GGBR4.SA","GOAU4.SA","GOLL4.SA",
    "HAPV3.SA","HYPE3.SA","ITSA4.SA","ITUB4.SA","JBSS3.SA","KLBN11.SA","LREN3.SA","LWSA3.SA","MGLU3.SA","MRFG3.SA",
    "MRVE3.SA","MULT3.SA","NTCO3.SA","PETR3.SA","PETR4.SA","PRIO3.SA","RADL3.SA","RAIL3.SA","RAIZ4.SA","RENT3.SA",
    "RECV3.SA","SANB11.SA","SBSP3.SA","SLCE3.SA","SMTO3.SA","SUZB3.SA","TAEE11.SA","TIMS3.SA","TOTS3.SA","TRPL4.SA",
    "UGPA3.SA","USIM5.SA","VALE3.SA","VIVT3.SA","VIVA3.SA","WEGE3.SA","YDUQ3.SA","AURE3.SA","BHIA3.SA","CASH3.SA",
    "CVCB3.SA","DIRR3.SA","ENAT3.SA","GMAT3.SA","IFCM3.SA","INTB3.SA","JHSF3.SA","KEPL3.SA","MOVI3.SA","ORVR3.SA",
    "PETZ3.SA","PLAS3.SA","POMO4.SA","POSI3.SA","RANI3.SA","RAPT4.SA","STBP3.SA","TEND3.SA","TUPY3.SA",
    "BRSR6.SA","CXSE3.SA"
]

bdrs_50 = [
    "AAPL34.SA","AMZO34.SA","GOGL34.SA","MSFT34.SA","TSLA34.SA","META34.SA","NFLX34.SA","NVDC34.SA","MELI34.SA",
    "BABA34.SA","DISB34.SA","PYPL34.SA","JNJB34.SA","PGCO34.SA","KOCH34.SA","VISA34.SA","WMTB34.SA","NIKE34.SA",
    "ADBE34.SA","AVGO34.SA","CSCO34.SA","COST34.SA","CVSH34.SA","GECO34.SA","GSGI34.SA","HDCO34.SA","INTC34.SA",
    "JPMC34.SA","MAEL34.SA","MCDP34.SA","MDLZ34.SA","MRCK34.SA","ORCL34.SA","PEP334.SA","PFIZ34.SA","PMIC34.SA",
    "QCOM34.SA","SBUX34.SA","TGTB34.SA","TMOS34.SA","TXN34.SA","UNHH34.SA","UPSB34.SA","VZUA34.SA",
    "ABTT34.SA","AMGN34.SA","AXPB34.SA","BAOO34.SA","CATP34.SA","HONB34.SA"
]

etfs_fiis_24 = [
    "BOVA11.SA","IVVB11.SA","SMAL11.SA","HASH11.SA","GOLD11.SA","GARE11.SA","HGLG11.SA","XPLG11.SA","VILG11.SA",
    "BRCO11.SA","BTLG11.SA","XPML11.SA","VISC11.SA","HSML11.SA","MALL11.SA","KNRI11.SA","JSRE11.SA","PVBI11.SA",
    "HGRE11.SA","MXRF11.SA","KNCR11.SA","KNIP11.SA","CPTS11.SA","IRDM11.SA",
    "DIVO11.SA","NDIV11.SA","SPUB11.SA"
]

ativos_scan = sorted(set(acoes_100 + bdrs_50 + etfs_fiis_24))

# =====================================================
# AUTORIZAÇÃO SEMANAL (REGIME)
# =====================================================
def autorizado_semanal(df):

    if df is None or len(df) < 80:
        return False

    df = df.copy()

    df["EMA69"] = ta.ema(df["Close"], length=69)

    adx = ta.adx(df["High"], df["Low"], df["Close"], length=14)
    df = pd.concat([df, adx], axis=1)

    # candle fechado
    idx = -2

    # tendência
    if df["EMA69"].iloc[idx] <= df["EMA69"].iloc[idx - 1]:
        return False

    # preço acima da média
    if df["Close"].iloc[idx] <= df["EMA69"].iloc[idx]:
        return False

    # direção
    if df["DMP_14"].iloc[idx] <= df["DMN_14"].iloc[idx]:
        return False

    # força mínima
    if df["ADX_14"].iloc[idx] < 15:
        return False

    return True


# =====================================================
# SETUP DIÁRIO – 123 / INSIDE (gatilho)
# =====================================================
def procurar_setup_diario(df):

    if df is None or len(df) < 80:
        return None

    df = df.copy()
    df["EMA69"] = ta.ema(df["Close"], length=69)

    # candle fechado
    preco_fechamento = df["Close"].iloc[-1]

    # filtro de tendência diária
    if df["EMA69"].iloc[-1] <= df["EMA69"].iloc[-2]:
        return None

    for i in range(-6, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        is_123 = c2["Low"] < c1["Low"] and c3["Low"] > c2["Low"]
        is_inside = c3["High"] <= c2["High"] and c3["Low"] >= c2["Low"]

        if is_123 or is_inside:

            entrada = round(max(c2["High"], c3["High"]), 2)
            stop = round(c2["Low"], 2)

            return {
                "Setup": "Diário 123 / Inside",
                "Preço Fechamento": round(preco_fechamento, 2),
                "Entrada Técnica": entrada,
                "Stop Técnico": stop
            }

    return None


# =====================================================
# SETUP SEMANAL OPERACIONAL – OBV
# =====================================================
def procurar_setup_semanal_obv(df):

    if df is None or len(df) < 80:
        return None

    df = df.copy()

    df["EMA69"] = ta.ema(df["Close"], length=69)

    df["OBV"] = ta.obv(df["Close"], df["Volume"])
    df["OBV_EMA21"] = ta.ema(df["OBV"], length=21)

    idx = -2  # candle fechado

    # tendência
    if df["EMA69"].iloc[idx] <= df["EMA69"].iloc[idx - 1]:
        return None

    if df["Close"].iloc[idx] <= df["EMA69"].iloc[idx]:
        return None

    # fluxo
    if df["OBV"].iloc[idx] <= df["OBV_EMA21"].iloc[idx]:
        return None

    # rompimento das máximas das últimas 10 semanas (anteriores)
    max_10 = df["High"].rolling(10).max().iloc[idx - 1]

    close = df["Close"].iloc[idx]
    high = df["High"].iloc[idx]
    low = df["Low"].iloc[idx]

    if close <= max_10:
        return None

    # fechamento na metade superior do candle
    range_candle = high - low
    if range_candle == 0:
        return None

    pos = (close - low) / range_candle

    if pos < 0.5:
        return None

    return {
        "Setup": "Semanal OBV",
        "Preço Fechamento": round(close, 2),
        "Rompimento": round(max_10, 2)
    }


# =====================================================
# EXECUÇÃO
# =====================================================
def executar():

    st.title("📈 Scanner B3 – Diário autorizado pelo Semanal + Semanal OBV")

    st.write(f"Ativos monitorados: {len(ativos_scan)}")

    if st.button("🔍 Escanear"):

        resultados_diario = []
        resultados_semanal_obv = []

        progress = st.progress(0)

        dados_diarios = yf.download(
            ativos_scan,
            period="1y",
            interval="1d",
            group_by="ticker",
            progress=False
        )

        dados_semanais = yf.download(
            ativos_scan,
            period="5y",
            interval="1wk",
            group_by="ticker",
            progress=False
        )

        for i, ativo in enumerate(ativos_scan):

            try:
                df_w = dados_semanais[ativo].dropna()
                autorizado = autorizado_semanal(df_w)
            except:
                autorizado = False

            # diário só aparece se semanal autorizar
            if autorizado:
                try:
                    df_d = dados_diarios[ativo].dropna()
                    res_d = procurar_setup_diario(df_d)

                    if res_d:
                        res_d["Ativo"] = ativo.replace(".SA", "")
                        resultados_diario.append(res_d)
                except:
                    pass

            # semanal operacional independente
            try:
                df_w2 = dados_semanais[ativo].dropna()
                res_obv = procurar_setup_semanal_obv(df_w2)

                if res_obv:
                    res_obv["Ativo"] = ativo.replace(".SA", "")
                    resultados_semanal_obv.append(res_obv)
            except:
                pass

            progress.progress((i + 1) / len(ativos_scan))

        st.subheader("📌 Entradas no gráfico diário (autorizadas pelo semanal)")

        if resultados_diario:
            st.dataframe(pd.DataFrame(resultados_diario), use_container_width=True)
        else:
            st.warning("Nenhum sinal diário autorizado pelo semanal.")

        st.subheader("📌 Entradas no gráfico semanal – Setup OBV")

        if resultados_semanal_obv:
            st.dataframe(pd.DataFrame(resultados_semanal_obv), use_container_width=True)
        else:
            st.warning("Nenhum sinal no setup semanal OBV.")


if __name__ == "__main__":
    executar()

import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta

st.set_page_config(
    page_title="Scanner B3 – CMF e KVO (Diário autorizado pelo semanal + Semanal independente)",
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
# FILTROS
# =====================================================
def filtro_tendencia_simples(df):

    if df is None or len(df) < 80:
        return None

    df = df.copy()
    df["EMA69"] = ta.ema(df["Close"], length=69)

    if df["Close"].iloc[-1] <= df["EMA69"].iloc[-1]:
        return None

    if df["EMA69"].iloc[-1] <= df["EMA69"].iloc[-2]:
        return None

    return df


def filtro_tendencia_rigido(df, adx_min):

    if df is None or len(df) < 80:
        return None

    df = df.copy()
    df["EMA69"] = ta.ema(df["Close"], length=69)

    dmi = ta.adx(df["High"], df["Low"], df["Close"], length=14)
    df = pd.concat([df, dmi], axis=1)

    if df["Close"].iloc[-1] <= df["EMA69"].iloc[-1]:
        return None

    if df["EMA69"].iloc[-1] <= df["EMA69"].iloc[-2]:
        return None

    if df["DMP_14"].iloc[-1] <= df["DMN_14"].iloc[-1]:
        return None

    if df["ADX_14"].iloc[-1] < adx_min:
        return None

    return df


# =====================================================
# AUTORIZAÇÃO SEMANAL PARA O DIÁRIO (BRANDA)
# =====================================================
def autoriza_semanal(df_w):

    df = filtro_tendencia_simples(df_w)
    if df is None:
        return False

    return True


# =====================================================
# SETUPS DIÁRIOS
# =====================================================
def setup_cmf_diario(df_d):

    df = filtro_tendencia_rigido(df_d, adx_min=12)
    if df is None:
        return False

    df["CMF"] = ta.cmf(df["High"], df["Low"], df["Close"], df["Volume"], length=20)

    return df["CMF"].iloc[-2] < 0 and df["CMF"].iloc[-1] > 0


def setup_kvo_diario(df_d):

    df = filtro_tendencia_rigido(df_d, adx_min=12)
    if df is None:
        return False

    kvo = ta.kvo(df["High"], df["Low"], df["Close"], df["Volume"])
    df = pd.concat([df, kvo], axis=1)

    kvo_col = [c for c in df.columns if c.startswith("KVO_") and not c.lower().startswith("kvos")][0]
    sig_col = [c for c in df.columns if c.startswith("KVOs_")][0]

    return (
        df[kvo_col].iloc[-2] <= df[sig_col].iloc[-2]
        and df[kvo_col].iloc[-1] > df[sig_col].iloc[-1]
    )


# =====================================================
# SETUPS SEMANAIS INDEPENDENTES (RÍGIDOS)
# =====================================================
def setup_cmf_semanal(df_w):

    df = filtro_tendencia_rigido(df_w, adx_min=18)
    if df is None:
        return False

    df["CMF"] = ta.cmf(df["High"], df["Low"], df["Close"], df["Volume"], length=20)

    return df["CMF"].iloc[-2] < 0 and df["CMF"].iloc[-1] > 0


def setup_kvo_semanal(df_w):

    df = filtro_tendencia_rigido(df_w, adx_min=18)
    if df is None:
        return False

    kvo = ta.kvo(df["High"], df["Low"], df["Close"], df["Volume"])
    df = pd.concat([df, kvo], axis=1)

    kvo_col = [c for c in df.columns if c.startswith("KVO_") and not c.lower().startswith("kvos")][0]
    sig_col = [c for c in df.columns if c.startswith("KVOs_")][0]

    return (
        df[kvo_col].iloc[-2] <= df[sig_col].iloc[-2]
        and df[kvo_col].iloc[-1] > df[sig_col].iloc[-1]
    )


# =====================================================
# EXECUÇÃO
# =====================================================
def executar():

    st.title("📊 Scanner – CMF e KVO")

    if st.button("🔍 Escanear"):

        res_diario = []
        res_semanal = []

        dados_d = yf.download(ativos_scan, period="1y", interval="1d", group_by="ticker", progress=False)
        dados_w = yf.download(ativos_scan, period="5y", interval="1wk", group_by="ticker", progress=False)

        progress = st.progress(0)

        for i, ativo in enumerate(ativos_scan):

            try:
                df_d = dados_d[ativo].dropna()
                df_w = dados_w[ativo].dropna()

                if autoriza_semanal(df_w):

                    if setup_cmf_diario(df_d):
                        res_diario.append({
                            "Ativo": ativo.replace(".SA",""),
                            "Setup": "CMF Diário",
                            "Entrada": "Abertura do próximo pregão"
                        })

                    if setup_kvo_diario(df_d):
                        res_diario.append({
                            "Ativo": ativo.replace(".SA",""),
                            "Setup": "KVO Diário",
                            "Entrada": "Abertura do próximo pregão"
                        })

                if setup_cmf_semanal(df_w):
                    res_semanal.append({
                        "Ativo": ativo.replace(".SA",""),
                        "Setup": "CMF Semanal",
                        "Entrada": "Abertura da próxima semana"
                    })

                if setup_kvo_semanal(df_w):
                    res_semanal.append({
                        "Ativo": ativo.replace(".SA",""),
                        "Setup": "KVO Semanal",
                        "Entrada": "Abertura da próxima semana"
                    })

            except:
                pass

            progress.progress((i + 1) / len(ativos_scan))

        st.subheader("Entradas no gráfico diário (com autorização do semanal)")
        if res_diario:
            st.dataframe(pd.DataFrame(res_diario), use_container_width=True)
        else:
            st.warning("Nenhum sinal diário.")

        st.subheader("Entradas no gráfico semanal (setup independente)")
        if res_semanal:
            st.dataframe(pd.DataFrame(res_semanal), use_container_width=True)
        else:
            st.warning("Nenhum sinal semanal.")


if __name__ == "__main__":
    executar()


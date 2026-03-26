"""
BCBA Swing Analyzer
Herramienta de análisis técnico para el mercado de capitales argentino.
Panel Líder + Panel General | Swing Trading
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta
import warnings

warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════
#  PAGE CONFIG
# ════════════════════════════════════════════════════════
st.set_page_config(
    page_title="BCBA Swing Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════
#  TICKERS
# ════════════════════════════════════════════════════════
PANEL_LIDER = [
    "ALUA", "BBAR", "BMA", "BYMA", "CEPU", "COME", "CRES", "CVH",
    "EDN", "GGAL", "HARG", "LOMA", "MIRG", "PAMP", "SUPV",
    "TECO2", "TGNO4", "TGSU2", "TRAN", "TXAR", "VALO", "YPFD",
]

PANEL_GENERAL = [
    "AGRO", "ALEC", "AUSO", "BPAT", "BRIO", "CAPU", "CAPX",
    "CGPA2", "CLOR", "CECO2", "CELU", "DGCU2", "DYCA", "ESME",
    "FERR", "FIPL", "GAMI", "GARO", "GBAN", "GCDI", "GCLA",
    "HAVA", "INTR", "INVJ", "IRSA", "KLIC", "LEDE", "LONG",
    "METR", "MOLI", "MORI", "MTCR", "NGSM", "OEST", "ORAN",
    "PATA", "POLL", "PSUR", "REGE", "RICH", "RIGO", "ROSE",
    "RUSA", "SAMI", "SEMI", "TGLT", "TPAU", "TXAR", "VGCO",
]

# Nombres legibles
NOMBRES = {
    "ALUA": "Aluar", "BBAR": "BBVA Argentina", "BMA": "Banco Macro",
    "BYMA": "BYMA", "CEPU": "Central Puerto", "COME": "Sociedad Comercial del Plata",
    "CRES": "Cresud", "CVH": "Cablevision Holding", "EDN": "Edenor",
    "GGAL": "Grupo Financiero Galicia", "HARG": "Holcim Argentina",
    "LOMA": "Loma Negra", "MIRG": "Mirgor", "PAMP": "Pampa Energía",
    "SUPV": "Supervielle", "TECO2": "Telecom Argentina", "TGNO4": "Transportadora Gas Norte",
    "TGSU2": "Transportadora Gas Sur", "TRAN": "Transener", "TXAR": "Ternium Argentina",
    "VALO": "Grupo Supervielle", "YPFD": "YPF",
    "AGRO": "AgroIndustrial", "IRSA": "IRSA", "METR": "Metrogas",
}

SECTORES = {
    "YPFD": "Energía", "PAMP": "Energía", "CEPU": "Energía", "EDN": "Energía",
    "TGSU2": "Energía", "TGNO4": "Energía", "TRAN": "Energía",
    "GGAL": "Financiero", "BMA": "Financiero", "BBAR": "Financiero",
    "SUPV": "Financiero", "BYMA": "Financiero", "VALO": "Financiero",
    "TXAR": "Industria", "ALUA": "Industria", "LOMA": "Construcción",
    "HARG": "Construcción", "TECO2": "Telecomunicaciones",
    "CVH": "Telecomunicaciones", "CRES": "Agropecuario",
}


# ════════════════════════════════════════════════════════
#  INDICADORES TÉCNICOS (vectorizados con numpy/pandas)
# ════════════════════════════════════════════════════════
def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram


def calc_bollinger(close: pd.Series, period=20, num_std=2):
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    bandwidth = (upper - lower) / sma.replace(0, np.nan)
    return upper, sma, lower, pct_b, bandwidth


def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k=14, d=3):
    lowest_low = low.rolling(k).min()
    highest_high = high.rolling(k).max()
    denom = (highest_high - lowest_low).replace(0, np.nan)
    k_line = 100 * (close - lowest_low) / denom
    d_line = k_line.rolling(d).mean()
    return k_line, d_line


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def calc_rvol(volume: pd.Series, period=20) -> pd.Series:
    avg = volume.rolling(period).mean().replace(0, np.nan)
    return volume / avg


def calc_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series, lookback=20) -> dict:
    recent_high = high.rolling(lookback).max().iloc[-1]
    recent_low = low.rolling(lookback).min().iloc[-1]
    pivot = (recent_high + recent_low + close.iloc[-1]) / 3
    r1 = 2 * pivot - recent_low
    s1 = 2 * pivot - recent_high
    r2 = pivot + (recent_high - recent_low)
    s2 = pivot - (recent_high - recent_low)
    return {
        "soporte": round(s1, 2),
        "resistencia": round(r1, 2),
        "pivot": round(pivot, 2),
        "s2": round(s2, 2),
        "r2": round(r2, 2),
    }


# ════════════════════════════════════════════════════════
#  SCORING
# ════════════════════════════════════════════════════════
def score_ticker(df: pd.DataFrame) -> tuple[int, list[str]]:
    """Calcula score de swing (0–100) y lista de señales detectadas."""
    if df is None or len(df) < 35:
        return 0, []

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    signals: list[str] = []
    score = 0

    # — RSI —
    rsi = calc_rsi(close)
    rsi_last = rsi.iloc[-1]
    if rsi_last < 30:
        score += 22
        signals.append(f"RSI sobrevendido ({rsi_last:.1f}) ⚡")
    elif rsi_last < 40:
        score += 12
        signals.append(f"RSI en zona de compra ({rsi_last:.1f}) ✅")
    elif rsi_last > 70:
        score -= 15
        signals.append(f"RSI sobrecomprado ({rsi_last:.1f}) ⚠️")
    elif 45 < rsi_last < 60:
        score += 5
        signals.append(f"RSI neutro ({rsi_last:.1f})")

    # — MACD —
    macd, signal_line, hist = calc_macd(close)
    h_last, h_prev = hist.iloc[-1], hist.iloc[-2]
    if h_last > 0 and h_prev <= 0:
        score += 28
        signals.append("Cruce MACD alcista ⚡")
    elif h_last > 0 and h_last > h_prev:
        score += 15
        signals.append("MACD histograma creciente ✅")
    elif h_last < 0 and h_prev >= 0:
        score -= 25
        signals.append("Cruce MACD bajista ⚠️")
    elif h_last < 0:
        score -= 8
        signals.append("MACD negativo")

    # — Bollinger Bands —
    upper, mid, lower, pct_b, bw = calc_bollinger(close)
    pb_last = pct_b.iloc[-1]
    bw_last = bw.iloc[-1]
    bw_avg = bw.rolling(50).mean().iloc[-1]
    if pb_last < 0.15:
        score += 22
        signals.append("Precio en banda inferior BB ⚡")
    elif pb_last > 0.85:
        score -= 12
        signals.append("Precio en banda superior BB ⚠️")
    if not np.isnan(bw_avg) and bw_last < bw_avg * 0.75:
        score += 12
        signals.append("Compresión BB — breakout potencial 🎯")

    # — Estocástico —
    k_line, d_line = calc_stochastic(high, low, close)
    k_last, d_last = k_line.iloc[-1], d_line.iloc[-1]
    k_prev, d_prev = k_line.iloc[-2], d_line.iloc[-2]
    if k_last < 20 and d_last < 20:
        score += 18
        signals.append(f"Estocástico sobrevendido ({k_last:.0f}/{d_last:.0f}) ⚡")
    elif k_last > k_prev and d_last > d_prev and k_last < 50:
        score += 8
        signals.append(f"Estocástico girando al alza ✅")
    elif k_last > 80 and d_last > 80:
        score -= 12
        signals.append(f"Estocástico sobrecomprado ({k_last:.0f}/{d_last:.0f}) ⚠️")

    # — Volumen relativo —
    rvol = calc_rvol(volume)
    rvol_last = rvol.iloc[-1]
    if rvol_last > 2.0:
        score += 12
        signals.append(f"Volumen muy elevado (RVOL {rvol_last:.1f}x) 📊")
    elif rvol_last > 1.4:
        score += 6
        signals.append(f"Volumen elevado (RVOL {rvol_last:.1f}x) 📊")

    # — Tendencia SMA —
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    precio = close.iloc[-1]
    if precio > sma20 > sma50:
        score += 10
        signals.append("Tendencia alcista (P > SMA20 > SMA50) ✅")
    elif sma20 > sma50 and precio < sma20:
        score += 5
        signals.append("Tendencia positiva, precio bajo SMA20 (pullback)")
    elif precio < sma20 < sma50:
        score -= 10
        signals.append("Tendencia bajista")

    # — Variación reciente —
    if len(close) >= 10:
        var_5d = (close.iloc[-1] / close.iloc[-5] - 1) * 100
        if -3 < var_5d < 0:
            score += 5
            signals.append(f"Corrección moderada ({var_5d:.1f}%) — zona de entrada")

    return max(0, min(100, score)), signals


# ════════════════════════════════════════════════════════
#  DATA FETCHING
# ════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def fetch_batch(tickers_ba: list[str], period: str) -> pd.DataFrame | None:
    try:
        raw = yf.download(
            tickers_ba,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        return raw
    except Exception:
        return None


def extract_ticker_df(raw: pd.DataFrame, ticker_ba: str) -> pd.DataFrame | None:
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            df = raw.xs(ticker_ba, axis=1, level=1).dropna()
        else:
            df = raw.dropna()
        return df if len(df) >= 35 else None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def build_screening_table(panel_key: str, period: str) -> pd.DataFrame:
    panel_map = {
        "Panel Líder": PANEL_LIDER,
        "Panel General": PANEL_GENERAL,
        "Ambos": PANEL_LIDER + PANEL_GENERAL,
    }
    tickers = panel_map[panel_key]
    tickers_ba = [t + ".BA" for t in tickers]

    raw = fetch_batch(tickers_ba, period)
    if raw is None or raw.empty:
        return pd.DataFrame()

    rows = []
    for ticker, ticker_ba in zip(tickers, tickers_ba):
        df = extract_ticker_df(raw, ticker_ba)
        if df is None:
            continue

        score, signals = score_ticker(df)
        close = df["Close"]

        var_1d = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
        var_5d = ((close.iloc[-1] / close.iloc[-5]) - 1) * 100 if len(close) > 5 else 0
        var_20d = ((close.iloc[-1] / close.iloc[-20]) - 1) * 100 if len(close) > 20 else 0

        rsi_val = calc_rsi(close).iloc[-1]
        _, _, hist = calc_macd(close)
        atr_val = calc_atr(df["High"], df["Low"], close).iloc[-1]
        rvol_val = calc_rvol(df["Volume"]).iloc[-1]
        sr = calc_support_resistance(df["High"], df["Low"], close)
        k_val, _ = calc_stochastic(df["High"], df["Low"], close)

        if score >= 65:
            rec = "🟢 COMPRA"
        elif score >= 45:
            rec = "🟡 NEUTRAL"
        else:
            rec = "🔴 CAUTELA"

        panel = "Líder" if ticker in PANEL_LIDER else "General"
        sector = SECTORES.get(ticker, "—")
        nombre = NOMBRES.get(ticker, ticker)

        rows.append({
            "Ticker": ticker,
            "Nombre": nombre,
            "Panel": panel,
            "Sector": sector,
            "Precio": round(close.iloc[-1], 2),
            "Var 1D%": round(var_1d, 2),
            "Var 5D%": round(var_5d, 2),
            "Var 20D%": round(var_20d, 2),
            "Score": int(score),
            "Señal": rec,
            "RSI": round(rsi_val, 1),
            "Estoc. %K": round(k_val.iloc[-1], 1),
            "MACD Hist": round(hist.iloc[-1], 4),
            "ATR": round(atr_val, 2),
            "RVOL": round(rvol_val, 2),
            "Soporte": sr["soporte"],
            "Pivot": sr["pivot"],
            "Resistencia": sr["resistencia"],
            "# Señales": len(signals),
            "Detalle señales": " | ".join(signals),
            "_df": df,
        })

    df_result = pd.DataFrame(rows)
    if not df_result.empty:
        df_result = df_result.sort_values("Score", ascending=False).reset_index(drop=True)
    return df_result


# ════════════════════════════════════════════════════════
#  GRÁFICO INTERACTIVO
# ════════════════════════════════════════════════════════
def build_chart(
    df: pd.DataFrame, ticker: str,
    show_bb=True, show_macd=True, show_rsi=True, show_stoch=True,
    sr_data: dict | None = None,
) -> go.Figure:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    panel_flags = [show_macd, show_rsi, show_stoch]
    n_rows = 1 + sum(panel_flags)
    row_heights = [0.55] + [0.15] * (n_rows - 1)

    titles = [ticker] + ["MACD"] * show_macd + ["RSI"] * show_rsi + ["Estocástico"] * show_stoch

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.025,
        subplot_titles=titles,
    )

    # Velas
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Precio",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350",
        ),
        row=1, col=1,
    )

    # SMA 20 y 50
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    fig.add_trace(go.Scatter(x=df.index, y=sma20, name="SMA20",
        line=dict(color="#FFA500", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sma50, name="SMA50",
        line=dict(color="#CE93D8", width=1.5)), row=1, col=1)

    # Bollinger
    if show_bb:
        upper, _, lower_bb, _, _ = calc_bollinger(close)
        fig.add_trace(go.Scatter(x=df.index, y=upper, name="BB Sup",
            line=dict(color="rgba(100,181,246,0.6)", width=1, dash="dot"),
            showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower_bb, name="BB Inf",
            line=dict(color="rgba(100,181,246,0.6)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(100,181,246,0.04)",
            showlegend=False), row=1, col=1)

    # Soporte / Resistencia
    if sr_data:
        for level, label, color in [
            (sr_data["soporte"], f"S1 ${sr_data['soporte']:,.0f}", "#4CAF50"),
            (sr_data["resistencia"], f"R1 ${sr_data['resistencia']:,.0f}", "#F44336"),
            (sr_data["pivot"], f"Pivot ${sr_data['pivot']:,.0f}", "#90CAF9"),
        ]:
            fig.add_hline(y=level, line_dash="dash", line_color=color,
                          opacity=0.6, annotation_text=label,
                          annotation_position="right", row=1, col=1)

    current_row = 2

    # MACD
    if show_macd:
        macd, signal_line, hist = calc_macd(close)
        bar_colors = ["#26a69a" if h >= 0 else "#ef5350" for h in hist]
        fig.add_trace(go.Bar(x=df.index, y=hist, name="Histograma",
            marker_color=bar_colors, opacity=0.75), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd, name="MACD",
            line=dict(color="#42A5F5", width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=signal_line, name="Signal",
            line=dict(color="#FFA726", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=0, line_color="gray", opacity=0.3, row=current_row, col=1)
        current_row += 1

    # RSI
    if show_rsi:
        rsi = calc_rsi(close)
        fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI",
            line=dict(color="#EC407A", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ef5350",
                      opacity=0.6, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#26a69a",
                      opacity=0.6, row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray",
                      opacity=0.3, row=current_row, col=1)
        current_row += 1

    # Estocástico
    if show_stoch:
        k, d = calc_stochastic(high, low, close)
        fig.add_trace(go.Scatter(x=df.index, y=k, name="%K",
            line=dict(color="#00BCD4", width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=d, name="%D",
            line=dict(color="#FF7043", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=80, line_dash="dot", line_color="#ef5350",
                      opacity=0.6, row=current_row, col=1)
        fig.add_hline(y=20, line_dash="dot", line_color="#26a69a",
                      opacity=0.6, row=current_row, col=1)

    fig.update_layout(
        height=750,
        template="plotly_dark",
        paper_bgcolor="rgba(14,17,23,0)",
        plot_bgcolor="rgba(14,17,23,0)",
        showlegend=True,
        legend=dict(orientation="h", y=1.04, x=0, font_size=11),
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=60, t=35, b=0),
        font=dict(size=11),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")

    return fig


# ════════════════════════════════════════════════════════
#  ESTILOS CSS
# ════════════════════════════════════════════════════════
CSS = """
<style>
[data-testid="stAppViewContainer"] { background: #0e1117; }
[data-testid="stSidebar"] { background: #161b22; }
.alert-box {
    border-left: 4px solid #26a69a;
    background: rgba(38,166,154,0.08);
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 6px;
    font-size: 13px;
}
.alert-box.warn {
    border-left-color: #FFA726;
    background: rgba(255,167,38,0.08);
}
.sr-card {
    background: #161b22;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
    margin: 4px 0;
}
div[data-testid="metric-container"] {
    background: #161b22;
    border-radius: 8px;
    padding: 10px 14px;
}
</style>
"""


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    # Header
    col_t, col_ts = st.columns([4, 1])
    with col_t:
        st.markdown("## 📈 BCBA Swing Analyzer")
        st.caption(
            f"Datos: Yahoo Finance · Actualización: {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y %H:%M')} hs"
        )
    with col_ts:
        st.markdown("<br>", unsafe_allow_html=True)

    # ── SIDEBAR ────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")

        panel_sel = st.selectbox(
            "Panel",
            ["Panel Líder", "Panel General", "Ambos"],
            help="Panel a analizar",
        )
        period_sel = st.selectbox(
            "Período histórico",
            ["3mo", "6mo", "1y"],
            index=1,
            format_func=lambda x: {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año"}[x],
        )

        st.divider()
        st.markdown("### 🔔 Filtros de Alerta")
        min_score = st.slider("Score mínimo", 0, 100, 55, step=5)
        max_rsi = st.slider("RSI máximo", 30, 80, 60)
        min_rvol = st.slider("RVOL mínimo", 1.0, 3.0, 1.0, step=0.1)

        st.divider()
        st.markdown("### 📊 Indicadores")
        show_bb = st.checkbox("Bollinger Bands", value=True)
        show_macd = st.checkbox("MACD", value=True)
        show_rsi = st.checkbox("RSI", value=True)
        show_stoch = st.checkbox("Estocástico", value=True)
        show_sr = st.checkbox("Soporte / Resistencia", value=True)

        st.divider()
        if st.button("🔄 Actualizar datos", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.caption("Cache: 5 min · Clic en Actualizar para forzar recarga")

    # ── CARGA DE DATOS ──────────────────────────────────
    with st.spinner("⏳ Descargando y procesando datos del mercado…"):
        df_screen = build_screening_table(panel_sel, period_sel)

    if df_screen.empty:
        st.error("❌ No se pudieron cargar los datos. Verificá tu conexión e intentá nuevamente.")
        return

    # ── MÉTRICAS RESUMEN ────────────────────────────────
    n_total = len(df_screen)
    n_compra = (df_screen["Señal"].str.contains("COMPRA")).sum()
    n_neutral = (df_screen["Señal"].str.contains("NEUTRAL")).sum()
    n_cautela = (df_screen["Señal"].str.contains("CAUTELA")).sum()
    avg_score = df_screen["Score"].mean()
    avg_rsi = df_screen["RSI"].mean()
    n_alertas = (
        (df_screen["Score"] >= min_score)
        & (df_screen["RSI"] <= max_rsi)
        & (df_screen["RVOL"] >= min_rvol)
    ).sum()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Tickers", n_total)
    c2.metric("🟢 Compra", n_compra)
    c3.metric("🟡 Neutral", n_neutral)
    c4.metric("🔴 Cautela", n_cautela)
    c5.metric("Score Promedio", f"{avg_score:.0f}")
    c6.metric("🔔 Alertas", n_alertas)

    st.divider()

    # ── TABS ─────────────────────────────────────────────
    tab_screen, tab_alertas, tab_detalle = st.tabs(
        ["📋 Screening", "🔔 Alertas", "🔬 Análisis Individual"]
    )

    # ══════════════════════════
    #  TAB 1 — SCREENING
    # ══════════════════════════
    with tab_screen:
        st.subheader("Ranking técnico — Swing Trading")

        # Filtros rápidos
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_signal = st.multiselect(
                "Señal", ["🟢 COMPRA", "🟡 NEUTRAL", "🔴 CAUTELA"],
                default=["🟢 COMPRA", "🟡 NEUTRAL"],
            )
        with col_f2:
            if "Sector" in df_screen.columns:
                sectores_disp = ["Todos"] + sorted(df_screen["Sector"].dropna().unique().tolist())
                filter_sector = st.selectbox("Sector", sectores_disp)
            else:
                filter_sector = "Todos"
        with col_f3:
            sort_by = st.selectbox(
                "Ordenar por",
                ["Score", "Var 1D%", "Var 5D%", "RSI", "RVOL"],
            )

        df_filtered = df_screen.copy()
        if filter_signal:
            df_filtered = df_filtered[df_filtered["Señal"].isin(filter_signal)]
        if filter_sector != "Todos":
            df_filtered = df_filtered[df_filtered["Sector"] == filter_sector]
        df_filtered = df_filtered.sort_values(sort_by, ascending=(sort_by == "RSI"))

        display_cols = [
            "Ticker", "Panel", "Sector", "Precio", "Var 1D%", "Var 5D%",
            "Score", "Señal", "RSI", "Estoc. %K", "MACD Hist", "RVOL",
            "Soporte", "Resistencia",
        ]
        df_show = df_filtered[display_cols].copy()

        def color_score(val):
            if val >= 65:
                return "background-color: rgba(38,166,154,0.25)"
            elif val >= 45:
                return "background-color: rgba(255,167,38,0.25)"
            return "background-color: rgba(239,83,80,0.20)"

        def color_var(val):
            if val > 0:
                return "color: #26a69a; font-weight:600"
            elif val < 0:
                return "color: #ef5350; font-weight:600"
            return ""

        styled = (
            df_show.style
            .applymap(color_score, subset=["Score"])
            .applymap(color_var, subset=["Var 1D%", "Var 5D%"])
            .format({
                "Precio": "${:,.2f}",
                "Var 1D%": "{:+.2f}%",
                "Var 5D%": "{:+.2f}%",
                "Score": "{:.0f}",
                "RSI": "{:.1f}",
                "Estoc. %K": "{:.1f}",
                "RVOL": "{:.2f}x",
                "Soporte": "${:,.2f}",
                "Resistencia": "${:,.2f}",
            })
        )

        st.dataframe(styled, use_container_width=True, height=460)

        csv_data = df_filtered[display_cols].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar CSV",
            csv_data,
            f"bcba_screening_{datetime.now(timezone(timedelta(hours=-3))).strftime('%Y%m%d_%H%M')}.csv",
            "text/csv",
        )

    # ══════════════════════════
    #  TAB 2 — ALERTAS
    # ══════════════════════════
    with tab_alertas:
        st.subheader("🔔 Papeles que cumplen los filtros de alerta")
        st.caption(
            f"Score ≥ {min_score} | RSI ≤ {max_rsi} | RVOL ≥ {min_rvol}x"
        )

        alertas_df = df_screen[
            (df_screen["Score"] >= min_score)
            & (df_screen["RSI"] <= max_rsi)
            & (df_screen["RVOL"] >= min_rvol)
        ].sort_values("Score", ascending=False)

        if alertas_df.empty:
            st.info("Ningún papel cumple los filtros actuales. Ajustá los umbrales en el sidebar.")
        else:
            for _, row in alertas_df.iterrows():
                css_class = "alert-box" if "COMPRA" in row["Señal"] else "alert-box warn"
                var_color = "#26a69a" if row["Var 1D%"] >= 0 else "#ef5350"
                st.markdown(
                    f"""<div class="{css_class}">
                    <strong>{row['Ticker']}</strong> &nbsp;·&nbsp; {row['Señal']} &nbsp;·&nbsp;
                    Score: <strong>{row['Score']}</strong> &nbsp;·&nbsp;
                    Precio: <strong>${row['Precio']:,.2f}</strong> &nbsp;
                    <span style="color:{var_color}">({row['Var 1D%']:+.2f}% hoy)</span>
                    &nbsp;·&nbsp; RSI: <strong>{row['RSI']:.1f}</strong> &nbsp;·&nbsp;
                    RVOL: <strong>{row['RVOL']:.2f}x</strong> &nbsp;·&nbsp;
                    Soporte: <strong>${row['Soporte']:,.2f}</strong> →
                    Resistencia: <strong>${row['Resistencia']:,.2f}</strong>
                    <br><small style="color:#aaa">{row['Detalle señales']}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ══════════════════════════
    #  TAB 3 — ANÁLISIS INDIVIDUAL
    # ══════════════════════════
    with tab_detalle:
        st.subheader("🔬 Análisis individual")

        col_sel1, col_sel2 = st.columns([2, 1])
        with col_sel1:
            ticker_list = df_screen["Ticker"].tolist()
            selected_ticker = st.selectbox("Seleccioná un ticker:", ticker_list)
        with col_sel2:
            chart_period = st.selectbox(
                "Período del gráfico",
                ["3mo", "6mo", "1y"],
                index=1,
                format_func=lambda x: {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año"}[x],
            )

        if selected_ticker:
            row = df_screen[df_screen["Ticker"] == selected_ticker].iloc[0]
            df_ticker = row["_df"]

            # Si el período del gráfico difiere del período de screening, re-fetch
            if chart_period != period_sel:
                ticker_ba = selected_ticker + ".BA"
                with st.spinner("Cargando período seleccionado…"):
                    raw_single = fetch_batch([ticker_ba], chart_period)
                    if raw_single is not None and not raw_single.empty:
                        df_ticker_chart = extract_ticker_df(raw_single, ticker_ba) or df_ticker
                    else:
                        df_ticker_chart = df_ticker
            else:
                df_ticker_chart = df_ticker

            # Métricas clave
            close_last = df_ticker["Close"].iloc[-1]
            sr = calc_support_resistance(df_ticker["High"], df_ticker["Low"], df_ticker["Close"])
            dist_sop = ((sr["soporte"] / close_last) - 1) * 100
            dist_res = ((sr["resistencia"] / close_last) - 1) * 100
            atr_val = calc_atr(df_ticker["High"], df_ticker["Low"], df_ticker["Close"]).iloc[-1]
            atr_pct = (atr_val / close_last) * 100

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Precio", f"${close_last:,.2f}", f"{row['Var 1D%']:+.2f}%")
            m2.metric("Score", f"{row['Score']}/100", row["Señal"].split(" ", 1)[1])
            m3.metric("RSI (14)", f"{row['RSI']:.1f}")
            m4.metric("Estoc. %K", f"{row['Estoc. %K']:.1f}")
            m5.metric("RVOL", f"{row['RVOL']:.2f}x")
            m6.metric("ATR%", f"{atr_pct:.1f}%", help="ATR como % del precio — volatilidad diaria esperada")

            st.markdown("---")

            # Soporte / Resistencia
            col_s, col_p, col_r = st.columns(3)
            with col_s:
                st.markdown(
                    f"""<div class="sr-card">
                    <div style="color:#aaa;font-size:12px">🛡️ SOPORTE (S1)</div>
                    <div style="font-size:1.4em;font-weight:700;color:#4CAF50">${sr['soporte']:,.2f}</div>
                    <div style="color:#ef5350;font-size:12px">{dist_sop:.1f}% del precio actual</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_p:
                st.markdown(
                    f"""<div class="sr-card">
                    <div style="color:#aaa;font-size:12px">⚖️ PIVOT</div>
                    <div style="font-size:1.4em;font-weight:700;color:#90CAF9">${sr['pivot']:,.2f}</div>
                    <div style="color:#aaa;font-size:12px">Nivel de equilibrio</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_r:
                st.markdown(
                    f"""<div class="sr-card">
                    <div style="color:#aaa;font-size:12px">🎯 RESISTENCIA (R1)</div>
                    <div style="font-size:1.4em;font-weight:700;color:#F44336">${sr['resistencia']:,.2f}</div>
                    <div style="color:#26a69a;font-size:12px">+{dist_res:.1f}% del precio actual</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Señales
            with st.expander("📌 Señales técnicas detectadas", expanded=True):
                signals_list = row["Detalle señales"].split(" | ")
                for s in signals_list:
                    if s.strip():
                        st.markdown(f"- {s}")

            # Gráfico
            st.markdown("#### Gráfico de precios")
            fig = build_chart(
                df_ticker_chart,
                selected_ticker,
                show_bb=show_bb,
                show_macd=show_macd,
                show_rsi=show_rsi,
                show_stoch=show_stoch,
                sr_data=sr if show_sr else None,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Variaciones
            st.markdown("#### Retornos históricos")
            close = df_ticker["Close"]
            periodos = {
                "1 día": 1, "5 días": 5, "10 días": 10,
                "20 días": 20, "3 meses": 63,
            }
            ret_data = {}
            for label, n in periodos.items():
                if len(close) > n:
                    ret_data[label] = round((close.iloc[-1] / close.iloc[-n] - 1) * 100, 2)

            df_ret = pd.DataFrame.from_dict(
                ret_data, orient="index", columns=["Variación %"]
            )
            df_ret["Color"] = df_ret["Variación %"].apply(
                lambda x: "🟢" if x > 0 else "🔴"
            )
            df_ret["Variación %"] = df_ret["Variación %"].apply(lambda x: f"{x:+.2f}%")
            st.dataframe(df_ret, use_container_width=False)


if __name__ == "__main__":
    main()

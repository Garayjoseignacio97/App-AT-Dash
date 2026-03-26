# ─────────────────────────────────────────────────────────────────────────────
# BCBA Technical Analyzer — Swing Trading Dashboard
# Autor: Nacho | Fuente de datos: Yahoo Finance (yfinance)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings("ignore")

# ─── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────────────────────

st.set_page_config(
    page_title="BCBA Analyzer | Swing Trading",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Fondo general */
.main { background-color: #0e1117; }
/* Cards de métricas */
[data-testid="metric-container"] {
    background: #1a1d27;
    border: 1px solid #2d3148;
    border-radius: 10px;
    padding: 12px;
}
/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #1a1d27;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}
/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1a1d27; }
::-webkit-scrollbar-thumb { background: #3d4163; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─── LISTA DE TICKERS BCBA ────────────────────────────────────────────────────
# Formato: "TICKER.BA" -> (Nombre, Sector, Panel)

TICKERS: dict[str, tuple[str, str, str]] = {
    # ── Panel Líder ──
    "ALUA.BA":  ("Aluar Aluminio",            "Materiales",       "Líder"),
    "BBAR.BA":  ("BBVA Argentina",            "Financiero",       "Líder"),
    "BMA.BA":   ("Banco Macro",               "Financiero",       "Líder"),
    "BYMA.BA":  ("BYMA",                      "Financiero",       "Líder"),
    "CEPU.BA":  ("Central Puerto",            "Energía",          "Líder"),
    "COME.BA":  ("Com. del Plata",            "Conglomerado",     "Líder"),
    "CRES.BA":  ("Cresud",                    "Agropecuario",     "Líder"),
    "CVH.BA":   ("Cablevision Holding",       "Comunicaciones",   "Líder"),
    "EDN.BA":   ("Edenor",                    "Servicios Púb.",   "Líder"),
    "GGAL.BA":  ("Grupo Financiero Galicia",  "Financiero",       "Líder"),
    "HARG.BA":  ("Holcim Argentina",          "Materiales",       "Líder"),
    "LOMA.BA":  ("Loma Negra",                "Materiales",       "Líder"),
    "METR.BA":  ("MetroGAS",                  "Energía",          "Líder"),
    "MIRG.BA":  ("Mirgor",                    "Tecnología",       "Líder"),
    "MOLI.BA":  ("Molinos Río de la Plata",   "Consumo",          "Líder"),
    "PAMP.BA":  ("Pampa Energía",             "Energía",          "Líder"),
    "SUPV.BA":  ("Supervielle",               "Financiero",       "Líder"),
    "TECO2.BA": ("Telecom Argentina",         "Comunicaciones",   "Líder"),
    "TGNO4.BA": ("Transp. Gas del Norte",     "Energía",          "Líder"),
    "TGSU2.BA": ("Transp. Gas del Sur",       "Energía",          "Líder"),
    "TRAN.BA":  ("Transener",                 "Servicios Púb.",   "Líder"),
    "TXAR.BA":  ("Ternium Argentina",         "Materiales",       "Líder"),
    "VALO.BA":  ("Grupo Supervielle",         "Financiero",       "Líder"),
    "YPFD.BA":  ("YPF",                       "Energía",          "Líder"),
    # ── Panel General ──
    "AGRO.BA":  ("AgroToken / Garovaglio",    "Agropecuario",     "General"),
    "AUSO.BA":  ("Autopistas del Sol",        "Infraestructura",  "General"),
    "BHIP.BA":  ("Banco Hipotecario",         "Financiero",       "General"),
    "BOLT.BA":  ("Boldt",                     "Tecnología",       "General"),
    "BPAT.BA":  ("Banco Patagonia",           "Financiero",       "General"),
    "CADO.BA":  ("Carlos Casado",             "Agropecuario",     "General"),
    "CAPX.BA":  ("Capex",                     "Energía",          "General"),
    "CARC.BA":  ("Carboclor",                 "Materiales",       "General"),
    "CGPA2.BA": ("Celulosa Argentina",        "Materiales",       "General"),
    "DYCA.BA":  ("Dycasa",                    "Construcción",     "General"),
    "FERR.BA":  ("Ferrum",                    "Materiales",       "General"),
    "FIPL.BA":  ("Fiplasto",                  "Materiales",       "General"),
    "GARO.BA":  ("Garovaglio y Zorraquín",    "Conglomerado",     "General"),
    "GBAN.BA":  ("Gas Natural BAN",           "Energía",          "General"),
    "GCDI.BA":  ("GCDI",                      "Construcción",     "General"),
    "GCLA.BA":  ("Grupo Clarín",              "Comunicaciones",   "General"),
    "GRIM.BA":  ("Grimoldi",                  "Consumo",          "General"),
    "HAVA.BA":  ("Havanna",                   "Consumo",          "General"),
    "INVJ.BA":  ("Inversora Juramento",       "Agropecuario",     "General"),
    "IRSA.BA":  ("IRSA Inversiones",          "Real Estate",      "General"),
    "LEDE.BA":  ("Ledesma",                   "Agropecuario",     "General"),
    "LONG.BA":  ("Longvie",                   "Consumo",          "General"),
    "MOLA.BA":  ("Molinos Agro",              "Agropecuario",     "General"),
    "MORI.BA":  ("Morixe Hermanos",           "Consumo",          "General"),
    "MTR.BA":   ("Matba Rofex",               "Financiero",       "General"),
    "PESA.BA":  ("Petróleo Sudamericano",     "Energía",          "General"),
    "REGE.BA":  ("Grupo Roggio",              "Infraestructura",  "General"),
    "RICH.BA":  ("Richmark",                  "Materiales",       "General"),
    "SAMI.BA":  ("S.A. San Miguel",           "Agropecuario",     "General"),
    "SEMI.BA":  ("Semillas Vicky",            "Agropecuario",     "General"),
    "TGLT.BA":  ("TGLT",                      "Real Estate",      "General"),
}

SECTORES = sorted(set(v[1] for v in TICKERS.values()))


# ─── INDICADORES TÉCNICOS ─────────────────────────────────────────────────────

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_f = series.ewm(span=fast, adjust=False).mean()
    ema_s = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_f - ema_s
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger(series: pd.Series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    pct_b = (series - lower) / (upper - lower).replace(0, np.nan)
    width = (upper - lower) / sma
    return upper, sma, lower, pct_b, width


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period=14, d_period=3):
    lowest = low.rolling(k_period).min()
    highest = high.rolling(k_period).max()
    k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def rvol(volume: pd.Series, period=20) -> pd.Series:
    avg = volume.rolling(period).mean()
    return volume / avg.replace(0, np.nan)


def support_resistance(close: pd.Series, high: pd.Series, low: pd.Series, window=10):
    """Detecta niveles de soporte/resistencia por máximos y mínimos pivote."""
    levels: list[tuple[str, float]] = []
    for i in range(window, len(close) - window):
        if float(high.iloc[i]) == float(high.iloc[i - window: i + window + 1].max()):
            levels.append(("R", float(high.iloc[i])))
        if float(low.iloc[i]) == float(low.iloc[i - window: i + window + 1].min()):
            levels.append(("S", float(low.iloc[i])))

    # Filtrar niveles muy cercanos (< 1.5% de distancia)
    filtered: list[tuple[str, float]] = []
    for t, p in sorted(levels, key=lambda x: x[1]):
        if not filtered or abs(p - filtered[-1][1]) / filtered[-1][1] > 0.015:
            filtered.append((t, p))

    current = float(close.iloc[-1])
    supports    = [p for t, p in filtered if p < current]
    resistances = [p for t, p in filtered if p > current]

    nearest_s = supports[-1]    if supports    else None
    nearest_r = resistances[0]  if resistances else None
    return nearest_s, nearest_r, filtered


# ─── SCORING SWING TRADING ───────────────────────────────────────────────────

def score_ticker(df: pd.DataFrame) -> tuple[int, list[str], str, dict]:
    """
    Evalúa señales técnicas orientadas a swing trading.
    Retorna: (score, señales, recomendación, métricas)
    """
    empty = (0, [], "Sin datos", {})
    if df is None or len(df) < 55:
        return empty

    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    # ── Calcular indicadores ──
    rsi_s             = rsi(close)
    macd_l, macd_sig, macd_h = macd(close)
    bb_u, bb_m, bb_l, pct_b_s, bb_w_s = bollinger(close)
    atr_s             = atr(high, low, close)
    k_s, d_s          = stochastic(high, low, close)
    rvol_s            = rvol(volume)
    sma20_s           = close.rolling(20).mean()
    sma50_s           = close.rolling(50).mean()
    nearest_s, nearest_r, _ = support_resistance(close, high, low)

    # ── Últimos valores ──
    rsi_v    = float(rsi_s.iloc[-1])
    macd_v   = float(macd_l.iloc[-1])
    msig_v   = float(macd_sig.iloc[-1])
    mh_v     = float(macd_h.iloc[-1])
    mh_prev  = float(macd_h.iloc[-2])
    pct_b_v  = float(pct_b_s.iloc[-1])
    bb_w_v   = float(bb_w_s.iloc[-1])
    k_v      = float(k_s.iloc[-1])
    d_v      = float(d_s.iloc[-1])
    k_prev   = float(k_s.iloc[-2])
    d_prev   = float(d_s.iloc[-2])
    rvol_v   = float(rvol_s.iloc[-1])
    price    = float(close.iloc[-1])
    sma20_v  = float(sma20_s.iloc[-1])
    sma50_v  = float(sma50_s.iloc[-1])
    atr_v    = float(atr_s.iloc[-1])

    score   = 0
    signals = []

    # 1. MACD — cruce y momentum
    macd_prev   = float(macd_l.iloc[-2])
    msig_prev   = float(macd_sig.iloc[-2])
    if macd_v > msig_v and macd_prev <= msig_prev:
        score += 2; signals.append("✅ MACD: cruce alcista (señal fuerte)")
    elif macd_v < msig_v and macd_prev >= msig_prev:
        score -= 2; signals.append("🔴 MACD: cruce bajista (señal fuerte)")
    elif macd_v > msig_v:
        score += 1; signals.append("📈 MACD por encima de señal")
    else:
        score -= 1; signals.append("📉 MACD por debajo de señal")

    if mh_v > 0 and mh_v > mh_prev:
        score += 1; signals.append("✅ Histograma MACD en expansión alcista")
    elif mh_v < 0 and mh_v < mh_prev:
        score -= 1; signals.append("🔴 Histograma MACD en expansión bajista")

    # 2. RSI
    if 45 <= rsi_v <= 65:
        score += 1; signals.append(f"✅ RSI en zona saludable ({rsi_v:.0f})")
    elif rsi_v > 70:
        score -= 1; signals.append(f"⚠️ RSI sobrecomprado ({rsi_v:.0f})")
    elif rsi_v < 30:
        score += 1; signals.append(f"⚠️ RSI sobrevendido ({rsi_v:.0f}) — posible rebote")
    elif 30 <= rsi_v < 45:
        signals.append(f"👁️ RSI en zona de carga ({rsi_v:.0f})")

    # 3. Bollinger Bands
    if pct_b_v > 1.0:
        score -= 1; signals.append("⚠️ Precio sobre banda superior BB")
    elif pct_b_v < 0.0:
        score += 1; signals.append("✅ Precio en/bajo banda inferior BB")
    elif 0.45 <= pct_b_v <= 0.55:
        score += 1; signals.append("✅ Precio en zona media BB (momentum)")

    # Compresión de bandas (squeeze → posible ruptura)
    if bb_w_v < 0.05:
        score += 1; signals.append("✅ BB squeeze detectado — posible ruptura inminente")

    # 4. Estocástico — cruce
    if k_v > d_v and k_prev <= d_prev and k_v < 80:
        score += 2; signals.append(f"✅ Estocástico: cruce alcista ({k_v:.0f})")
    elif k_v < d_v and k_prev >= d_prev and k_v > 20:
        score -= 2; signals.append(f"🔴 Estocástico: cruce bajista ({k_v:.0f})")
    elif k_v > 80:
        signals.append(f"⚠️ Estocástico sobrecomprado ({k_v:.0f})")
    elif k_v < 20:
        signals.append(f"⚠️ Estocástico sobrevendido ({k_v:.0f}) — posible rebote")

    # 5. Volumen relativo
    if rvol_v > 2.5:
        score += 2; signals.append(f"✅ RVOL muy alto ({rvol_v:.1f}x) — posible ruptura")
    elif rvol_v > 1.5:
        score += 1; signals.append(f"✅ RVOL elevado ({rvol_v:.1f}x) — interés creciente")
    elif rvol_v < 0.5:
        score -= 1; signals.append(f"⚠️ RVOL bajo ({rvol_v:.1f}x) — sin convicción")

    # 6. Tendencia (SMAs)
    if price > sma20_v > sma50_v:
        score += 1; signals.append("✅ Tendencia alcista confirmada (P > SMA20 > SMA50)")
    elif price < sma20_v < sma50_v:
        score -= 1; signals.append("🔴 Tendencia bajista confirmada (P < SMA20 < SMA50)")
    elif price > sma20_v and sma20_v < sma50_v:
        signals.append("👁️ Precio sobre SMA20 pero SMA20 aún bajo SMA50 — recuperación")

    # 7. Soporte / Resistencia
    if nearest_s and abs(price - nearest_s) / price < 0.025:
        score += 1; signals.append(f"✅ Precio próximo a soporte (${nearest_s:,.1f})")
    if nearest_r and abs(price - nearest_r) / price < 0.025:
        score -= 1; signals.append(f"⚠️ Precio próximo a resistencia (${nearest_r:,.1f})")

    # ── Recomendación ──
    if score >= 6:    rec = "COMPRA FUERTE"
    elif score >= 3:  rec = "COMPRA"
    elif score >= -2: rec = "NEUTRAL"
    elif score >= -5: rec = "VENTA"
    else:             rec = "VENTA FUERTE"

    # ── Niveles de gestión de posición (2 ATR) ──
    metrics = {
        "rsi":        round(rsi_v, 1),
        "macd":       round(macd_v, 4),
        "macd_sig":   round(msig_v, 4),
        "pct_b":      round(pct_b_v, 2),
        "bb_width":   round(bb_w_v, 4),
        "stoch_k":    round(k_v, 1),
        "stoch_d":    round(d_v, 1),
        "rvol":       round(rvol_v, 2),
        "atr":        round(atr_v, 2),
        "sma20":      round(sma20_v, 2),
        "sma50":      round(sma50_v, 2),
        "stop_loss":  round(price - 2 * atr_v, 2),
        "target_1":   round(price + 2 * atr_v, 2),
        "target_2":   round(price + 4 * atr_v, 2),
        "support":    round(nearest_s, 2) if nearest_s else None,
        "resistance": round(nearest_r, 2) if nearest_r else None,
    }

    return score, signals, rec, metrics


# ─── DESCARGA DE DATOS ────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_batch(tickers_tuple: tuple, period: str) -> dict[str, pd.DataFrame]:
    """
    Descarga histórica en batch con yf.download().
    Retorna dict {ticker: DataFrame OHLCV}.
    """
    tickers_list = list(tickers_tuple)
    result: dict[str, pd.DataFrame] = {}

    try:
        raw = yf.download(
            tickers_list,
            period=period,
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as e:
        st.warning(f"Error en descarga batch: {e}")
        return result

    for ticker in tickers_list:
        try:
            if len(tickers_list) == 1:
                df = raw.copy()
            else:
                df = raw[ticker].copy()
            df = df.dropna(how="all")
            if len(df) >= 55:
                result[ticker] = df
        except Exception:
            continue

    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_intraday_prices(tickers_tuple: tuple) -> dict[str, float | None]:
    """Precios intradiarios vía fast_info (cache 30 min)."""
    prices: dict[str, float | None] = {}

    def _fetch(ticker: str):
        try:
            prices[ticker] = yf.Ticker(ticker).fast_info.last_price
        except Exception:
            prices[ticker] = None

    with ThreadPoolExecutor(max_workers=12) as pool:
        pool.map(_fetch, list(tickers_tuple))

    return prices


# ─── HELPERS UI ──────────────────────────────────────────────────────────────

REC_COLORS = {
    "COMPRA FUERTE": ("#00d4aa", "#0d2b24"),
    "COMPRA":        ("#4ade80", "#0f2318"),
    "NEUTRAL":       ("#fbbf24", "#2b2410"),
    "VENTA":         ("#f87171", "#2b1010"),
    "VENTA FUERTE":  ("#ff4b6b", "#330a14"),
}

def badge(rec: str) -> str:
    color, bg = REC_COLORS.get(rec, ("#aaa", "#222"))
    return f'<span style="background:{bg};color:{color};border:1px solid {color};border-radius:6px;padding:2px 8px;font-size:0.78em;font-weight:700">{rec}</span>'

def score_color(s: int) -> str:
    if s >= 6:  return "#00d4aa"
    if s >= 3:  return "#4ade80"
    if s >= -2: return "#fbbf24"
    if s >= -5: return "#f87171"
    return "#ff4b6b"


def build_chart(df: pd.DataFrame, ticker: str, metrics: dict) -> go.Figure:
    """Genera figura Plotly con velas, BB, SMAs, MACD, RSI, Estocástico y Volumen."""
    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]

    # Indicadores
    bb_u, bb_m, bb_l, _, _ = bollinger(close)
    macd_l, macd_sig, macd_h = macd(close)
    rsi_s         = rsi(close)
    k_s, d_s      = stochastic(high, low, close)
    sma20_s       = close.rolling(20).mean()
    sma50_s       = close.rolling(50).mean()
    _, _, sr_levels = support_resistance(close, high, low)

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.50, 0.18, 0.17, 0.15],
        subplot_titles=[
            f"{ticker} — Precio + Bollinger + SMAs",
            "MACD (12/26/9)",
            "RSI (14)  |  Estocástico (14/3)",
            "Volumen  |  RVOL"
        ]
    )

    # ── 1. Velas ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=high, low=low, close=close,
        name="Precio",
        increasing_line_color="#00d4aa", increasing_fillcolor="#00d4aa",
        decreasing_line_color="#ff4b6b", decreasing_fillcolor="#ff4b6b",
        line=dict(width=1),
    ), row=1, col=1)

    # Bollinger
    fig.add_trace(go.Scatter(x=df.index, y=bb_u, name="BB Sup", line=dict(color="#818cf8", width=1, dash="dash"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_m, name="BB Med / SMA20", line=dict(color="#818cf8", width=1), fill=None, showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_l, name="BB Inf", line=dict(color="#818cf8", width=1, dash="dash"),
                             fill="tonexty", fillcolor="rgba(129,140,248,0.06)", showlegend=False), row=1, col=1)
    # SMA50
    fig.add_trace(go.Scatter(x=df.index, y=sma50_s, name="SMA50", line=dict(color="#f59e0b", width=1.5), showlegend=False), row=1, col=1)

    # S/R horizontales
    for lvl_type, price_lvl in sr_levels[-12:]:
        c = "rgba(74,222,128,0.35)" if lvl_type == "S" else "rgba(248,113,113,0.35)"
        fig.add_hline(y=price_lvl, line_dash="dot", line_color=c, line_width=1, row=1, col=1)

    # ── 2. MACD ──
    bar_colors = ["#00d4aa" if v >= 0 else "#ff4b6b" for v in macd_h]
    fig.add_trace(go.Bar(x=df.index, y=macd_h, name="Histograma",
                         marker_color=bar_colors, opacity=0.7, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_l, line=dict(color="#00d4aa", width=1.5), showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_sig, line=dict(color="#f59e0b", width=1.5), showlegend=False), row=2, col=1)
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_width=1, row=2, col=1)

    # ── 3. RSI + Estocástico ──
    fig.add_trace(go.Scatter(x=df.index, y=rsi_s, line=dict(color="#a78bfa", width=1.8), name="RSI", showlegend=False), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,75,107,0.5)", line_width=1, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,212,170,0.5)", line_width=1, row=3, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,75,107,0.04)", line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(0,212,170,0.04)", line_width=0, row=3, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=k_s, line=dict(color="#fb923c", width=1.2), showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=d_s, line=dict(color="#facc15", width=1.2, dash="dot"), showlegend=False), row=3, col=1)

    # ── 4. Volumen ──
    vol_colors = ["#00d4aa" if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i]) else "#ff4b6b"
                  for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=volume, marker_color=vol_colors, opacity=0.7, showlegend=False), row=4, col=1)
    # Volumen promedio (20p)
    vol_avg = volume.rolling(20).mean()
    fig.add_trace(go.Scatter(x=df.index, y=vol_avg, line=dict(color="#f59e0b", width=1.2, dash="dash"), showlegend=False), row=4, col=1)

    # ── Layout ──
    fig.update_layout(
        template="plotly_dark",
        height=820,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=28, b=0),
        hovermode="x unified",
    )
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.04)",
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    # Fijar rango RSI/Estocástico
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    return fig


# ─── APP PRINCIPAL ────────────────────────────────────────────────────────────

def main():
    # ══ SIDEBAR ══════════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown("## 🇦🇷 BCBA Analyzer")
        st.caption("Swing Trading Dashboard")
        st.divider()

        panel_sel = st.multiselect(
            "Panel", ["Líder", "General"],
            default=["Líder", "General"]
        )
        sector_sel = st.multiselect("Sector (todos si vacío)", SECTORES, default=[])

        period_map = {"3mo": "3 meses", "6mo": "6 meses", "1y": "1 año", "2y": "2 años"}
        period = st.selectbox("Período histórico", list(period_map.keys()), index=1,
                              format_func=lambda x: period_map[x])

        score_min = st.slider("Score mínimo a mostrar", -10, 10, value=-2, step=1)

        st.divider()
        if st.button("🔄 Limpiar caché y actualizar", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.caption(f"⏱ Cache: 5 min | {datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m %H:%M')}")

    # ══ FILTRADO DE TICKERS ════════════════════════════════════════════════

    filtered = {
        k: v for k, v in TICKERS.items()
        if v[2] in panel_sel and (not sector_sel or v[1] in sector_sel)
    }
    tickers_list = list(filtered.keys())

    if not tickers_list:
        st.warning("Sin tickers para los filtros seleccionados.")
        return

    # ══ DESCARGA DE DATOS ══════════════════════════════════════════════════

    with st.spinner("⏳ Descargando datos históricos de mercado..."):
        data = fetch_batch(tuple(tickers_list), period)

    if not data:
        st.error("❌ No se pudo obtener datos. Verificá la conexión o intentá de nuevo.")
        return

    # ══ CÁLCULO DE SCORES ══════════════════════════════════════════════════

    rows = []
    detail_store: dict[str, dict] = {}  # ticker -> {df, metrics, signals}

    for ticker in tickers_list:
        df = data.get(ticker)
        if df is None:
            continue

        try:
            score, signals, rec, metrics = score_ticker(df)
        except Exception:
            continue

        if score < score_min:
            continue

        nombre, sector, panel = filtered[ticker]
        price   = float(df["Close"].iloc[-1])
        price_p = float(df["Close"].iloc[-2]) if len(df) > 1 else price
        var     = (price / price_p - 1) * 100 if price_p else 0.0

        sym = ticker.replace(".BA", "")
        rows.append({
            "Ticker":        sym,
            "Nombre":        nombre,
            "Panel":         panel,
            "Sector":        sector,
            "Precio $":      round(price, 2),
            "Var %":         round(var, 2),
            "Score":         score,
            "Señal":         rec,
            "RSI":           metrics["rsi"],
            "Stoch %K":      metrics["stoch_k"],
            "RVOL":          metrics["rvol"],
            "ATR":           metrics["atr"],
            "Stop Loss":     metrics["stop_loss"],
            "Target 1":      metrics["target_1"],
            "Target 2":      metrics["target_2"],
            "N° Señales":    len(signals),
        })
        detail_store[sym] = {"df": df, "metrics": metrics, "signals": signals, "score": score, "rec": rec}

    if not rows:
        st.info("Sin resultados con los filtros actuales. Bajá el score mínimo o ampliá el panel/sector.")
        return

    results_df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)

    # ══ TABS ═══════════════════════════════════════════════════════════════

    tab1, tab2, tab3 = st.tabs(["📊 Ranking & Screener", "📈 Análisis Individual", "🔔 Alertas"])

    # ─────────────────────────────────────────────────────────────────────
    # TAB 1 — RANKING
    # ─────────────────────────────────────────────────────────────────────
    with tab1:
        compra_fuerte = len(results_df[results_df["Score"] >= 6])
        compra        = len(results_df[(results_df["Score"] >= 3) & (results_df["Score"] < 6)])
        neutral       = len(results_df[(results_df["Score"] > -3) & (results_df["Score"] < 3)])
        venta         = len(results_df[results_df["Score"] <= -3])
        total         = len(results_df)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📋 Total analizado",   total)
        c2.metric("🟢 Compra fuerte",     compra_fuerte)
        c3.metric("🟩 Compra",            compra)
        c4.metric("🟡 Neutral",           neutral)
        c5.metric("🔴 Venta / VF",        venta)

        st.divider()

        # ── Tabla con colores ──
        display_cols = ["Ticker","Nombre","Panel","Sector","Precio $","Var %","Score","Señal","RSI","RVOL","N° Señales"]

        def _color_señal(val):
            c, bg = REC_COLORS.get(val, ("#aaa","#222"))
            return f"background-color:{bg};color:{c};font-weight:700"

        def _color_score(val):
            return f"color:{score_color(val)};font-weight:700"

        def _color_var(val):
            return "color:#4ade80" if val >= 0 else "color:#f87171"

        styled = (
            results_df[display_cols]
            .style
            .map(_color_señal, subset=["Señal"])
            .map(_color_score, subset=["Score"])
            .map(_color_var,   subset=["Var %"])
            .format({
                "Precio $": "${:,.2f}",
                "Var %":    "{:+.2f}%",
                "Score":    "{:+d}",
                "RSI":      "{:.1f}",
                "RVOL":     "{:.2f}x",
            })
        )

        st.dataframe(styled, use_container_width=True, height=520)

        # ── Export CSV ──
        csv_bytes = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Exportar ranking completo (CSV)",
            csv_bytes, "bcba_ranking.csv", "text/csv",
            use_container_width=True
        )

    # ─────────────────────────────────────────────────────────────────────
    # TAB 2 — ANÁLISIS INDIVIDUAL
    # ─────────────────────────────────────────────────────────────────────
    with tab2:
        ticker_opts = list(detail_store.keys())
        selected = st.selectbox(
            "Seleccioná un ticker para análisis completo",
            ticker_opts,
            format_func=lambda x: f"{x}  —  {TICKERS.get(x+'.BA', ('?','?','?'))[0]}"
        )

        if not selected or selected not in detail_store:
            st.info("Seleccioná un ticker del menú.")
        else:
            d = detail_store[selected]
            df       = d["df"]
            metrics  = d["metrics"]
            signals  = d["signals"]
            score    = d["score"]
            rec      = d["rec"]
            price    = float(df["Close"].iloc[-1])
            price_p  = float(df["Close"].iloc[-2])
            var      = (price / price_p - 1) * 100

            # ── Encabezado ──
            nombre, sector, panel = TICKERS.get(selected + ".BA", ("?", "?", "?"))
            st.markdown(
                f"### {selected} &nbsp; <small style='color:#94a3b8'>{nombre} · {sector} · Panel {panel}</small>",
                unsafe_allow_html=True
            )

            m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
            m1.metric("Precio",    f"${price:,.2f}",          f"{var:+.2f}%")
            m2.metric("Score",     f"{score:+d}",              rec)
            m3.metric("RSI",       f"{metrics['rsi']:.1f}")
            m4.metric("Stoch %K",  f"{metrics['stoch_k']:.0f}")
            m5.metric("RVOL",      f"{metrics['rvol']:.2f}x")
            m6.metric("Stop Loss", f"${metrics['stop_loss']:,.2f}")
            m7.metric("Target 1",  f"${metrics['target_1']:,.2f}")

            st.divider()

            # ── Señales activas ──
            with st.expander("🔍 Señales activas en este ticker", expanded=True):
                if signals:
                    cols = st.columns(2)
                    for i, sig in enumerate(signals):
                        cols[i % 2].markdown(f"- {sig}")
                else:
                    st.info("Sin señales detectadas.")

            # ── Gráfico ──
            fig = build_chart(df, selected, metrics)
            st.plotly_chart(fig, use_container_width=True)

            # ── Tabla de gestión de posición ──
            st.subheader("📐 Gestión de posición (ATR × 2)")
            rr = pd.DataFrame([
                {
                    "Nivel":      "🛑 Stop Loss",
                    "Precio $":   metrics["stop_loss"],
                    "Distancia":  f"-{abs(price - metrics['stop_loss']) / price * 100:.1f}%",
                    "R/R":        "—"
                },
                {
                    "Nivel":      "🟡 Entrada (precio actual)",
                    "Precio $":   round(price, 2),
                    "Distancia":  "—",
                    "R/R":        "—"
                },
                {
                    "Nivel":      "🎯 Target 1 (+2 ATR)",
                    "Precio $":   metrics["target_1"],
                    "Distancia":  f"+{abs(metrics['target_1'] - price) / price * 100:.1f}%",
                    "R/R":        "1:1"
                },
                {
                    "Nivel":      "🚀 Target 2 (+4 ATR)",
                    "Precio $":   metrics["target_2"],
                    "Distancia":  f"+{abs(metrics['target_2'] - price) / price * 100:.1f}%",
                    "R/R":        "1:2"
                },
            ])
            st.table(rr.set_index("Nivel"))

            # ── S/R detectados ──
            if metrics.get("support") or metrics.get("resistance"):
                col_s, col_r = st.columns(2)
                if metrics.get("support"):
                    col_s.metric("🟢 Soporte más cercano", f"${metrics['support']:,.2f}",
                                 f"-{abs(price - metrics['support']) / price * 100:.1f}%")
                if metrics.get("resistance"):
                    col_r.metric("🔴 Resistencia más cercana", f"${metrics['resistance']:,.2f}",
                                 f"+{abs(metrics['resistance'] - price) / price * 100:.1f}%")

    # ─────────────────────────────────────────────────────────────────────
    # TAB 3 — ALERTAS (en pantalla)
    # ─────────────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("🔔 Alertas de señales técnicas activas")

        alert_rows = []
        for sym, d in detail_store.items():
            nombre, sector, panel = TICKERS.get(sym + ".BA", ("?", "?", "?"))
            df_t  = d["df"]
            price = float(df_t["Close"].iloc[-1])
            for sig in d["signals"]:
                if "✅" in sig:
                    tipo = "BULLISH"
                elif "🔴" in sig:
                    tipo = "BEARISH"
                else:
                    tipo = "WATCH"
                alert_rows.append({
                    "Ticker":  sym,
                    "Panel":   panel,
                    "Sector":  sector,
                    "Precio $": round(price, 2),
                    "Score":   d["score"],
                    "Tipo":    tipo,
                    "Señal":   sig,
                })

        if not alert_rows:
            st.info("Sin alertas para los tickers del filtro actual.")
        else:
            alerts_df = pd.DataFrame(alert_rows)

            a1, a2, a3 = st.columns(3)
            a1.metric("🟢 BULLISH", len(alerts_df[alerts_df["Tipo"] == "BULLISH"]))
            a2.metric("🔴 BEARISH", len(alerts_df[alerts_df["Tipo"] == "BEARISH"]))
            a3.metric("👁️ WATCH",   len(alerts_df[alerts_df["Tipo"] == "WATCH"]))

            st.divider()

            tipo_filter = st.radio("Mostrar", ["Todas", "BULLISH", "BEARISH", "WATCH"], horizontal=True)
            if tipo_filter != "Todas":
                alerts_df = alerts_df[alerts_df["Tipo"] == tipo_filter]

            def _color_tipo(val):
                m = {"BULLISH": "background-color:#0f2318;color:#4ade80;font-weight:700",
                     "BEARISH": "background-color:#2b1010;color:#f87171;font-weight:700",
                     "WATCH":   "background-color:#2b2410;color:#fbbf24;font-weight:700"}
                return m.get(val, "")

            st.dataframe(
                alerts_df.style
                    .map(_color_tipo, subset=["Tipo"])
                    .map(_color_score, subset=["Score"])
                    .format({"Precio $": "${:,.2f}", "Score": "{:+d}"}),
                use_container_width=True,
                height=480,
            )

            # ── Top oportunidades bullish ──
            st.subheader("🏆 Top oportunidades bullish (score + señales)")
            top = (
                alerts_df[alerts_df["Tipo"] == "BULLISH"]
                .groupby("Ticker")
                .agg(N_señales=("Señal", "count"), Score=("Score", "first"), Precio=("Precio $", "first"))
                .sort_values(["Score", "N_señales"], ascending=False)
                .head(10)
            )
            if not top.empty:
                st.dataframe(top, use_container_width=True)
            else:
                st.info("Sin señales bullish en el filtro actual.")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()

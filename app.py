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
import os
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
        vertical_spacing=0.04,
        row_heights=[0.48, 0.19, 0.19, 0.14],
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
        height=960,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=10, t=45, b=10),
        hovermode="x unified",
    )
    # Tamaño de los títulos de subpaneles
    for ann in fig.layout.annotations:
        ann.font = dict(size=11, color="#94a3b8")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.04)",
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    # Fijar rango RSI/Estocástico
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    return fig


# ─── BACKTESTER ───────────────────────────────────────────────────────────────

def compute_score_series(df: pd.DataFrame) -> pd.Series:
    """Calcula el score técnico para cada fecha del DataFrame (rolling)."""
    close, high, low, volume = df["Close"], df["High"], df["Low"], df["Volume"]
    rsi_s              = rsi(close)
    macd_l, macd_sig, macd_h = macd(close)
    _, _, _, pct_b_s, bb_w_s = bollinger(close)
    k_s, d_s           = stochastic(high, low, close)
    rvol_s             = rvol(volume)
    sma20_s            = close.rolling(20).mean()
    sma50_s            = close.rolling(50).mean()

    scores = pd.Series(np.nan, index=df.index, dtype=float)
    for i in range(55, len(df)):
        s = 0
        mv,  sv  = float(macd_l.iloc[i]),   float(macd_sig.iloc[i])
        mvp, svp = float(macd_l.iloc[i-1]), float(macd_sig.iloc[i-1])
        mhv, mhp = float(macd_h.iloc[i]),   float(macd_h.iloc[i-1])

        if mv > sv and mvp <= svp:   s += 2
        elif mv < sv and mvp >= svp: s -= 2
        elif mv > sv:                s += 1
        else:                        s -= 1
        if mhv > 0 and mhv > mhp:   s += 1
        elif mhv < 0 and mhv < mhp: s -= 1

        rv = float(rsi_s.iloc[i])
        if 45 <= rv <= 65:   s += 1
        elif rv > 70:        s -= 1
        elif rv < 30:        s += 1

        pb = float(pct_b_s.iloc[i])
        bw = float(bb_w_s.iloc[i])
        if pb > 1.0:                 s -= 1
        elif pb < 0.0:               s += 1
        elif 0.45 <= pb <= 0.55:     s += 1
        if not np.isnan(bw) and bw < 0.05: s += 1

        kv, dv = float(k_s.iloc[i]), float(d_s.iloc[i])
        kp, dp = float(k_s.iloc[i-1]), float(d_s.iloc[i-1])
        if kv > dv and kp <= dp and kv < 80:  s += 2
        elif kv < dv and kp >= dp and kv > 20: s -= 2

        rv2 = float(rvol_s.iloc[i])
        if rv2 > 2.5:   s += 2
        elif rv2 > 1.5: s += 1
        elif rv2 < 0.5: s -= 1

        p, s20, s50 = float(close.iloc[i]), float(sma20_s.iloc[i]), float(sma50_s.iloc[i])
        if p > s20 > s50:   s += 1
        elif p < s20 < s50: s -= 1

        scores.iloc[i] = s
    return scores


def run_backtest(
    df: pd.DataFrame,
    score_s: pd.Series,
    entry_threshold: int = 3,
    hold_days: int = 10,
    stop_pct: float = 0.05,
    target_pct: float = 0.10,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Backtester de una sola acción.
    Retorna: (trades_df, equity_series, bh_series)
    """
    trades   = []
    in_trade = False
    entry_price = entry_date = entry_score = None
    days_held   = 0
    capital     = 100.0
    equity_vals = [100.0]
    equity_idx  = [df.index[0]]

    for i in range(1, len(df)):
        date  = df.index[i]
        price = float(df["Close"].iloc[i])
        sc    = score_s.iloc[i] if not np.isnan(score_s.iloc[i]) else 0

        if in_trade:
            days_held += 1
            ret = price / entry_price - 1
            reason = None
            if ret <= -stop_pct:              reason = "🛑 Stop Loss"
            elif ret >= target_pct:           reason = "🎯 Target"
            elif days_held >= hold_days:      reason = "⏱ Tiempo"

            if reason:
                trades.append({
                    "Ticker":         "—",
                    "Entrada":        entry_date.strftime("%d/%m/%y"),
                    "Salida":         date.strftime("%d/%m/%y"),
                    "Días":           days_held,
                    "Precio entrada": round(entry_price, 2),
                    "Precio salida":  round(price, 2),
                    "Retorno %":      round(ret * 100, 2),
                    "Score entrada":  entry_score,
                    "Motivo salida":  reason,
                    "_ret":           ret,
                })
                capital  *= (1 + ret)
                in_trade  = False
        else:
            if sc >= entry_threshold and not np.isnan(sc):
                in_trade    = True
                entry_price = price
                entry_date  = date
                entry_score = sc
                days_held   = 0

        equity_vals.append(capital)
        equity_idx.append(date)

    equity_s = pd.Series(equity_vals, index=equity_idx)
    # Buy & hold
    bh_start = float(df["Close"].iloc[0])
    bh_s     = df["Close"] / bh_start * 100

    return pd.DataFrame(trades), equity_s, bh_s


def backtest_metrics(trades_df: pd.DataFrame, equity_s: pd.Series, bh_s: pd.Series) -> dict:
    """Calcula métricas agregadas del backtest."""
    total_ret  = round(equity_s.iloc[-1] - 100, 2)
    bh_ret     = round(float(bh_s.iloc[-1]) - 100, 2)
    n_trades   = len(trades_df)

    if n_trades == 0:
        return {
            "Total Return %": total_ret, "B&H Return %": bh_ret,
            "N° Operaciones": 0, "Win Rate %": 0, "Profit Factor": 0,
            "Sharpe": 0, "Max Drawdown %": 0, "Avg días": 0,
        }

    wins      = trades_df[trades_df["_ret"] > 0]
    losses    = trades_df[trades_df["_ret"] <= 0]
    win_rate  = round(len(wins) / n_trades * 100, 1)
    gross_win = wins["_ret"].sum() if len(wins) else 0
    gross_los = abs(losses["_ret"].sum()) if len(losses) else 1e-9
    pf        = round(gross_win / gross_los, 2) if gross_los else 0

    # Drawdown
    roll_max  = equity_s.cummax()
    dd        = (equity_s - roll_max) / roll_max * 100
    max_dd    = round(dd.min(), 2)

    # Sharpe (daily returns de la equity curve, anualizado)
    daily_ret = equity_s.pct_change().dropna()
    sharpe    = round((daily_ret.mean() / daily_ret.std() * np.sqrt(252))
                      if daily_ret.std() > 0 else 0, 2)

    avg_dias  = round(trades_df["Días"].mean(), 1)

    return {
        "Total Return %": total_ret,
        "B&H Return %":   bh_ret,
        "N° Operaciones": n_trades,
        "Win Rate %":     win_rate,
        "Profit Factor":  pf,
        "Sharpe":         sharpe,
        "Max Drawdown %": max_dd,
        "Avg días":       avg_dias,
    }


def build_equity_chart(equity_s: pd.Series, bh_s: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_s.index, y=equity_s.values,
        name="Estrategia", line=dict(color="#00d4aa", width=2),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.06)",
    ))
    fig.add_trace(go.Scatter(
        x=bh_s.index, y=bh_s.values,
        name="Buy & Hold", line=dict(color="#f59e0b", width=1.5, dash="dash"),
    ))
    fig.add_hline(y=100, line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.update_layout(
        template="plotly_dark",
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08),
        title=dict(text=f"Equity Curve — {ticker}", font=dict(size=12, color="#94a3b8")),
        yaxis=dict(ticksuffix="%", gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    return fig


def build_score_chart(score_s: pd.Series, df: pd.DataFrame,
                      entry_threshold: int, trades_df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.55, 0.45], vertical_spacing=0.04,
                        subplot_titles=["Precio + Operaciones", "Score técnico"])

    close = df["Close"]
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=close, close=close,
        name="Precio",
        increasing_line_color="#00d4aa", increasing_fillcolor="#00d4aa",
        decreasing_line_color="#ff4b6b", decreasing_fillcolor="#ff4b6b",
        line=dict(width=1),
    ), row=1, col=1)

    # Markers de entrada y salida
    if not trades_df.empty:
        entry_dates = pd.to_datetime(trades_df["Entrada"], format="%d/%m/%y", errors="coerce")
        exit_dates  = pd.to_datetime(trades_df["Salida"],  format="%d/%m/%y", errors="coerce")
        entry_prices = trades_df["Precio entrada"].values
        exit_prices  = trades_df["Precio salida"].values
        rets         = trades_df["_ret"].values

        fig.add_trace(go.Scatter(
            x=entry_dates, y=entry_prices, mode="markers",
            marker=dict(symbol="triangle-up", size=10, color="#00d4aa", line=dict(width=1, color="#fff")),
            name="Entrada", hovertemplate="Entrada: $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)

        exit_colors = ["#4ade80" if r > 0 else "#f87171" for r in rets]
        fig.add_trace(go.Scatter(
            x=exit_dates, y=exit_prices, mode="markers",
            marker=dict(symbol="triangle-down", size=10, color=exit_colors,
                        line=dict(width=1, color="#fff")),
            name="Salida", hovertemplate="Salida: $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    # Score series
    score_clean = score_s.dropna()
    score_colors = ["#00d4aa" if v >= entry_threshold else
                    "#fbbf24" if v >= 0 else "#f87171"
                    for v in score_clean.values]
    fig.add_trace(go.Bar(
        x=score_clean.index, y=score_clean.values,
        marker_color=score_colors, opacity=0.75,
        name="Score", showlegend=False,
    ), row=2, col=1)
    fig.add_hline(y=entry_threshold, line_dash="dash", line_color="#00d4aa",
                  opacity=0.7, annotation_text=f"Umbral entrada ({entry_threshold})",
                  annotation_font_size=10, row=2, col=1)
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_width=1, row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=36, b=0),
        hovermode="x unified",
    )
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)",
                     rangebreaks=[dict(bounds=["sat", "mon"])])
    for ann in fig.layout.annotations:
        ann.font = dict(size=11, color="#94a3b8")
    return fig



# ─── ANÁLISIS FUNDAMENTAL ─────────────────────────────────────────────────────

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_fundamentals(tickers_tuple: tuple) -> dict[str, dict]:
    """
    Descarga métricas fundamentales desde yfinance.info.
    Cache de 24 horas (los fundamentales no cambian intradía).
    """
    result = {}
    def _fetch(ticker: str):
        try:
            info = yf.Ticker(ticker).info
            result[ticker] = {
                # Valuación
                "pe":          info.get("trailingPE"),
                "pb":          info.get("priceToBook"),
                "ev_ebitda":   info.get("enterpriseToEbitda"),
                # Rentabilidad
                "roe":         info.get("returnOnEquity"),
                "roa":         info.get("returnOnAssets"),
                "margen_neto": info.get("profitMargins"),
                # Deuda
                "debt_eq":     info.get("debtToEquity"),
                "current":     info.get("currentRatio"),
                # Dividendos
                "div_yield":   info.get("dividendYield"),
                "payout":      info.get("payoutRatio"),
                # Extra
                "market_cap":  info.get("marketCap"),
                "sector":      info.get("sector"),
                "employees":   info.get("fullTimeEmployees"),
            }
        except Exception:
            result[ticker] = {}

    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(_fetch, list(tickers_tuple))
    return result


def score_fundamentals(f: dict) -> tuple[int, list[str]]:
    """
    Score fundamental basado en múltiplos, rentabilidad, deuda y dividendos.
    Rango aproximado: -8 a +10. Positivo = fundamentals favorables.
    """
    score = 0
    signals = []

    def val(key): return f.get(key)

    # ── Valuación ──
    pe = val("pe")
    if pe is not None and pe > 0:
        if pe < 10:
            score += 2; signals.append(f"✅ P/E bajo ({pe:.1f}x) — valuación atractiva")
        elif pe < 20:
            score += 1; signals.append(f"✅ P/E moderado ({pe:.1f}x)")
        elif pe < 35:
            signals.append(f"👁️ P/E elevado ({pe:.1f}x)")
        else:
            score -= 1; signals.append(f"⚠️ P/E muy alto ({pe:.1f}x) — valuación exigente")
    elif pe is not None and pe < 0:
        score -= 1; signals.append("🔴 P/E negativo — empresa con pérdidas")

    pb = val("pb")
    if pb is not None:
        if pb < 1:
            score += 2; signals.append(f"✅ P/B bajo ({pb:.2f}x) — cotiza bajo valor libro")
        elif pb < 2:
            score += 1; signals.append(f"✅ P/B razonable ({pb:.2f}x)")
        elif pb < 4:
            signals.append(f"👁️ P/B elevado ({pb:.2f}x)")
        else:
            score -= 1; signals.append(f"⚠️ P/B muy alto ({pb:.2f}x)")

    ev = val("ev_ebitda")
    if ev is not None and ev > 0:
        if ev < 8:
            score += 2; signals.append(f"✅ EV/EBITDA bajo ({ev:.1f}x) — empresa barata")
        elif ev < 15:
            score += 1; signals.append(f"✅ EV/EBITDA moderado ({ev:.1f}x)")
        else:
            score -= 1; signals.append(f"⚠️ EV/EBITDA alto ({ev:.1f}x)")

    # ── Rentabilidad ──
    roe = val("roe")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 20:
            score += 2; signals.append(f"✅ ROE alto ({roe_pct:.1f}%) — alta rentabilidad del patrimonio")
        elif roe_pct > 10:
            score += 1; signals.append(f"✅ ROE positivo ({roe_pct:.1f}%)")
        elif roe_pct > 0:
            signals.append(f"👁️ ROE bajo ({roe_pct:.1f}%)")
        else:
            score -= 1; signals.append(f"🔴 ROE negativo ({roe_pct:.1f}%)")

    roa = val("roa")
    if roa is not None:
        roa_pct = roa * 100
        if roa_pct > 10:
            score += 1; signals.append(f"✅ ROA alto ({roa_pct:.1f}%)")
        elif roa_pct > 5:
            signals.append(f"👁️ ROA moderado ({roa_pct:.1f}%)")
        elif roa_pct < 0:
            score -= 1; signals.append(f"🔴 ROA negativo ({roa_pct:.1f}%)")

    mn = val("margen_neto")
    if mn is not None:
        mn_pct = mn * 100
        if mn_pct > 20:
            score += 2; signals.append(f"✅ Margen neto alto ({mn_pct:.1f}%)")
        elif mn_pct > 10:
            score += 1; signals.append(f"✅ Margen neto positivo ({mn_pct:.1f}%)")
        elif mn_pct > 0:
            signals.append(f"👁️ Margen neto bajo ({mn_pct:.1f}%)")
        else:
            score -= 1; signals.append(f"🔴 Margen neto negativo ({mn_pct:.1f}%)")

    # ── Deuda ──
    de = val("debt_eq")
    if de is not None:
        de_v = de / 100 if de > 10 else de   # yfinance a veces devuelve en %
        if de_v < 0.3:
            score += 1; signals.append(f"✅ Deuda/Patrimonio bajo ({de_v:.2f}x) — balance sólido")
        elif de_v < 1.0:
            signals.append(f"👁️ Deuda/Patrimonio moderado ({de_v:.2f}x)")
        elif de_v < 2.0:
            score -= 1; signals.append(f"⚠️ Deuda/Patrimonio elevado ({de_v:.2f}x)")
        else:
            score -= 2; signals.append(f"🔴 Deuda/Patrimonio muy alto ({de_v:.2f}x) — riesgo financiero")

    cr = val("current")
    if cr is not None:
        if cr > 2:
            score += 1; signals.append(f"✅ Current Ratio alto ({cr:.2f}x) — buena liquidez")
        elif cr > 1:
            signals.append(f"👁️ Current Ratio ajustado ({cr:.2f}x)")
        else:
            score -= 1; signals.append(f"🔴 Current Ratio < 1 ({cr:.2f}x) — riesgo de liquidez")

    # ── Dividendos ──
    dy = val("div_yield")
    if dy is not None and dy > 0:
        dy_pct = dy * 100
        if dy_pct > 5:
            score += 2; signals.append(f"✅ Dividend Yield alto ({dy_pct:.1f}%) — renta atractiva")
        elif dy_pct > 2:
            score += 1; signals.append(f"✅ Dividend Yield moderado ({dy_pct:.1f}%)")
        else:
            signals.append(f"👁️ Dividend Yield bajo ({dy_pct:.1f}%)")

    po = val("payout")
    if po is not None:
        po_pct = po * 100
        if po_pct > 100:
            score -= 1; signals.append(f"⚠️ Payout Ratio > 100% ({po_pct:.0f}%) — dividendo insostenible")
        elif po_pct > 80:
            signals.append(f"👁️ Payout Ratio alto ({po_pct:.0f}%)")

    return score, signals


def rec_fundamental(score: int) -> tuple[str, str]:
    """Retorna (etiqueta, color_hex) para el score fundamental."""
    if score >= 8:   return "MUY SÓLIDO",  "#00d4aa"
    if score >= 5:   return "SÓLIDO",       "#4ade80"
    if score >= 2:   return "NEUTRO",       "#fbbf24"
    if score >= -1:  return "DÉBIL",        "#f87171"
    return               "MUY DÉBIL",   "#ff4b6b"


def fmt(val, fmt_str="", suffix="", prefix="", na="N/D"):
    """Formatea un valor fundamental, devuelve N/D si es None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return na
    try:
        if fmt_str:
            return prefix + format(val, fmt_str) + suffix
        return prefix + str(val) + suffix
    except Exception:
        return na


def build_fundamental_radar(f: dict, ticker: str) -> go.Figure:
    """Gráfico radar con las 6 dimensiones fundamentales normalizadas 0-10."""
    def norm(val, lo, hi):
        if val is None or np.isnan(float(val if val else 0)): return 5
        return round(max(0, min(10, (float(val) - lo) / (hi - lo) * 10)), 1)

    roe = f.get("roe") or 0
    roa = f.get("roa") or 0
    mn  = f.get("margen_neto") or 0
    pe  = f.get("pe") or 30
    pb  = f.get("pb") or 3
    de  = f.get("debt_eq") or 100
    cr  = f.get("current") or 1
    dy  = f.get("div_yield") or 0

    dims = {
        "Valuación":     norm(30 - min(pe, 30), 0, 30),
        "ROE":           norm(roe * 100, -10, 30),
        "ROA":           norm(roa * 100, -5, 15),
        "Margen":        norm(mn * 100, -10, 30),
        "Solidez deuda": norm(2 - min(de/100 if de > 10 else de, 2), 0, 2),
        "Liquidez":      norm(cr, 0, 3),
    }

    cats   = list(dims.keys()) + [list(dims.keys())[0]]
    values = list(dims.values()) + [list(dims.values())[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values, theta=cats,
        fill="toself",
        fillcolor="rgba(0,212,170,0.15)",
        line=dict(color="#00d4aa", width=2),
        name=ticker,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10],
                            gridcolor="rgba(255,255,255,0.1)",
                            tickfont=dict(size=9, color="#94a3b8")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)",
                             tickfont=dict(size=11, color="#cbd5e1")),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark",
        height=320,
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
        title=dict(text=f"Perfil fundamental — {ticker}",
                   font=dict(size=12, color="#94a3b8"), x=0.5),
    )
    return fig



# ─── PANEL MACRO ARGENTINO ───────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro() -> dict:
    """
    Obtiene variables macro argentinas desde APIs públicas.
    - Tipos de cambio: dolarapi.com
    - Riesgo país: ambito.com
    Cache: 5 minutos.
    """
    result = {
        "oficial": None, "blue": None, "mep": None, "ccl": None,
        "brecha_blue": None, "brecha_ccl": None, "riesgo_pais": None,
        "error": False,
    }

    # ── Tipos de cambio ──
    try:
        import urllib.request, json as _json
        req = urllib.request.Request(
            "https://dolarapi.com/v1/dolares",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            dolares = _json.loads(r.read().decode())
        for d in dolares:
            casa = d.get("casa", "").lower()
            venta = d.get("venta")
            if casa == "oficial"         : result["oficial"] = venta
            elif casa == "blue"          : result["blue"]    = venta
            elif casa == "bolsa"         : result["mep"]     = venta
            elif casa == "contadoconliqui": result["ccl"]    = venta
    except Exception:
        result["error"] = True

    # ── Brecha ──
    if result["oficial"] and result["oficial"] > 0:
        if result["blue"]:
            result["brecha_blue"] = round((result["blue"] / result["oficial"] - 1) * 100, 1)
        if result["ccl"]:
            result["brecha_ccl"]  = round((result["ccl"]  / result["oficial"] - 1) * 100, 1)

    # ── Riesgo país ──
    try:
        import urllib.request, json as _json
        req2 = urllib.request.Request(
            "https://mercados.ambito.com/riesgo-pais/referencia",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req2, timeout=6) as r:
            rp_data = _json.loads(r.read().decode())
        val = rp_data.get("valor") or rp_data.get("ultimo") or rp_data.get("value")
        if val:
            result["riesgo_pais"] = float(str(val).replace(",", ".").replace(".", "", str(val).count(".")-1))
    except Exception:
        pass

    return result


def render_macro_panel():
    """Renderiza el panel macro como una fila compacta de métricas."""
    macro = fetch_macro()

    def _fmt_dolar(val):
        return f"${val:,.0f}" if val else "—"

    def _brecha_color(val):
        if val is None: return "#94a3b8"
        if val < 20:    return "#4ade80"
        if val < 50:    return "#fbbf24"
        return "#f87171"

    def _rp_color(val):
        if val is None: return "#94a3b8"
        if val < 800:   return "#4ade80"
        if val < 1500:  return "#fbbf24"
        return "#f87171"

    ofic  = _fmt_dolar(macro["oficial"])
    blue  = _fmt_dolar(macro["blue"])
    mep   = _fmt_dolar(macro["mep"])
    ccl   = _fmt_dolar(macro["ccl"])
    b_bl  = f"{macro['brecha_blue']:+.1f}%" if macro["brecha_blue"] is not None else "—"
    b_ccl = f"{macro['brecha_ccl']:+.1f}%"  if macro["brecha_ccl"]  is not None else "—"
    rp    = f"{macro['riesgo_pais']:,.0f} bps" if macro["riesgo_pais"] else "—"

    bc  = _brecha_color(macro["brecha_ccl"])
    bbc = _brecha_color(macro["brecha_blue"])
    rpc = _rp_color(macro["riesgo_pais"])

    st.markdown(f"""
    <div style="background:#13161f;border:1px solid #1e2235;border-radius:10px;
                padding:10px 20px;margin-bottom:14px;display:flex;
                align-items:center;gap:0;flex-wrap:wrap">
      <span style="color:#94a3b8;font-size:11px;font-weight:600;
                   letter-spacing:.05em;margin-right:18px">🌐 MACRO AR</span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">Oficial </span>
        <span style="color:#e2e8f0;font-weight:700">{ofic}</span>
      </span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">Blue </span>
        <span style="color:#e2e8f0;font-weight:700">{blue}</span>
      </span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">MEP </span>
        <span style="color:#e2e8f0;font-weight:700">{mep}</span>
      </span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">CCL </span>
        <span style="color:#e2e8f0;font-weight:700">{ccl}</span>
      </span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">Brecha CCL </span>
        <span style="color:{bc};font-weight:700">{b_ccl}</span>
      </span>
      <span style="margin-right:22px;font-size:13px">
        <span style="color:#64748b">Brecha Blue </span>
        <span style="color:{bbc};font-weight:700">{b_bl}</span>
      </span>
      <span style="font-size:13px">
        <span style="color:#64748b">Riesgo País </span>
        <span style="color:{rpc};font-weight:700">{rp}</span>
      </span>
    </div>
    """, unsafe_allow_html=True)


# ─── CEDEARS ─────────────────────────────────────────────────────────────────

CEDEARS: dict[str, tuple[str, str, int]] = {
    # ticker.BA : (nombre, ticker_usd_yf, ratio_cedear)
    "AAPL.BA":  ("Apple",           "AAPL",  10),
    "MSFT.BA":  ("Microsoft",       "MSFT",  10),
    "GOOGL.BA": ("Alphabet",        "GOOGL", 10),
    "AMZN.BA":  ("Amazon",          "AMZN",  10),
    "TSLA.BA":  ("Tesla",           "TSLA",  10),
    "META.BA":  ("Meta",            "META",  10),
    "NVDA.BA":  ("Nvidia",          "NVDA",  10),
    "BABA.BA":  ("Alibaba",         "BABA",   5),
    "MELI.BA":  ("MercadoLibre",    "MELI",   1),
    "GLOB.BA":  ("Globant",         "GLOB",   1),
    "AMD.BA":   ("AMD",             "AMD",   10),
    "INTC.BA":  ("Intel",           "INTC",  10),
    "QCOM.BA":  ("Qualcomm",        "QCOM",  10),
    "KO.BA":    ("Coca-Cola",       "KO",    10),
    "DIS.BA":   ("Disney",          "DIS",   10),
    "WMT.BA":   ("Walmart",         "WMT",   10),
    "JPM.BA":   ("JPMorgan",        "JPM",   10),
    "GS.BA":    ("Goldman Sachs",   "GS",    10),
    "XOM.BA":   ("ExxonMobil",      "XOM",   10),
    "GOLD.BA":  ("Barrick Gold",    "GOLD",  10),
    "BAC.BA":   ("Bank of America", "BAC",   10),
    "PBR.BA":   ("Petrobras",       "PBR",   10),
}

CEDEAR_SECTORS = {
    "AAPL.BA":"Tecnología","MSFT.BA":"Tecnología","GOOGL.BA":"Tecnología",
    "AMZN.BA":"Tecnología","TSLA.BA":"Automotriz","META.BA":"Tecnología",
    "NVDA.BA":"Tecnología","BABA.BA":"Tecnología","MELI.BA":"Tecnología",
    "GLOB.BA":"Tecnología","AMD.BA":"Tecnología","INTC.BA":"Tecnología",
    "QCOM.BA":"Tecnología","KO.BA":"Consumo","DIS.BA":"Entretenimiento",
    "WMT.BA":"Consumo","JPM.BA":"Financiero","GS.BA":"Financiero",
    "XOM.BA":"Energía","GOLD.BA":"Materiales","BAC.BA":"Financiero",
    "PBR.BA":"Energía",
}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_cedears(ccl: float | None) -> pd.DataFrame:
    """
    Descarga precios ARS y USD de cada CEDEAR y calcula el CCL implícito.
    """
    if not ccl or ccl <= 0:
        ccl = 1200.0   # fallback si no hay dato macro

    tickers_ba  = list(CEDEARS.keys())
    tickers_usd = list(set(v[1] for v in CEDEARS.values()))

    rows = []
    try:
        # Precios ARS (batch)
        raw_ar = yf.download(tickers_ba, period="5d", auto_adjust=True,
                             progress=False, threads=True)
        # Precios USD (batch)
        raw_us = yf.download(tickers_usd, period="5d", auto_adjust=True,
                             progress=False, threads=True)
    except Exception:
        return pd.DataFrame()

    def _last(raw, ticker):
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                s = raw["Close"][ticker].dropna()
            else:
                s = raw["Close"].dropna()
            return float(s.iloc[-1]) if len(s) else None
        except Exception:
            return None

    for ticker_ba, (nombre, ticker_usd, ratio) in CEDEARS.items():
        p_ar  = _last(raw_ar, ticker_ba)
        p_us  = _last(raw_us, ticker_usd)
        if p_ar is None or p_us is None or p_us == 0:
            continue

        ccl_impl  = round(p_ar / (p_us / ratio), 2)  # cada 1 acción US = ratio CEDEARs
        premium   = round((ccl_impl / ccl - 1) * 100, 2)
        sector    = CEDEAR_SECTORS.get(ticker_ba, "—")
        sym       = ticker_ba.replace(".BA", "")

        rows.append({
            "Ticker":       sym,
            "Nombre":       nombre,
            "Sector":       sector,
            "Precio ARS $": round(p_ar, 2),
            "Precio USD $": round(p_us, 2),
            "Ratio":        ratio,
            "CCL Implícito":ccl_impl,
            "CCL Referencia":round(ccl, 2),
            "Prima/Desc %": premium,
            "_oport":       abs(premium),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Prima/Desc %", key=abs).reset_index(drop=True)
    return df


# ─── CORRELACIÓN ─────────────────────────────────────────────────────────────

def build_correlation_heatmap(data: dict[str, pd.DataFrame], min_periods: int = 30) -> go.Figure:
    """Heatmap de correlación de retornos diarios entre todos los tickers disponibles."""
    returns = {}
    for ticker, df in data.items():
        sym = ticker.replace(".BA", "")
        try:
            r = df["Close"].pct_change().dropna()
            if len(r) >= min_periods:
                returns[sym] = r
        except Exception:
            continue

    if len(returns) < 2:
        return go.Figure()

    ret_df  = pd.DataFrame(returns).dropna(how="all")
    corr_df = ret_df.corr()
    labels  = corr_df.columns.tolist()
    matrix  = corr_df.values

    # Colorscale divergente centrada en 0
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=labels, y=labels,
        colorscale=[
            [0.0,  "#ff4b6b"],
            [0.25, "#f87171"],
            [0.5,  "#1e2235"],
            [0.75, "#4ade80"],
            [1.0,  "#00d4aa"],
        ],
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Correlación: %{z:.3f}<extra></extra>",
    ))

    n = len(labels)
    h = max(500, n * 22)
    fig.update_layout(
        template="plotly_dark",
        height=h,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=10),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
        title=dict(text="Correlación de retornos diarios", font=dict(size=13, color="#94a3b8")),
    )
    return fig


# ─── HISTORIAL DE SEÑALES ────────────────────────────────────────────────────

HIST_KEY = "signal_history"   # clave en st.session_state


def save_signal_snapshot(results_df: pd.DataFrame, macro: dict) -> None:
    """
    Guarda un snapshot del screener actual en session_state.
    Cada fila lleva timestamp, macro vars y señal técnica.
    """
    if HIST_KEY not in st.session_state:
        st.session_state[HIST_KEY] = []

    ts  = datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M")
    ccl = macro.get("ccl") or ""
    rp  = macro.get("riesgo_pais") or ""

    for _, row in results_df.iterrows():
        st.session_state[HIST_KEY].append({
            "Timestamp":    ts,
            "Ticker":       row["Ticker"],
            "Score":        row["Score"],
            "Señal":        row["Señal"],
            "Precio $":     row["Precio $"],
            "Var %":        row["Var %"],
            "RSI":          row["RSI"],
            "RVOL":         row["RVOL"],
            "CCL":          ccl,
            "Riesgo País":  rp,
        })


def build_history_chart(hist_df: pd.DataFrame, ticker: str) -> go.Figure:
    """Score histórico de un ticker a lo largo del tiempo."""
    df_t = hist_df[hist_df["Ticker"] == ticker].copy()
    df_t["Timestamp"] = pd.to_datetime(df_t["Timestamp"])
    df_t = df_t.sort_values("Timestamp")

    fig = go.Figure()
    bar_colors = [score_color(int(v)) for v in df_t["Score"]]
    fig.add_trace(go.Bar(
        x=df_t["Timestamp"], y=df_t["Score"],
        marker_color=bar_colors, opacity=0.8, name="Score",
        hovertemplate="<b>%{x}</b><br>Score: %{y}<extra></extra>",
    ))
    fig.add_hline(y=3,  line_dash="dash", line_color="#4ade80", opacity=0.6,
                  annotation_text="Compra", annotation_font_size=10)
    fig.add_hline(y=-2, line_dash="dash", line_color="#f87171", opacity=0.6,
                  annotation_text="Venta", annotation_font_size=10)
    fig.add_hline(y=0,  line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.update_layout(
        template="plotly_dark", height=260,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text=f"Evolución del score — {ticker}",
                   font=dict(size=12, color="#94a3b8")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    )
    return fig


# ─── COMPARADOR DE PAPELES ───────────────────────────────────────────────────

def build_comparison_chart(
    data: dict[str, pd.DataFrame],
    tickers: list[str],
    merval_df: pd.DataFrame | None = None,
) -> go.Figure:
    """Retornos normalizados (base 100) de múltiples tickers + Merval opcional."""
    fig = go.Figure()
    COLORS = ["#00d4aa", "#a78bfa", "#fb923c", "#f43f5e", "#38bdf8"]

    for i, ticker in enumerate(tickers):
        sym = ticker if ticker.endswith(".BA") else ticker + ".BA"
        df  = data.get(sym)
        if df is None or len(df) < 2:
            continue
        close   = df["Close"].dropna()
        normed  = close / float(close.iloc[0]) * 100
        nombre  = TICKERS.get(sym, (ticker,"",""))[0]
        color   = COLORS[i % len(COLORS)]
        var_tot = round(float(normed.iloc[-1]) - 100, 2)
        fig.add_trace(go.Scatter(
            x=normed.index, y=normed.values,
            name=f"{ticker} ({var_tot:+.1f}%)",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>{ticker}</b><br>%{{x}}<br>Retorno: %{{y:.1f}}<extra></extra>",
        ))

    if merval_df is not None and len(merval_df) > 1:
        close_m = merval_df["Close"].dropna()
        normed_m = close_m / float(close_m.iloc[0]) * 100
        var_m   = round(float(normed_m.iloc[-1]) - 100, 2)
        fig.add_trace(go.Scatter(
            x=normed_m.index, y=normed_m.values,
            name=f"Merval ({var_m:+.1f}%)",
            line=dict(color="#94a3b8", width=1.5, dash="dot"),
            hovertemplate="<b>Merval</b><br>%{x}<br>Retorno: %{y:.1f}<extra></extra>",
        ))

    fig.add_hline(y=100, line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.update_layout(
        template="plotly_dark",
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08, font=dict(size=11)),
        yaxis=dict(ticksuffix="", title="Base 100",
                   gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)",
                   rangebreaks=[dict(bounds=["sat", "mon"])]),
    )
    return fig


def build_drawdown_chart(
    data: dict[str, pd.DataFrame],
    tickers: list[str],
) -> go.Figure:
    """Drawdown desde máximo para cada ticker seleccionado."""
    fig = go.Figure()
    COLORS      = ["#00d4aa", "#a78bfa", "#fb923c", "#f43f5e", "#38bdf8"]
    FILL_COLORS = ["rgba(0,212,170,0.08)", "rgba(167,139,250,0.08)",
                   "rgba(251,146,60,0.08)", "rgba(244,63,94,0.08)",
                   "rgba(56,189,248,0.08)"]

    for i, ticker in enumerate(tickers):
        sym  = ticker if ticker.endswith(".BA") else ticker + ".BA"
        df   = data.get(sym)
        if df is None or len(df) < 2:
            continue
        close    = df["Close"].dropna()
        roll_max = close.cummax()
        dd       = (close - roll_max) / roll_max * 100
        color    = COLORS[i % len(COLORS)]
        fcolor   = FILL_COLORS[i % len(FILL_COLORS)]
        fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values,
            name=ticker,
            line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=fcolor,
            hovertemplate=f"<b>{ticker}</b><br>%{{x}}<br>DD: %{{y:.1f}}%<extra></extra>",
        ))

    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)", line_width=1)
    fig.update_layout(
        template="plotly_dark",
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e1117",
        font=dict(color="#cbd5e1", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08, font=dict(size=11)),
        yaxis=dict(ticksuffix="%", title="Drawdown",
                   gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)",
                   rangebreaks=[dict(bounds=["sat", "mon"])]),
    )
    return fig


# ─── WATCHLIST PERSISTENTE ───────────────────────────────────────────────────

WATCHLIST_FILE = "watchlist.json"


def load_watchlist() -> list[str]:
    try:
        if os.path.exists(WATCHLIST_FILE):
            import json
            return json.load(open(WATCHLIST_FILE, "r"))
    except Exception:
        pass
    return []


def save_watchlist(tickers: list[str]) -> None:
    try:
        import json
        json.dump(tickers, open(WATCHLIST_FILE, "w"), indent=2)
    except Exception:
        pass


# ─── SIMULADOR DE POSICIÓN ───────────────────────────────────────────────────

def calc_position(
    capital: float,
    risk_pct: float,
    price: float,
    atr: float,
    atr_mult: float = 2.0,
    commission_pct: float = 0.006,
) -> dict:
    """
    Calcula sizing óptimo de posición basado en riesgo fijo por operación.
    """
    risk_amount  = capital * (risk_pct / 100)
    stop_dist    = atr * atr_mult
    stop_price   = price - stop_dist
    shares       = max(1, int(risk_amount / stop_dist))

    gross_invest = shares * price
    commission   = gross_invest * commission_pct
    net_invest   = gross_invest + commission
    pct_capital  = net_invest / capital * 100

    target_1     = price + stop_dist           # 1:1
    target_2     = price + stop_dist * 2       # 1:2
    target_3     = price + stop_dist * 3       # 1:3

    gain_t1      = (target_1 - price) * shares - commission
    gain_t2      = (target_2 - price) * shares - commission
    gain_t3      = (target_3 - price) * shares - commission
    loss_sl      = (price - stop_price) * shares + commission

    return {
        "shares":       shares,
        "price":        round(price, 2),
        "stop":         round(stop_price, 2),
        "stop_dist":    round(stop_dist, 2),
        "stop_dist_pct":round(stop_dist / price * 100, 2),
        "target_1":     round(target_1, 2),
        "target_2":     round(target_2, 2),
        "target_3":     round(target_3, 2),
        "gross_invest": round(gross_invest, 2),
        "commission":   round(commission, 2),
        "net_invest":   round(net_invest, 2),
        "pct_capital":  round(pct_capital, 2),
        "risk_amount":  round(risk_amount, 2),
        "gain_t1":      round(gain_t1, 2),
        "gain_t2":      round(gain_t2, 2),
        "gain_t3":      round(gain_t3, 2),
        "loss_sl":      round(loss_sl, 2),
        "rr_1":         round(gain_t1 / loss_sl, 2) if loss_sl > 0 else 0,
        "rr_2":         round(gain_t2 / loss_sl, 2) if loss_sl > 0 else 0,
        "rr_3":         round(gain_t3 / loss_sl, 2) if loss_sl > 0 else 0,
    }


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
    save_signal_snapshot(results_df, fetch_macro())

    # ══ PANEL MACRO ════════════════════════════════════════════════════════
    macro_data = fetch_macro()
    render_macro_panel()

    # ══ GUARDAR SNAPSHOT ════════════════════════════════════════════════
    if "results_df" in dir() or True:
        pass   # snapshot se guarda tras calcular results_df (ver abajo)

    # ══ TABS ═══════════════════════════════════════════════════════════════

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(["📊 Ranking & Screener", "📈 Análisis Individual", "🔔 Alertas", "🧪 Backtester", "📑 Análisis Fundamental", "💱 CEDEARs", "🔗 Correlación", "📜 Historial", "⚖️ Comparador", "📋 Watchlist", "🎯 Sizing"])

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

        # ── Filtro por señal ──
        todas_señales = ["COMPRA FUERTE", "COMPRA", "NEUTRAL", "VENTA", "VENTA FUERTE"]
        señal_filter = st.multiselect(
            "Filtrar por señal",
            todas_señales,
            default=todas_señales,
            help="Seleccioná una o más señales para filtrar el ranking"
        )
        filtered_df = results_df[results_df["Señal"].isin(señal_filter)] if señal_filter else results_df

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
            filtered_df[display_cols]
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
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
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


    # ─────────────────────────────────────────────────────────────────────
    # TAB 4 — BACKTESTER
    # ─────────────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("🧪 Backtester de Estrategia Técnica")
        st.caption("Simulación histórica basada en el score técnico del screener. No incluye comisiones ni slippage.")

        # ── Controles ──
        bc1, bc2 = st.columns([1, 2])
        with bc1:
            bt_mode = st.radio("Modo", ["Ticker individual", "Portfolio completo"],
                               horizontal=False)

        with bc2:
            bk1, bk2 = st.columns(2)
            with bk1:
                bt_entry   = st.slider("Score mínimo de entrada", 1, 8, 3, 1,
                                       help="Score >= N para abrir posición")
                bt_hold    = st.slider("Período de hold (ruedas)", 3, 30, 10, 1,
                                       help="Máximo de días a mantener la posición")
            with bk2:
                bt_stop    = st.slider("Stop Loss %", 2, 15, 5, 1,
                                       help="Cierra la posición si cae este %") / 100
                bt_target  = st.slider("Target %", 3, 30, 10, 1,
                                       help="Cierra la posición si sube este %") / 100

        st.divider()

        # ── Ticker individual ──
        if bt_mode == "Ticker individual":
            bt_ticker = st.selectbox(
                "Seleccioná un ticker",
                list(detail_store.keys()),
                format_func=lambda x: f"{x}  —  {TICKERS.get(x+'.BA', ('?','?','?'))[0]}"
            )

            if bt_ticker and bt_ticker in detail_store:
                df_bt = detail_store[bt_ticker]["df"]

                with st.spinner("⏳ Calculando score histórico y simulando operaciones…"):
                    score_s  = compute_score_series(df_bt)
                    trades_df, equity_s, bh_s = run_backtest(
                        df_bt, score_s, bt_entry, bt_hold, bt_stop, bt_target
                    )
                    trades_df["Ticker"] = bt_ticker
                    mets = backtest_metrics(trades_df, equity_s, bh_s)

                # ── Métricas resumen ──
                m1,m2,m3,m4,m5,m6,m7,m8 = st.columns(8)
                def _delta_color(v): return "normal" if v >= 0 else "inverse"

                m1.metric("📈 Retorno estrategia", f"{mets['Total Return %']:+.1f}%",
                          delta=f"{mets['Total Return %'] - mets['B&H Return %']:+.1f}% vs B&H")
                m2.metric("📊 Buy & Hold",         f"{mets['B&H Return %']:+.1f}%")
                m3.metric("🎯 Win Rate",            f"{mets['Win Rate %']}%")
                m4.metric("⚡ Profit Factor",       f"{mets['Profit Factor']}")
                m5.metric("📐 Sharpe",              f"{mets['Sharpe']}")
                m6.metric("📉 Max Drawdown",        f"{mets['Max Drawdown %']:.1f}%")
                m7.metric("🔢 Operaciones",         mets["N° Operaciones"])
                m8.metric("⏱ Promedio días",        f"{mets['Avg días']}")

                st.divider()

                # ── Equity curve ──
                st.plotly_chart(build_equity_chart(equity_s, bh_s, bt_ticker),
                                use_container_width=True)

                # ── Gráfico precio + score ──
                st.plotly_chart(build_score_chart(score_s, df_bt, bt_entry, trades_df),
                                use_container_width=True)

                # ── Tabla de operaciones ──
                if not trades_df.empty:
                    st.subheader(f"📋 Operaciones simuladas ({len(trades_df)})")

                    def _color_ret(val):
                        return "color:#4ade80;font-weight:700" if val > 0 else "color:#f87171;font-weight:700"

                    display_trades = trades_df.drop(columns=["_ret", "Ticker"], errors="ignore")
                    styled_trades = (
                        display_trades.style
                        .map(_color_ret, subset=["Retorno %"])
                        .format({"Precio entrada": "${:,.2f}", "Precio salida": "${:,.2f}",
                                 "Retorno %": "{:+.2f}%"})
                    )
                    st.dataframe(styled_trades, use_container_width=True, height=380)

                    csv_bt = display_trades.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Exportar operaciones (CSV)", csv_bt,
                                       f"backtest_{bt_ticker}.csv", "text/csv")
                else:
                    st.info("Sin operaciones generadas con los parámetros actuales. Probá bajar el score de entrada o ampliar el período histórico.")

        # ── Portfolio completo ──
        else:
            if st.button("▶️ Correr backtest de portfolio", type="primary", use_container_width=False):
                all_trades  = []
                equities    = {}
                bh_returns  = {}

                progress = st.progress(0, text="Procesando tickers…")
                tickers_bt = list(detail_store.keys())

                for idx, sym in enumerate(tickers_bt):
                    progress.progress((idx + 1) / len(tickers_bt), text=f"Procesando {sym}…")
                    df_bt = detail_store[sym]["df"]
                    try:
                        score_s = compute_score_series(df_bt)
                        trd, eq_s, bh_s = run_backtest(df_bt, score_s, bt_entry, bt_hold, bt_stop, bt_target)
                        trd["Ticker"] = sym
                        all_trades.append(trd)
                        equities[sym]   = eq_s
                        bh_returns[sym] = float(bh_s.iloc[-1]) - 100
                    except Exception:
                        continue

                progress.empty()

                if not equities:
                    st.warning("No se pudo correr el backtest en ningún ticker.")
                else:
                    # Equity portfolio = promedio simple de todas las curves
                    eq_df    = pd.DataFrame(equities).ffill()
                    eq_port  = eq_df.mean(axis=1)
                    bh_avg   = np.mean(list(bh_returns.values()))

                    all_trades_df = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
                    bh_series_fake = pd.Series(
                        [100 + bh_avg * t / len(eq_port) for t in range(len(eq_port))],
                        index=eq_port.index
                    )
                    mets_p = backtest_metrics(all_trades_df, eq_port, bh_series_fake)

                    # Métricas portfolio
                    pm1,pm2,pm3,pm4,pm5,pm6,pm7,pm8 = st.columns(8)
                    pm1.metric("📈 Retorno portfolio",  f"{mets_p['Total Return %']:+.1f}%")
                    pm2.metric("📊 B&H promedio",       f"{bh_avg:+.1f}%")
                    pm3.metric("🎯 Win Rate global",    f"{mets_p['Win Rate %']}%")
                    pm4.metric("⚡ Profit Factor",      f"{mets_p['Profit Factor']}")
                    pm5.metric("📐 Sharpe",             f"{mets_p['Sharpe']}")
                    pm6.metric("📉 Max Drawdown",       f"{mets_p['Max Drawdown %']:.1f}%")
                    pm7.metric("🔢 Total operaciones",  mets_p["N° Operaciones"])
                    pm8.metric("⏱ Avg días",            f"{mets_p['Avg días']}")

                    st.divider()

                    # Equity curve portfolio
                    st.plotly_chart(
                        build_equity_chart(eq_port, bh_series_fake, "Portfolio completo"),
                        use_container_width=True
                    )

                    # Top performers
                    if not all_trades_df.empty:
                        col_tp, col_bt = st.columns(2)

                        with col_tp:
                            st.subheader("🏆 Top performers")
                            perf = (
                                all_trades_df.groupby("Ticker")
                                .agg(
                                    Operaciones=("_ret", "count"),
                                    Retorno_total=("_ret", lambda x: round(x.sum() * 100, 2)),
                                    Win_rate=("_ret", lambda x: round((x > 0).mean() * 100, 1)),
                                )
                                .sort_values("Retorno_total", ascending=False)
                            )
                            st.dataframe(perf.head(10), use_container_width=True)

                        with col_bt:
                            st.subheader("📋 Todas las operaciones")
                            display_all = all_trades_df.drop(columns=["_ret"], errors="ignore")
                            st.dataframe(
                                display_all.style.map(
                                    lambda v: "color:#4ade80;font-weight:700" if v > 0 else "color:#f87171;font-weight:700",
                                    subset=["Retorno %"]
                                ).format({"Retorno %": "{:+.2f}%",
                                          "Precio entrada": "${:,.2f}",
                                          "Precio salida":  "${:,.2f}"}),
                                use_container_width=True, height=380
                            )

                        csv_port = all_trades_df.drop(columns=["_ret"], errors="ignore").to_csv(index=False).encode("utf-8")
                        st.download_button("📥 Exportar todas las operaciones (CSV)",
                                           csv_port, "backtest_portfolio.csv", "text/csv")
            else:
                st.info("Configurá los parámetros y presioná **▶️ Correr backtest de portfolio** para simular la estrategia en todos los tickers del panel seleccionado.")


    # ─────────────────────────────────────────────────────────────────────
    # TAB 5 — ANÁLISIS FUNDAMENTAL
    # ─────────────────────────────────────────────────────────────────────
    with tab5:
        st.subheader("📑 Análisis Fundamental")
        st.caption("Datos: yfinance · Cache 24 hs · Cobertura variable según ticker (mejor en Panel Líder)")

        f_mode = st.radio("Vista", ["Ticker individual", "Screener fundamental"],
                          horizontal=True)
        st.divider()

        # ══ DESCARGA FUNDAMENTALES ══════════════════════════════════════
        with st.spinner("⏳ Descargando métricas fundamentales…"):
            fund_data = fetch_fundamentals(tuple(tickers_list))

        # ══ TICKER INDIVIDUAL ═══════════════════════════════════════════
        if f_mode == "Ticker individual":
            f_ticker = st.selectbox(
                "Seleccioná un ticker",
                list(detail_store.keys()),
                format_func=lambda x: f"{x}  —  {TICKERS.get(x+'.BA', ('?','?','?'))[0]}",
                key="f_ticker_sel"
            )

            if f_ticker:
                f = fund_data.get(f_ticker + ".BA", {})
                tech_score = detail_store[f_ticker]["score"]
                tech_rec   = detail_store[f_ticker]["rec"]
                fund_score, fund_signals = score_fundamentals(f)
                fund_rec_label, fund_rec_color = rec_fundamental(fund_score)
                combined   = tech_score + fund_score
                comb_label = "COMPRA FUERTE" if combined >= 10 else                              "COMPRA"        if combined >= 5  else                              "NEUTRAL"       if combined >= -2 else                              "VENTA"         if combined >= -6 else "VENTA FUERTE"

                nombre, sector, panel = TICKERS.get(f_ticker + ".BA", ("?","?","?"))
                st.markdown(
                    f"### {f_ticker} &nbsp;"
                    f"<small style='color:#94a3b8'>{nombre} · {sector} · Panel {panel}</small>",
                    unsafe_allow_html=True
                )

                # ── Scores: técnico / fundamental / combinado ──
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.markdown(f"""
                    <div style='background:#1a1d27;border:1px solid #2d3148;border-radius:10px;padding:16px;text-align:center'>
                        <div style='color:#94a3b8;font-size:12px;margin-bottom:6px'>📊 SCORE TÉCNICO</div>
                        <div style='font-size:2em;font-weight:700;color:{score_color(tech_score)}'>{tech_score:+d}</div>
                        <div style='font-size:13px;color:{score_color(tech_score)};margin-top:4px'>{tech_rec}</div>
                    </div>""", unsafe_allow_html=True)
                with sc2:
                    st.markdown(f"""
                    <div style='background:#1a1d27;border:1px solid #2d3148;border-radius:10px;padding:16px;text-align:center'>
                        <div style='color:#94a3b8;font-size:12px;margin-bottom:6px'>📑 SCORE FUNDAMENTAL</div>
                        <div style='font-size:2em;font-weight:700;color:{fund_rec_color}'>{fund_score:+d}</div>
                        <div style='font-size:13px;color:{fund_rec_color};margin-top:4px'>{fund_rec_label}</div>
                    </div>""", unsafe_allow_html=True)
                with sc3:
                    comb_color = score_color(combined // 2)
                    st.markdown(f"""
                    <div style='background:#1a1d27;border:2px solid {comb_color};border-radius:10px;padding:16px;text-align:center'>
                        <div style='color:#94a3b8;font-size:12px;margin-bottom:6px'>⚡ SCORE COMBINADO</div>
                        <div style='font-size:2em;font-weight:700;color:{comb_color}'>{combined:+d}</div>
                        <div style='font-size:13px;color:{comb_color};margin-top:4px'>{comb_label}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Radar + métricas lado a lado ──
                col_radar, col_mets = st.columns([1, 1])

                with col_radar:
                    st.plotly_chart(build_fundamental_radar(f, f_ticker),
                                    use_container_width=True)

                with col_mets:
                    # Tabla de métricas con 4 secciones
                    sections = [
                        ("📐 Valuación", [
                            ("P/E (trailing)",  fmt(f.get("pe"),        ".1f", "x")),
                            ("P/B",             fmt(f.get("pb"),        ".2f", "x")),
                            ("EV/EBITDA",       fmt(f.get("ev_ebitda"), ".1f", "x")),
                        ]),
                        ("💰 Rentabilidad", [
                            ("ROE",         fmt(f.get("roe"),         ".1%") if f.get("roe") is not None else "N/D"),
                            ("ROA",         fmt(f.get("roa"),         ".1%") if f.get("roa") is not None else "N/D"),
                            ("Margen Neto", fmt(f.get("margen_neto"), ".1%") if f.get("margen_neto") is not None else "N/D"),
                        ]),
                        ("🏦 Deuda y Liquidez", [
                            ("Debt/Equity",   fmt(f.get("debt_eq"),  ".2f", "x") if f.get("debt_eq") is not None else "N/D"),
                            ("Current Ratio", fmt(f.get("current"),  ".2f", "x")),
                        ]),
                        ("💵 Dividendos", [
                            ("Dividend Yield", fmt(f.get("div_yield"), ".2%") if f.get("div_yield") is not None else "N/D"),
                            ("Payout Ratio",   fmt(f.get("payout"),   ".1%") if f.get("payout")    is not None else "N/D"),
                        ]),
                    ]

                    for title, items in sections:
                        st.markdown(f"**{title}**")
                        rows_html = "".join(
                            f"<tr><td style='padding:4px 8px;color:#94a3b8;font-size:13px'>{k}</td>"
                            f"<td style='padding:4px 8px;font-weight:600;font-size:13px;"
                            f"color:{'#cbd5e1' if v != 'N/D' else '#4b5563'}'>{v}</td></tr>"
                            for k, v in items
                        )
                        st.markdown(
                            f"<table style='width:100%;border-collapse:collapse'>{rows_html}</table>",
                            unsafe_allow_html=True
                        )
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                st.divider()

                # ── Señales fundamentales ──
                with st.expander("📌 Señales fundamentales detectadas", expanded=True):
                    if fund_signals:
                        col_a, col_b = st.columns(2)
                        for i, sig in enumerate(fund_signals):
                            (col_a if i % 2 == 0 else col_b).markdown(f"- {sig}")
                    else:
                        st.info("Sin datos fundamentales suficientes para este ticker.")

        # ══ SCREENER FUNDAMENTAL ════════════════════════════════════════
        else:
            st.markdown("##### Ranking por score fundamental — todos los tickers analizados")

            fund_rows = []
            for sym in detail_store.keys():
                f = fund_data.get(sym + ".BA", {})
                nombre, sector, panel = TICKERS.get(sym + ".BA", ("?","?","?"))
                tech_sc  = detail_store[sym]["score"]
                fund_sc, _ = score_fundamentals(f)
                combined_sc = tech_sc + fund_sc
                f_label, f_color = rec_fundamental(fund_sc)

                fund_rows.append({
                    "Ticker":       sym,
                    "Nombre":       nombre,
                    "Panel":        panel,
                    "Sector":       sector,
                    "Score Téc.":   tech_sc,
                    "Score Fund.":  fund_sc,
                    "Score Comb.":  combined_sc,
                    "Señal Fund.":  f_label,
                    "P/E":          fmt(f.get("pe"),        ".1f"),
                    "P/B":          fmt(f.get("pb"),        ".2f"),
                    "EV/EBITDA":    fmt(f.get("ev_ebitda"), ".1f"),
                    "ROE":          fmt(f.get("roe"),        ".1%") if f.get("roe")  is not None else "N/D",
                    "ROA":          fmt(f.get("roa"),        ".1%") if f.get("roa")  is not None else "N/D",
                    "Marg. Neto":   fmt(f.get("margen_neto"),".1%") if f.get("margen_neto") is not None else "N/D",
                    "Debt/Eq.":     fmt(f.get("debt_eq"),   ".2f") if f.get("debt_eq") is not None else "N/D",
                    "Curr. Ratio":  fmt(f.get("current"),   ".2f"),
                    "Div. Yield":   fmt(f.get("div_yield"), ".2%") if f.get("div_yield") is not None else "N/D",
                })

            if not fund_rows:
                st.info("Sin datos para mostrar.")
            else:
                fund_df = pd.DataFrame(fund_rows).sort_values("Score Comb.", ascending=False).reset_index(drop=True)

                # Filtro rápido
                ff1, ff2 = st.columns([2, 2])
                with ff1:
                    sort_fund = st.selectbox("Ordenar por",
                        ["Score Comb.", "Score Téc.", "Score Fund."], key="sort_fund")
                with ff2:
                    panel_fund = st.multiselect("Panel", ["Líder", "General"],
                        default=["Líder", "General"], key="panel_fund")

                fund_df = fund_df[fund_df["Panel"].isin(panel_fund)] if panel_fund else fund_df
                fund_df = fund_df.sort_values(sort_fund, ascending=False).reset_index(drop=True)

                FUND_COLORS = {
                    "MUY SÓLIDO": ("#00d4aa", "#0d2b24"),
                    "SÓLIDO":     ("#4ade80", "#0f2318"),
                    "NEUTRO":     ("#fbbf24", "#2b2410"),
                    "DÉBIL":      ("#f87171", "#2b1010"),
                    "MUY DÉBIL":  ("#ff4b6b", "#330a14"),
                }

                def _color_fund_señal(val):
                    c, bg = FUND_COLORS.get(val, ("#aaa", "#222"))
                    return f"background-color:{bg};color:{c};font-weight:700"

                def _color_comb(val):
                    return f"color:{score_color(val // 2)};font-weight:700"

                display_fund_cols = ["Ticker","Nombre","Panel","Score Téc.","Score Fund.",
                                     "Score Comb.","Señal Fund.","P/E","P/B","ROE","ROA",
                                     "Marg. Neto","Debt/Eq.","Div. Yield"]

                styled_fund = (
                    fund_df[display_fund_cols].style
                    .map(_color_fund_señal, subset=["Señal Fund."])
                    .map(_color_comb,       subset=["Score Comb."])
                    .map(_color_score,      subset=["Score Téc."])
                    .map(lambda v: "color:#fbbf24;font-weight:600" if v == "N/D" else "",
                         subset=["P/E","P/B","ROE","ROA","Marg. Neto","Debt/Eq.","Div. Yield"])
                    .format({"Score Téc.":  "{:+d}",
                             "Score Fund.": "{:+d}",
                             "Score Comb.": "{:+d}"})
                )

                st.dataframe(styled_fund, use_container_width=True, height=500)

                csv_fund = fund_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Exportar screener fundamental (CSV)",
                                   csv_fund, "screener_fundamental.csv", "text/csv")


    # ─────────────────────────────────────────────────────────────────────
    # TAB 6 — CEDEARs
    # ─────────────────────────────────────────────────────────────────────
    with tab6:
        st.subheader("💱 Tracker de CEDEARs — Dólar Implícito")
        st.caption("Compara el CCL implícito de cada CEDEAR vs el CCL de referencia del panel macro.")

        macro_now = fetch_macro()
        ccl_ref   = macro_now.get("ccl") or 0
        cedear_df = fetch_cedears(ccl_ref)

        if cedear_df.empty:
            st.warning("No se pudieron obtener datos de CEDEARs. Revisá la conexión.")
        else:
            # ── Métricas resumen ──
            n_desc   = (cedear_df["Prima/Desc %"] < -2).sum()
            n_prem   = (cedear_df["Prima/Desc %"] >  2).sum()
            n_par    = len(cedear_df) - n_desc - n_prem
            avg_impl = cedear_df["CCL Implícito"].mean()

            cm1, cm2, cm3, cm4, cm5 = st.columns(5)
            cm1.metric("CCL Referencia",   f"${ccl_ref:,.0f}" if ccl_ref else "—")
            cm2.metric("CCL Implícito prom.", f"${avg_impl:,.0f}")
            cm3.metric("🟢 Con descuento (< −2%)", n_desc,
                       help="CEDEARs cuyo CCL implícito está por debajo del CCL real — potencialmente baratos en ARS")
            cm4.metric("🟡 A la par (±2%)",        n_par)
            cm5.metric("🔴 Con prima (> +2%)",     n_prem,
                       help="CEDEARs cuyo CCL implícito supera el CCL real — caros en ARS")

            st.divider()

            # ── Filtro sector ──
            sectores_c = sorted(cedear_df["Sector"].unique().tolist())
            sel_sect   = st.multiselect("Sector", sectores_c, default=sectores_c, key="ced_sect")
            cedear_filt = cedear_df[cedear_df["Sector"].isin(sel_sect)] if sel_sect else cedear_df

            # ── Color prima/descuento ──
            def _color_prima(val):
                if val < -2:   return "color:#4ade80;font-weight:700"
                elif val > 2:  return "color:#f87171;font-weight:700"
                return "color:#fbbf24;font-weight:700"

            display_ced = ["Ticker","Nombre","Sector","Precio ARS $","Precio USD $",
                           "Ratio","CCL Implícito","CCL Referencia","Prima/Desc %"]
            styled_ced = (
                cedear_filt[display_ced].style
                .map(_color_prima, subset=["Prima/Desc %"])
                .format({
                    "Precio ARS $":   "${:,.2f}",
                    "Precio USD $":   "${:,.2f}",
                    "CCL Implícito":  "${:,.2f}",
                    "CCL Referencia": "${:,.2f}",
                    "Prima/Desc %":   "{:+.2f}%",
                })
            )
            st.dataframe(styled_ced, use_container_width=True, height=520)

            # ── Gráfico de barras horizontal ──
            st.markdown("#### Prima / Descuento vs CCL de referencia")
            sorted_c = cedear_filt.sort_values("Prima/Desc %")
            bar_cols  = ["#4ade80" if v < -2 else "#f87171" if v > 2 else "#fbbf24"
                         for v in sorted_c["Prima/Desc %"]]
            fig_ced = go.Figure(go.Bar(
                x=sorted_c["Prima/Desc %"],
                y=sorted_c["Ticker"],
                orientation="h",
                marker_color=bar_cols,
                text=[f"{v:+.1f}%" for v in sorted_c["Prima/Desc %"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Prima/Desc: %{x:+.2f}%<extra></extra>",
            ))
            fig_ced.add_vline(x=0,  line_color="rgba(255,255,255,0.3)", line_width=1)
            fig_ced.add_vline(x=2,  line_dash="dot", line_color="#f87171", opacity=0.5)
            fig_ced.add_vline(x=-2, line_dash="dot", line_color="#4ade80", opacity=0.5)
            fig_ced.update_layout(
                template="plotly_dark", height=max(400, len(sorted_c) * 26),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0e1117",
                font=dict(color="#cbd5e1", size=11),
                margin=dict(l=10, r=60, t=20, b=20),
                xaxis=dict(ticksuffix="%", gridcolor="rgba(255,255,255,0.04)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            )
            st.plotly_chart(fig_ced, use_container_width=True)

            csv_ced = cedear_filt[display_ced].to_csv(index=False).encode("utf-8")
            st.download_button("📥 Exportar CEDEARs (CSV)", csv_ced,
                               "cedears_ccl.csv", "text/csv")

    # ─────────────────────────────────────────────────────────────────────
    # TAB 7 — CORRELACIÓN
    # ─────────────────────────────────────────────────────────────────────
    with tab7:
        st.subheader("🔗 Correlación entre papeles")
        st.caption("Correlación de retornos diarios. Verde = alta correlación positiva · Rojo = correlación negativa · Centro = sin relación.")

        col_opt1, col_opt2 = st.columns([2, 2])
        with col_opt1:
            corr_panel = st.multiselect(
                "Panel a incluir", ["Líder", "General"],
                default=["Líder"], key="corr_panel"
            )
        with col_opt2:
            corr_min   = st.slider("Mínimo de ruedas con datos", 20, 60, 30, 5, key="corr_min")

        # Filtrar data por panel
        corr_data = {
            k: v for k, v in data.items()
            if TICKERS.get(k, ("","","?"))[2] in corr_panel
        }

        if len(corr_data) < 2:
            st.info("Necesitás al menos 2 tickers para calcular correlación. Ampliá el panel.")
        else:
            with st.spinner("Calculando matriz de correlación…"):
                fig_corr = build_correlation_heatmap(corr_data, min_periods=corr_min)

            if not fig_corr.data:
                st.warning("Sin suficientes datos comunes. Reducí el mínimo de ruedas.")
            else:
                st.plotly_chart(fig_corr, use_container_width=True)

                # ── Pares más correlacionados / menos correlacionados ──
                ret_map = {}
                for ticker, df_c in corr_data.items():
                    sym = ticker.replace(".BA", "")
                    try:
                        r = df_c["Close"].pct_change().dropna()
                        if len(r) >= corr_min:
                            ret_map[sym] = r
                    except Exception:
                        continue

                if len(ret_map) >= 2:
                    ret_df2  = pd.DataFrame(ret_map).dropna(how="all")
                    corr_m   = ret_df2.corr()
                    pairs = []
                    cols_c = corr_m.columns.tolist()
                    for i in range(len(cols_c)):
                        for j in range(i+1, len(cols_c)):
                            pairs.append({
                                "Par":          f"{cols_c[i]} / {cols_c[j]}",
                                "Correlación":  round(corr_m.iloc[i, j], 3),
                            })
                    pairs_df = pd.DataFrame(pairs).sort_values("Correlación", ascending=False)

                    cp1, cp2 = st.columns(2)
                    with cp1:
                        st.markdown("##### 🔴 Pares más correlacionados (mayor riesgo de concentración)")
                        top_corr = pairs_df.head(8).style.format({"Correlación": "{:.3f}"})
                        st.dataframe(top_corr, use_container_width=True, hide_index=True)
                    with cp2:
                        st.markdown("##### 🟢 Pares menos correlacionados (mayor diversificación)")
                        low_corr = pairs_df.tail(8).style.format({"Correlación": "{:.3f}"})
                        st.dataframe(low_corr, use_container_width=True, hide_index=True)

                    csv_corr = pairs_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Exportar pares de correlación (CSV)",
                                       csv_corr, "correlacion.csv", "text/csv")

    # ─────────────────────────────────────────────────────────────────────
    # TAB 8 — HISTORIAL DE SEÑALES
    # ─────────────────────────────────────────────────────────────────────
    with tab8:
        st.subheader("📜 Historial de Señales")
        st.caption("Registro automático de cada estado del screener durante la sesión. Se guarda en memoria; exportá el CSV para conservarlo entre sesiones.")

        hist = st.session_state.get(HIST_KEY, [])

        if not hist:
            st.info("El historial se genera automáticamente al cargar la app. Volvé a esta tab después de algunas actualizaciones.")
        else:
            hist_df = pd.DataFrame(hist)

            # ── Métricas ──
            n_snaps  = hist_df["Timestamp"].nunique()
            n_ticks  = hist_df["Ticker"].nunique()
            last_ts  = hist_df["Timestamp"].max()

            hm1, hm2, hm3 = st.columns(3)
            hm1.metric("📸 Snapshots guardados", n_snaps)
            hm2.metric("📊 Tickers registrados", n_ticks)
            hm3.metric("🕐 Último registro",     last_ts)

            st.divider()

            # ── Filtros ──
            hf1, hf2 = st.columns([2, 2])
            with hf1:
                hist_ticker = st.selectbox("Ver evolución de ticker",
                    ["— Todos —"] + sorted(hist_df["Ticker"].unique().tolist()),
                    key="hist_ticker_sel")
            with hf2:
                hist_señal = st.multiselect("Filtrar por señal",
                    hist_df["Señal"].unique().tolist(),
                    default=list(hist_df["Señal"].unique()),
                    key="hist_señal_sel")

            hist_filt = hist_df.copy()
            if hist_señal:
                hist_filt = hist_filt[hist_filt["Señal"].isin(hist_señal)]

            # ── Gráfico de score histórico por ticker ──
            if hist_ticker != "— Todos —" and hist_ticker in hist_df["Ticker"].values:
                st.plotly_chart(build_history_chart(hist_df, hist_ticker),
                                use_container_width=True)
                hist_filt = hist_filt[hist_filt["Ticker"] == hist_ticker]

            # ── Tabla ──
            def _color_hist_señal(val):
                c, bg = REC_COLORS.get(val, ("#aaa","#222"))
                return f"background-color:{bg};color:{c};font-weight:700"

            styled_hist = (
                hist_filt.style
                .map(_color_hist_señal, subset=["Señal"])
                .map(_color_score,      subset=["Score"])
                .map(lambda v: "color:#4ade80" if v >= 0 else "color:#f87171",
                     subset=["Var %"])
                .format({
                    "Score":    "{:+d}",
                    "Precio $": "${:,.2f}",
                    "Var %":    "{:+.2f}%",
                    "RSI":      "{:.1f}",
                    "RVOL":     "{:.2f}x",
                })
            )
            st.dataframe(styled_hist, use_container_width=True, height=460)

            # ── Heatmap de señales por ticker a lo largo del tiempo ──
            if n_snaps > 1 and n_ticks > 1:
                st.markdown("#### Evolución de scores por ticker")
                pivot = hist_df.pivot_table(
                    index="Ticker", columns="Timestamp",
                    values="Score", aggfunc="last"
                ).fillna(0)
                fig_heat = go.Figure(go.Heatmap(
                    z=pivot.values, x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    colorscale=[
                        [0.0, "#ff4b6b"],[0.3, "#f87171"],
                        [0.5, "#1e2235"],[0.7, "#4ade80"],[1.0, "#00d4aa"]
                    ],
                    zmin=-8, zmax=8,
                    text=pivot.values.astype(int).astype(str),
                    texttemplate="%{text}",
                    hovertemplate="<b>%{y}</b><br>%{x}<br>Score: %{z}<extra></extra>",
                ))
                fig_heat.update_layout(
                    template="plotly_dark",
                    height=max(300, len(pivot) * 22),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0e1117",
                    font=dict(color="#cbd5e1", size=10),
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            # ── Export ──
            csv_hist = hist_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar historial completo (CSV)",
                csv_hist,
                f"historial_señales_{datetime.now(timezone(timedelta(hours=-3))).strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=False,
            )

            if st.button("🗑️ Limpiar historial de esta sesión", type="secondary"):
                st.session_state[HIST_KEY] = []
                st.rerun()


    # ─────────────────────────────────────────────────────────────────────
    # TAB 9 — COMPARADOR
    # ─────────────────────────────────────────────────────────────────────
    with tab9:
        st.subheader("⚖️ Comparador de Papeles")
        st.caption("Retornos normalizados (base 100) — compará performance relativa entre tickers y vs el Merval.")

        all_syms   = sorted([t.replace(".BA","") for t in data.keys()])
        default_sel = all_syms[:3] if len(all_syms) >= 3 else all_syms

        cp1, cp2 = st.columns([3, 1])
        with cp1:
            comp_tickers = st.multiselect(
                "Seleccioná hasta 5 tickers para comparar",
                all_syms,
                default=default_sel,
                max_selections=5,
                key="comp_tickers",
            )
        with cp2:
            show_merval = st.checkbox("Incluir Merval", value=True, key="comp_merval")
            comp_period = st.selectbox("Período", ["3mo","6mo","1y","2y"], index=1,
                                       format_func=lambda x: {"3mo":"3m","6mo":"6m","1y":"1a","2y":"2a"}[x],
                                       key="comp_period")

        if not comp_tickers:
            st.info("Seleccioná al menos un ticker.")
        else:
            # Descargar Merval si se pidió
            merval_df = None
            if show_merval:
                try:
                    raw_m = yf.download("^MERV", period=comp_period,
                                        auto_adjust=True, progress=False)
                    if not raw_m.empty:
                        merval_df = raw_m
                except Exception:
                    pass

            # Re-fetch si el período difiere del cargado en sidebar
            if comp_period != period:
                with st.spinner("Descargando datos del período seleccionado…"):
                    extra_tickers = [t+".BA" for t in comp_tickers]
                    raw_comp = yf.download(extra_tickers, period=comp_period,
                                           auto_adjust=True, progress=False,
                                           group_by="ticker", threads=True)
                    comp_data = {}
                    for sym in comp_tickers:
                        ticker_ba = sym + ".BA"
                        try:
                            if len(extra_tickers) == 1:
                                comp_data[ticker_ba] = raw_comp.dropna(how="all")
                            else:
                                comp_data[ticker_ba] = raw_comp[ticker_ba].dropna(how="all")
                        except Exception:
                            pass
            else:
                comp_data = data

            # ── Gráfico retornos normalizados ──
            fig_comp = build_comparison_chart(comp_data, comp_tickers, merval_df)
            st.plotly_chart(fig_comp, use_container_width=True)

            # ── Drawdown ──
            st.markdown("#### Drawdown desde máximo")
            fig_dd = build_drawdown_chart(comp_data, comp_tickers)
            st.plotly_chart(fig_dd, use_container_width=True)

            # ── Tabla comparativa de métricas ──
            st.markdown("#### Métricas comparativas")
            comp_rows = []
            for sym in comp_tickers:
                ticker_ba = sym + ".BA"
                df_c = comp_data.get(ticker_ba)
                if df_c is None or len(df_c) < 5:
                    continue
                close_c = df_c["Close"].dropna()
                roll_mx = close_c.cummax()
                dd_s    = (close_c - roll_mx) / roll_mx * 100
                daily_r = close_c.pct_change().dropna()
                sharpe  = round(daily_r.mean() / daily_r.std() * (252**0.5), 2) if daily_r.std() > 0 else 0
                nombre, sector, panel = TICKERS.get(ticker_ba, (sym,"—","—"))
                comp_rows.append({
                    "Ticker":       sym,
                    "Panel":        panel,
                    "Sector":       sector,
                    "Retorno %":    round(float(close_c.iloc[-1]/close_c.iloc[0]-1)*100, 2),
                    "Máx DD %":     round(float(dd_s.min()), 2),
                    "Sharpe":       sharpe,
                    "Vol. anual %": round(float(daily_r.std()) * (252**0.5) * 100, 2),
                    "Precio":       round(float(close_c.iloc[-1]), 2),
                })
            if comp_rows:
                comp_met_df = pd.DataFrame(comp_rows).set_index("Ticker")

                def _cr(v): return "color:#4ade80;font-weight:700" if v>0 else "color:#f87171;font-weight:700"
                def _dd(v): return "color:#f87171;font-weight:700" if v<-15 else "color:#fbbf24" if v<-5 else "color:#4ade80"

                st.dataframe(
                    comp_met_df.style
                    .map(_cr, subset=["Retorno %"])
                    .map(_dd, subset=["Máx DD %"])
                    .format({"Retorno %":"{:+.2f}%","Máx DD %":"{:.2f}%",
                             "Vol. anual %":"{:.2f}%","Precio":"${:,.2f}","Sharpe":"{:.2f}"}),
                    use_container_width=True,
                )

    # ─────────────────────────────────────────────────────────────────────
    # TAB 10 — WATCHLIST
    # ─────────────────────────────────────────────────────────────────────
    with tab10:
        st.subheader("📋 Watchlist Personalizada")
        st.caption("Tu lista de seguimiento persistente. Se guarda en watchlist.json en el repositorio.")

        wl = st.session_state['watchlist']
        all_syms_wl = sorted([t.replace(".BA","") for t in TICKERS.keys()])

        # ── Agregar ticker ──
        wa1, wa2 = st.columns([3, 1])
        with wa1:
            add_ticker = st.selectbox("Agregar ticker a la watchlist",
                                      ["— Seleccioná —"] + [s for s in all_syms_wl if s not in wl],
                                      key="wl_add")
        with wa2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Agregar", use_container_width=True) and add_ticker != "— Seleccioná —":
                if add_ticker not in wl:
                    wl.append(add_ticker)
                    save_watchlist(wl)
                    st.session_state['watchlist'] = wl
                    st.rerun()

        st.divider()

        if not wl:
            st.info("Tu watchlist está vacía. Agregá tickers desde el menú de arriba.")
        else:
            st.markdown(f"**{len(wl)} tickers en seguimiento**")

            # ── Tabla de watchlist con datos en vivo ──
            wl_rows = []
            for sym in wl:
                ticker_ba = sym + ".BA"
                df_wl = data.get(ticker_ba)
                if df_wl is not None and len(df_wl) > 1:
                    d_info = detail_store.get(sym, {})
                    price  = float(df_wl["Close"].iloc[-1])
                    price_p= float(df_wl["Close"].iloc[-2])
                    var    = (price/price_p-1)*100
                    nombre, sector, panel = TICKERS.get(ticker_ba,(sym,"—","—"))
                    wl_rows.append({
                        "Ticker":    sym,
                        "Nombre":    nombre,
                        "Panel":     panel,
                        "Sector":    sector,
                        "Precio $":  round(price,2),
                        "Var %":     round(var,2),
                        "Score":     d_info.get("score","—"),
                        "Señal":     d_info.get("rec","—"),
                        "RSI":       d_info.get("metrics",{}).get("rsi","—"),
                        "RVOL":      d_info.get("metrics",{}).get("rvol","—"),
                    })
                else:
                    wl_rows.append({"Ticker":sym,"Nombre":"—","Panel":"—","Sector":"—",
                                    "Precio $":"—","Var %":"—","Score":"—",
                                    "Señal":"—","RSI":"—","RVOL":"—"})

            if wl_rows:
                wl_df = pd.DataFrame(wl_rows)

                def _wl_var(v):
                    try: return "color:#4ade80;font-weight:700" if float(v)>0 else "color:#f87171;font-weight:700"
                    except: return ""
                def _wl_señal(v):
                    c,bg = REC_COLORS.get(v,("#aaa","#222"))
                    return f"background-color:{bg};color:{c};font-weight:700"

                num_cols = [c for c in ["Precio $","Var %","Score","RSI","RVOL"] if wl_df[c].apply(lambda x: isinstance(x,(int,float))).all()]
                fmt_dict = {}
                if "Precio $" in num_cols: fmt_dict["Precio $"] = "${:,.2f}"
                if "Var %"    in num_cols: fmt_dict["Var %"]    = "{:+.2f}%"
                if "Score"    in num_cols: fmt_dict["Score"]    = "{:+d}"
                if "RVOL"     in num_cols: fmt_dict["RVOL"]     = "{:.2f}x"

                styled_wl = wl_df.style
                if "Señal" in wl_df.columns:
                    styled_wl = styled_wl.map(_wl_señal, subset=["Señal"])
                if fmt_dict:
                    styled_wl = styled_wl.format(fmt_dict, na_rep="—")

                st.dataframe(styled_wl, use_container_width=True, height=400)

            # ── Gestión de watchlist ──
            st.markdown("#### Gestionar watchlist")
            wg1, wg2 = st.columns([3,1])
            with wg1:
                del_ticker = st.selectbox("Eliminar ticker", ["— Seleccioná —"] + wl, key="wl_del")
            with wg2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Eliminar", use_container_width=True) and del_ticker != "— Seleccioná —":
                    wl.remove(del_ticker)
                    save_watchlist(wl)
                    st.session_state['watchlist'] = wl
                    st.rerun()

            if st.button("🗑️ Limpiar toda la watchlist", type="secondary"):
                st.session_state['watchlist'] = []
                save_watchlist([])
                st.rerun()

            csv_wl = pd.DataFrame(wl_rows).to_csv(index=False).encode("utf-8")
            st.download_button("📥 Exportar watchlist (CSV)", csv_wl,
                               "watchlist.csv", "text/csv")

    # ─────────────────────────────────────────────────────────────────────
    # TAB 11 — SIZING
    # ─────────────────────────────────────────────────────────────────────
    with tab11:
        st.subheader("🎯 Simulador de Posición & Sizing")
        st.caption("Calculá el tamaño óptimo de cada operación basado en tu capital y riesgo por trade.")

        sz1, sz2 = st.columns([1, 1])
        with sz1:
            st.markdown("#### 💼 Parámetros de cuenta")
            sz_capital    = st.number_input("Capital disponible (ARS $)", min_value=1000,
                                            value=1_000_000, step=50_000, format="%d")
            sz_risk_pct   = st.slider("Riesgo máximo por operación (%)", 0.5, 5.0, 1.0, 0.25,
                                      help="% del capital que estás dispuesto a perder si salta el stop")
            sz_commission = st.slider("Comisión estimada (%)", 0.0, 1.5, 0.6, 0.1,
                                      help="Comisión de compra (IOL ~0.6%, otros brokers varían)")
            sz_atr_mult   = st.slider("Multiplicador ATR para stop", 1.0, 4.0, 2.0, 0.5,
                                      help="Stop Loss = Precio − (ATR × multiplicador)")

        with sz2:
            st.markdown("#### 📈 Seleccioná el papel")
            sz_ticker = st.selectbox(
                "Ticker",
                list(detail_store.keys()),
                format_func=lambda x: f"{x}  —  {TICKERS.get(x+'.BA',('?','?','?'))[0]}",
                key="sz_ticker",
            )

            if sz_ticker and sz_ticker in detail_store:
                d_sz    = detail_store[sz_ticker]
                price_sz= float(d_sz["df"]["Close"].iloc[-1])
                atr_sz  = d_sz["metrics"]["atr"]
                nombre_sz, sector_sz, panel_sz = TICKERS.get(sz_ticker+".BA",("?","?","?"))

                st.markdown(f"""
                <div style='background:#1a1d27;border:1px solid #2d3148;border-radius:8px;padding:12px;margin-top:8px'>
                    <div style='color:#94a3b8;font-size:11px'>Datos actuales de {sz_ticker}</div>
                    <div style='margin-top:6px;display:flex;gap:24px'>
                        <span><span style='color:#64748b;font-size:12px'>Precio </span>
                              <span style='color:#e2e8f0;font-weight:700'>${price_sz:,.2f}</span></span>
                        <span><span style='color:#64748b;font-size:12px'>ATR(14) </span>
                              <span style='color:#e2e8f0;font-weight:700'>${atr_sz:,.2f}</span></span>
                        <span><span style='color:#64748b;font-size:12px'>ATR% </span>
                              <span style='color:#e2e8f0;font-weight:700'>{atr_sz/price_sz*100:.1f}%</span></span>
                        <span><span style='color:#64748b;font-size:12px'>Señal </span>
                              <span style='color:#00d4aa;font-weight:700'>{d_sz["rec"]}</span></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        if sz_ticker and sz_ticker in detail_store:
            pos = calc_position(
                capital=sz_capital,
                risk_pct=sz_risk_pct,
                price=price_sz,
                atr=atr_sz,
                atr_mult=sz_atr_mult,
                commission_pct=sz_commission/100,
            )

            # ── Métricas principales ──
            sm1,sm2,sm3,sm4,sm5,sm6 = st.columns(6)
            sm1.metric("📦 Acciones a comprar",  f"{pos['shares']:,}")
            sm2.metric("💰 Capital a invertir",  f"${pos['net_invest']:,.0f}",
                       f"{pos['pct_capital']:.1f}% del capital")
            sm3.metric("🛑 Stop Loss",            f"${pos['stop']:,.2f}",
                       f"-{pos['stop_dist_pct']:.1f}%")
            sm4.metric("💸 Riesgo máximo",        f"${pos['loss_sl']:,.0f}",
                       f"{sz_risk_pct}% del capital")
            sm5.metric("🏦 Comisión estimada",    f"${pos['commission']:,.0f}")
            sm6.metric("📊 Exposición",           f"{pos['pct_capital']:.1f}%",
                       help="% del capital total comprometido en esta posición")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Tabla de targets ──
            st.markdown("#### 🎯 Niveles de salida y ratio Riesgo/Recompensa")
            rr_data = pd.DataFrame([
                {"Nivel":"🛑 Stop Loss",       "Precio":f"${pos['stop']:,.2f}",
                 "Variación":f"-{pos['stop_dist_pct']:.1f}%",
                 "P&L estimado":f"-${pos['loss_sl']:,.0f}", "R/R":"—"},
                {"Nivel":"🟡 Entrada",          "Precio":f"${pos['price']:,.2f}",
                 "Variación":"—","P&L estimado":"—","R/R":"—"},
                {"Nivel":"🎯 Target 1 (1:1)",   "Precio":f"${pos['target_1']:,.2f}",
                 "Variación":f"+{pos['stop_dist_pct']:.1f}%",
                 "P&L estimado":f"+${pos['gain_t1']:,.0f}","R/R":f"{pos['rr_1']:.1f}"},
                {"Nivel":"🎯 Target 2 (1:2)",   "Precio":f"${pos['target_2']:,.2f}",
                 "Variación":f"+{pos['stop_dist_pct']*2:.1f}%",
                 "P&L estimado":f"+${pos['gain_t2']:,.0f}","R/R":f"{pos['rr_2']:.1f}"},
                {"Nivel":"🚀 Target 3 (1:3)",   "Precio":f"${pos['target_3']:,.2f}",
                 "Variación":f"+{pos['stop_dist_pct']*3:.1f}%",
                 "P&L estimado":f"+${pos['gain_t3']:,.0f}","R/R":f"{pos['rr_3']:.1f}"},
            ])
            st.table(rr_data.set_index("Nivel"))

            # ── Gráfico de niveles ──
            fig_sz = go.Figure()
            price_range = [pos["stop"]*0.98, pos["target_3"]*1.02]
            for lvl, color, label in [
                (pos["stop"],     "#f87171", f"Stop ${pos['stop']:,.0f}"),
                (pos["price"],    "#fbbf24", f"Entrada ${pos['price']:,.0f}"),
                (pos["target_1"], "#4ade80", f"T1 ${pos['target_1']:,.0f}"),
                (pos["target_2"], "#00d4aa", f"T2 ${pos['target_2']:,.0f}"),
                (pos["target_3"], "#a78bfa", f"T3 ${pos['target_3']:,.0f}"),
            ]:
                fig_sz.add_shape(type="line", x0=0, x1=1, y0=lvl, y1=lvl,
                                 line=dict(color=color, width=2, dash="dash"))
                fig_sz.add_annotation(x=1.01, y=lvl, text=label,
                                      showarrow=False, xref="paper",
                                      font=dict(color=color, size=11), xanchor="left")

            # Zona de riesgo (rojo) y ganancia (verde)
            fig_sz.add_shape(type="rect", x0=0, x1=1, y0=pos["stop"], y1=pos["price"],
                             fillcolor="rgba(248,113,113,0.08)", line_width=0)
            fig_sz.add_shape(type="rect", x0=0, x1=1, y0=pos["price"], y1=pos["target_2"],
                             fillcolor="rgba(74,222,128,0.06)", line_width=0)

            fig_sz.update_layout(
                template="plotly_dark", height=320,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0e1117",
                margin=dict(l=10, r=120, t=10, b=10),
                xaxis=dict(visible=False),
                yaxis=dict(tickprefix="$", gridcolor="rgba(255,255,255,0.04)",
                           range=price_range),
                showlegend=False,
            )
            st.plotly_chart(fig_sz, use_container_width=True)

            # ── Resumen ejecutable ──
            st.markdown("#### 📋 Orden de compra sugerida")
            orden_txt = (
                f"Ticker:        {sz_ticker}\n"
                f"Accion:        COMPRA\n"
                f"Cantidad:      {pos['shares']:,} acciones\n"
                f"Precio limite: ${pos['price']:,.2f}\n"
                f"Stop Loss:     ${pos['stop']:,.2f}  (-{pos['stop_dist_pct']:.1f}%)\n"
                f"Target 1:      ${pos['target_1']:,.2f}  (R/R {pos['rr_1']:.1f})\n"
                f"Target 2:      ${pos['target_2']:,.2f}  (R/R {pos['rr_2']:.1f})\n"
                f"Capital:       ${pos['net_invest']:,.0f}  ({pos['pct_capital']:.1f}% del total)\n"
                f"Riesgo max.:   ${pos['loss_sl']:,.0f}  ({sz_risk_pct}% del capital)"
            )
            st.code(orden_txt, language="text")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()

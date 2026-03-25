# 🇦🇷 BCBA Technical Analyzer — Swing Trading Dashboard
Dashboard de análisis técnico para el mercado de capitales argentino (BCBA).  
Panel Líder + Panel General | Fuente de datos: Yahoo Finance (sin API key)

---

## 🧰 Indicadores implementados

| Indicador | Parámetros | Uso en swing trading |
|-----------|-----------|----------------------|
| RSI | 14 períodos | Sobrecompra/venta, momentum |
| MACD | 12/26/9 | Dirección, cruces, histograma |
| Bollinger Bands | 20/2 | Squeeze, rango, reversiones |
| Stochastico | 14/3/3 | Cruces en zonas extremas |
| ATR | 14 períodos | Stop loss y targets dinámicos |
| RVOL | Rel. a SMA20 vol | Confirmar rupturas |
| SMA 20/50 | — | Tendencia general |
| Soporte/Resistencia | Pivotes automáticos | Niveles clave |

---

## 📊 Scoring

El score va de **-10 a +10** (aproximado, puede ir algo más allá).

| Score | Recomendación |
|-------|---------------|
| ≥ 6   | COMPRA FUERTE |
| 3 a 5 | COMPRA |
| -2 a 2| NEUTRAL |
| -5 a -3 | VENTA |
| ≤ -6  | VENTA FUERTE |

---


## ⚠️ Disclaimer

Herramienta de análisis técnico para uso personal e informativo.  
No constituye asesoramiento financiero ni recomendación de inversión.  
Operar en mercados implica riesgo de pérdida de capital.

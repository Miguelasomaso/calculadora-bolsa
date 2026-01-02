import streamlit as st
import yfinance as yf
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Stocks Value", page_icon="💎", layout="wide")

# Truco para el nombre en Android
st.markdown(f"""
    <head>
        <title>Stocks Value</title>
        <link rel="manifest" href="manifest.json">
    </head>
""", unsafe_allow_html=True)

# --- MEMORIA DE LA APP ---
if 'data' not in st.session_state:
    st.session_state.data = {
        'price': 0.0, 'rev': 0.0, 'shares': 0.0, 
        'pe': 0.0, 'margin': 0.0, 'net_income': 0.0,
        'ticker': ""
    }

st.title("Stocks Value 💎")
st.caption("Calculadora de Valor Intrínseco - Rumbo a los 50")

# =========================================
# SECCIÓN 1: DATOS ACTUALES (BUSCADOR REPARADO)
# =========================================
st.header("1. Datos Actuales (Yahoo Finance)")

col_ticker, col_btn = st.columns([3, 1])
with col_ticker:
    ticker_input = st.text_input("Introduce el Ticker (ej: META, V, MSFT):", value=st.session_state.data['ticker']).upper()
with col_btn:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 Buscar Datos")

if search_btn and ticker_input:
    try:
        with st.spinner(f"Conectando con Yahoo para {ticker_input}..."):
            # PLAN B: Usar un buscador manual de yfinance que es más resistente
            stock = yf.Ticker(ticker_input)
            
            # Forzamos la obtención de datos específicos
            info = stock.info
            
            if not info or 'symbol' not in str(info).lower():
                st.error("Ticker no reconocido o bloqueo de Yahoo. Introduce los datos manualmente.")
            else:
                st.session_state.data['price'] = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
                st.session_state.data['rev'] = (info.get('totalRevenue', 0.0)) / 1_000_000
                st.session_state.data['shares'] = (info.get('sharesOutstanding', 0.0)) / 1_000_000
                st.session_state.data['margin'] = (info.get('profitMargins', 0.0)) * 100
                st.session_state.data['net_income'] = (info.get('netIncomeToCommon', 0.0)) / 1_000_000
                st.session_state.data['pe'] = info.get('forwardPE') or info.get('trailingPE') or 0.0
                st.session_state.data['ticker'] = ticker_input
                st.success(f"Datos de {ticker_input} cargados.")
    except Exception as e:
        st.warning("Yahoo ha bloqueado la conexión temporalmente. Por favor, rellena los datos a mano abajo.")

# Formulario de entrada
col_d1, col_d2, col_d3 = st.columns(3)
col_d4, col_d5, col_d6 = st.columns(3)

with col_d1:
    cp_input = st.number_input("Precio Acción Actual ($)", value=float(st.session_state.data['price']), format="%.2f")
with col_d2:
    cr_input_mil = st.number_input("Ingresos Totales (Millones $)", value=float(st.session_state.data['rev']), format="%.2f")
with col_d3:
    so_input_mil = st.number_input("Acciones en Circulación (Millones)", value=float(st.session_state.data['shares']), format="%.2f")
with col_d4:
    pe_estimado = st.number_input("P/E Estimado (NTM)", value=float(st.session_state.data['pe']), format="%.2f")
with col_d5:
    pm_input = st.number_input("Margen de Beneficio Actual (%)", value=float(st.session_state.data['margin']), format="%.2f")
with col_d6:
    ni_input_mil = st.number_input("Ingresos Netos Actuales (Millones $)", value=float(st.session_state.data['net_income']), format="%.2f")

st.markdown("---")
# =========================================
# SECCIÓN 2: ESCENARIOS (CON TUS ICONOS)
# =========================================
st.header("2. Tus Escenarios")

col_years, col_return = st.columns(2)
with col_years:
    projection_years = st.slider("Años de proyección", 1, 15, 5)
with col_return:
    desired_return = st.number_input("Rentabilidad Anual Deseada (%)", value=15.0, step=0.5)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento Ingresos %", value=d_rev, format="%.2f", key=f"r_{title}")
        marg = st.number_input(f"Margen Futuro %", value=d_marg, format="%.2f", key=f"m_{title}")
        pe = st.number_input(f"P/E Futuro (NTM)", value=d_pe, format="%.2f", key=f"p_{title}")
        sh = st.number_input(f"Cambio Acciones %", value=d_sh, format="%.2f", key=f"s_{title}")
        return rev, marg, pe, sh

bear_col, base_col, bull_col = st.columns(3)
bear = create_case(bear_col, "Bear Case", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(base_col, "Base Case", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(bull_col, "Bull Case", "🚀", 15.0, 20.0, 30.0, -1.0)

def calc_valuation(inputs):
    rg, fm, fpe, sc = inputs
    f_rev = cr_input_mil * ((1 + rg/100)**projection_years)
    f_ni = f_rev * (fm/100)
    f_mc = f_ni * fpe
    f_sh = so_input_mil * ((1 + sc/100)**projection_years)
    pt = f_mc / f_sh if f_sh > 0 else 0
    cagr = (((pt / cp_input)**(1/projection_years)) - 1) * 100 if cp_input > 0 and pt > 0 else 0
    buy = pt / ((1 + desired_return/100)**projection_years)
    return pt, cagr, buy

# =========================================
# 3. RESULTADOS (TARJETAS VISUALES CORREGIDAS)
# =========================================
if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    pt_bear, c_bear, b_bear = calc_valuation(bear)
    pt_base, c_base, b_base = calc_valuation(base)
    pt_bull, c_bull, b_bull = calc_valuation(bull)
    
    st.write("")
    c_oso, c_base, c_toro = st.columns(3)

    with c_oso:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🐻 Bear Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_bear:.2f}</b></p><p>CAGR: <b>{c_bear:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_bear:.2f}</h3></div>', unsafe_allow_html=True)

    with c_base:
        color = "green" if cp_input <= b_base else "#d32f2f"
        st.markdown(f'<div style="border:2px solid {color}; border-radius:12px; padding:20px; margin-bottom:20px; background-color:#f0fdf4;"><h2 style="color:#1b5e20;">📊 Base Case</h2><p>Precio Futuro ({projection_years}a):<br><b style="font-size:24px;">${pt_base:.2f}</b></p><p>CAGR: <b>{c_base:.2f}%</b></p><hr><p style="font-size:14px; font-weight:bold;">COMPRA HOY:</p><h1 style="color:{color};">${b_base:.2f}</h1></div>', unsafe_allow_html=True)

    with c_toro:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🚀 Bull Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_bull:.2f}</b></p><p>CAGR: <b>{c_bull:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_bull:.2f}</h3></div>', unsafe_allow_html=True)


import streamlit as st
import yfinance as yf

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Stocks Value", page_icon="💎", layout="wide")

# Truco para forzar el nombre en Android
st.markdown(f"""
    <head>
        <title>Stocks Value</title>
        <link rel="manifest" href="manifest.json">
    </head>
""", unsafe_allow_html=True)

# --- MEMORIA DE LA APP (Session State) ---
if 'data' not in st.session_state:
    st.session_state.data = {
        'price': 0.0, 'rev': 0.0, 'shares': 0.0, 
        'pe': 0.0, 'margin': 0.0, 'net_income': 0.0
    }

st.title("Stocks Value 💎")
st.caption("Calculadora de Valor Intrínseco - Rumbo a los 50")

# =========================================
# SECCIÓN 1: DATOS ACTUALES
# =========================================
st.header("1. Datos Actuales (Yahoo Finance)")

col_ticker, col_btn = st.columns([3, 1])
with col_ticker:
    ticker_input = st.text_input("Introduce el Ticker (ej: META, V, MSFT):").upper()
with col_btn:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 Buscar Datos")

if search_btn and ticker_input:
    try:
        with st.spinner(f"Obteniendo datos de {ticker_input}..."):
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            f_pe = info.get('forwardPE')
            if f_pe is None:
                f_pe = info.get('trailingPE', 0.0)
            
            st.session_state.data['price'] = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            st.session_state.data['rev'] = (info.get('totalRevenue', 0.0)) / 1_000_000
            st.session_state.data['shares'] = (info.get('sharesOutstanding', 0.0)) / 1_000_000
            st.session_state.data['pe'] = f_pe
            st.session_state.data['margin'] = (info.get('profitMargins', 0.0)) * 100
            st.session_state.data['net_income'] = (info.get('netIncomeToCommon', 0.0)) / 1_000_000
        st.success(f"Datos cargados. P/E usado: {f_pe:.2f}")
    except:
        st.error("Error al conectar. Introduce los datos manualmente.")

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
# SECCIÓN 2: PROYECCIÓN Y OBJETIVO
# =========================================
st.header("2. Tus Escenarios")

col_years, col_return = st.columns(2)
with col_years:
    projection_years = st.slider("Años de proyección", 1, 15, 5)
with col_return:
    desired_return = st.number_input("Rentabilidad Anual Deseada (%)", value=15.0, step=0.5)

bear_col, base_col, bull_col = st.columns(3)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento Ingresos %", value=d_rev, format="%.2f", key=f"r_{title}")
        marg = st.number_input(f"Margen Futuro %", value=d_marg, format="%.2f", key=f"m_{title}")
        pe = st.number_input(f"P/E Futuro (NTM)", value=d_pe, format="%.2f", key=f"p_{title}")
        sh = st.number_input(f"Cambio Acciones %", value=d_sh, format="%.2f", key=f"s_{title}")
        return rev, marg, pe, sh

# Inputs de los escenarios CON LOS NOMBRES NUEVOS
bear = create_case(bear_col, "Bear Case", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(base_col, "Base Case", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(bull_col, "Bull Case", "🚀", 15.0, 20.0, 30.0, -1.0)

def calc_valuation(inputs):
    rg, fm, fpe, sc = inputs
    future_rev = cr_input_mil * ((1 + rg/100)**projection_years)
    future_ni = future_rev * (fm/100)
    future_market_cap = future_ni * fpe
    future_shares = so_input_mil * ((1 + sc/100)**projection_years)
    
    price_target = future_market_cap / future_shares if future_shares > 0 else 0
    
    # CAGR calculation
    if cp_input > 0 and price_target > 0:
        cagr = (((price_target / cp_input)**(1/projection_years)) - 1) * 100
    else:
        cagr = 0
    # Required Buy Price
    required_price = price_target / ((1 + desired_return/100)**projection_years)
    
    return price_target, cagr, required_price

# =========================================
# 3. RESULTADOS (TARJETAS VISUALES)
# =========================================

if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    
    # 1. Realizar cálculos
    pt_bear, cagr_bear, buy_bear = calc_valuation(bear)
    pt_base, cagr_base, buy_base = calc_valuation(base)
    pt_bull, cagr_bull, buy_bull = calc_valuation(bull)
    
    st.write("") # Espacio
    
    # Columnas para mostrar resultados
    c_oso, c_base, c_toro = st.columns(3)

    # --- TARJETA BEAR CASE (OSO) ---
    with c_oso:
        st.markdown(f"""
        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
            <h3 style="margin-top:0; color: #555;">🐻 Bear Case</h3>
            <p>Precio Futuro ({projection_years}a):<br><b style="font-size: 18px">${pt_bear:.2f}</b></p>
            <p>CAGR Esperado: <b>{cagr_bear:.2f}%</b></p>
            <hr>
            <p style="font-size:12px">Precio máx. compra hoy:</p>
            <h3 style="color: #555;">${buy_bear:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

    # --- TARJETA BASE CASE (TU CASO) ---
    with c_base:
        # Lógica de color para el precio: Verde si está barata, Rojo si está cara
        color_precio = "green" if cp_input <= buy_base else "#d32f2f"
        mensaje_compra = "✅ OPORTUNIDAD" if cp_input <= buy_base else "⚠️ ESPERAR"
        
        st.markdown(f"""
        <div style="border: 2px solid {color_precio}; border-radius: 12px; padding: 20px; margin-bottom: 20px; background-color: #f0fdf4; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="margin-top:0; color: #1b5e20;">📊 Base Case</h2>
            <p style="font-size: 14px; color: #333;">(Tu múltiplo de 25)</p>
            <p>Precio Futuro ({projection_years}a):<br><b style="font-size: 24px; color: #000;">${pt_base:.2f}</b></p>
            <p>CAGR Esperado: <b>{cagr_base:.2f}%</b></p>
            <hr style="border-top: 1px solid #ccc;">
            <p style="font-size:14px; font-weight:bold;">PRECIO DE COMPRA HOY:</p>
            <h1 style="color: {color_precio}; margin:0;">${buy_base:.2f}</h1>
            <p style="color: {color_precio}; font-weight:bold; margin-top:5px;">{mensaje_compra}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- TARJETA BULL CASE (TORO) ---
    with c_toro:
        st.markdown(f"""
        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
            <h3 style="margin-top:0; color: #555;">🚀 Bull Case</h3>
            <p>Precio Futuro ({projection_years}a):<br><b style="font-size: 18px">${pt_bull:.2f}</b></p>
            <p>CAGR Esperado: <b>{cagr_bull:.2f}%</b></p>
            <hr>
            <p style="font-size:12px">Precio máx. compra hoy:</p>
            <h3 style="color: #555;">${buy_bull:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)








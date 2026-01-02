import streamlit as st
import yfinance as yf

import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Stocks Value", page_icon="📈", layout="wide")

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

st.title("Proyección de Valor y Precio de Entrada Ideal")
st.info("Priorizamos el Forward P/E (Estimado). Ajusta la 'Rentabilidad Deseada' para ver tu precio de compra.")

# =========================================
# SECCIÓN 1: DATOS ACTUALES
# =========================================
st.header("1. Datos Actuales y Estimaciones (NTM)")

col_ticker, col_btn = st.columns([3, 1])
with col_ticker:
    ticker_input = st.text_input("Introduce el Ticker (ej: V, MSFT, AMZN):").upper()
with col_btn:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 Buscar Datos")

if search_btn and ticker_input:
    try:
        with st.spinner(f"Obteniendo estimaciones para {ticker_input}..."):
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
st.header("2. Escenarios y Objetivo de Rentabilidad")

col_years, col_return = st.columns(2)
with col_years:
    projection_years = st.slider("Años de proyección", 1, 15, 5) # Subido a 15 por si quieres ver tu retiro a los 50 más de cerca
with col_return:
    desired_return = st.number_input("Rentabilidad Anual Deseada (%)", value=15.0, step=0.5)

bear_col, base_col, bull_col = st.columns(3)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento Ingresos % - {title}", value=d_rev, format="%.2f", key=f"r_{title}")
        marg = st.number_input(f"Margen Futuro % - {title}", value=d_marg, format="%.2f", key=f"m_{title}")
        pe = st.number_input(f"P/E Futuro (NTM) - {title}", value=d_pe, format="%.2f", key=f"p_{title}")
        sh = st.number_input(f"Cambio Acciones % - {title}", value=d_sh, format="%.2f", key=f"s_{title}")
        return rev, marg, pe, sh

# Aplicando tu criterio de P/E 25 para el Caso Base
bear = create_case(bear_col, "Pesimista", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(base_col, "Caso Base", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(bull_col, "Optimista", "🚀", 15.0, 20.0, 30.0, -1.0)

def calc_valuation(inputs):
    rg, fm, fpe, sc = inputs
    future_rev = cr_input_mil * ((1 + rg/100)**projection_years)
    future_ni = future_rev * (fm/100)
    future_market_cap = future_ni * fpe
    future_shares = so_input_mil * ((1 + sc/100)**projection_years)
    
    price_target = future_market_cap / future_shares if future_shares > 0 else 0
    cagr = (((price_target / cp_input)**(1/projection_years)) - 1) * 100 if cp_input > 0 and price_target > 0 else 0
    required_price = price_target / ((1 + desired_return/100)**projection_years)
    
    return price_target, cagr, required_price

if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    st.divider() # Una línea horizontal de separación general
    
    # Creamos las 3 columnas
    col_oso, col_base, col_toro = st.columns(3)

    # --- CASO OSO (CON BORDE) ---
    with col_oso:
        with st.container(border=True):  # <--- ESTO CREA LA CAJA
            st.markdown("### 🐻 Caso Oso")
            # Aquí van tus cálculos del caso Oso (asegúrate de que tus variables coinciden)
            # Ejemplo: st.metric("Precio Compra", f"${precio_oso:.2f}")
            # Si usas funciones para calcular, llámalas aquí dentro.
            st.info("Escenario pesimista")

    # --- CASO BASE (CON BORDE Y DESTACADO) ---
    with col_base:
        with st.container(border=True):  # <--- ESTO CREA LA CAJA
            st.markdown("### ⚖️ Caso Base")
            # Aquí tus cálculos del caso Base
            # st.metric("Precio Compra", f"${precio_base:.2f}")
            
            # Lógica del color (Verde/Rojo)
            # if precio_actual < precio_base:
            #     st.success("¡ZONA DE COMPRA!")
            # else:
            #     st.error("Sobrevalorada")

    # --- CASO TORO (CON BORDE) ---
    with col_toro:
        with st.container(border=True):  # <--- ESTO CREA LA CAJA
            st.markdown("### 🐂 Caso Toro")
            # Aquí tus cálculos del caso Toro
            # st.metric("Precio Compra", f"${precio_toro:.2f}")
            st.warning("Escenario optimista")







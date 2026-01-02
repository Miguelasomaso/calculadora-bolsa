import streamlit as st
import requests
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Stocks Value", page_icon="💎", layout="wide")

API_KEY = "EWVJNFHOMIH4QW49"

if 'data' not in st.session_state:
    st.session_state.data = {'price': 0.0, 'rev': 0.0, 'shares': 0.0, 'pe': 0.0, 'margin': 0.0, 'ticker': ""}

st.title("Stocks Value 💎")

# =========================================
# 1. BUSCADOR
# =========================================
col_ticker, col_btn = st.columns([3, 1])
ticker_input = col_ticker.text_input("Ticker:", value=st.session_state.data['ticker']).upper()

if col_btn.button("🔍 Obtener Datos", use_container_width=True):
    if ticker_input:
        try:
            with st.spinner(f"Buscando {ticker_input}..."):
                url_ov = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={API_KEY}'
                r_ov = requests.get(url_ov).json()
                time.sleep(1)
                url_pr = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_input}&apikey={API_KEY}'
                r_pr = requests.get(url_pr).json()

                if "Symbol" in r_ov:
                    st.session_state.data.update({
                        'price': float(r_pr.get("Global Quote", {}).get("05. price", 0.0)),
                        'rev': float(r_ov.get("RevenueTTM", 0.0)) / 1_000_000,
                        'shares': float(r_ov.get("SharesOutstanding", 0.0)) / 1_000_000,
                        'margin': float(r_ov.get("ProfitMargin", 0.0)) * 100,
                        'pe': float(r_ov.get("ForwardPE", 0.0)) if r_ov.get("ForwardPE") != 'None' else 0.0,
                        'ticker': ticker_input
                    })
                    st.success(f"Datos de {ticker_input} cargados.")
                else:
                    st.error("Límite de API o Ticker no válido.")
        except:
            st.error("Error de conexión.")

# Formulario (Inputs manuales por si falla la API)
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

cp_input = c1.number_input("Precio ($)", value=float(st.session_state.data['price']))
cr_input_mil = c2.number_input("Ingresos (M$)", value=float(st.session_state.data['rev']))
so_input_mil = c3.number_input("Acciones (M)", value=float(st.session_state.data['shares']))
pe_actual = c4.number_input("P/E Actual", value=float(st.session_state.data['pe']))
pm_input = c5.number_input("Margen (%)", value=float(st.session_state.data['margin']))

st.markdown("---")

# =========================================
# 2. ESCENARIOS
# =========================================
projection_years = st.slider("Años proyección", 1, 15, 5)
desired_return = st.number_input("Rentabilidad deseada %", value=15.0)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento % ({title})", value=d_rev)
        marg = st.number_input(f"Margen % ({title})", value=d_marg)
        pe = st.number_input(f"P/E Futuro ({title})", value=d_pe)
        sh = st.number_input(f"Acciones % ({title})", value=d_sh)
        return rev, marg, pe, sh

col1, col2, col3 = st.columns(3)
bear = create_case(col1, "Bear Case", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(col2, "Base Case", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(col3, "Bull Case", "🚀", 15.0, 20.0, 30.0, -1.0)

# =========================================
# 3. RESULTADOS (ESTILO SEGURO)
# =========================================
if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    def calc_val(inputs):
        rg, fm, fpe, sc = inputs
        try:
            f_rev = cr_input_mil * ((1 + rg/100)**projection_years)
            f_ni = f_rev * (fm/100)
            f_mc = f_ni * fpe
            f_sh = so_input_mil * ((1 + sc/100)**projection_years)
            pt = f_mc / f_sh if f_sh > 0 else 0
            cagr = (((pt / cp_input)**(1/projection_years)) - 1) * 100 if cp_input > 0 and pt > 0 else 0
            buy = pt / ((1 + desired_return/100)**projection_years)
            return pt, cagr, buy
        except:
            return 0.0, 0.0, 0.0

    pt_be, c_be, b_be = calc_val(bear)
    pt_ba, c_ba, b_ba = calc_val(base)
    pt_bu, c_bu, b_bu = calc_val(bull)
    
    # Tarjetas limpias
    r1, r2, r3 = st.columns(3)

    with r1:
        st.info(f"🐻 **Bear Case**\n\nPrecio Futuro: ${pt_be:.2f}\n\nCAGR: {c_be:.2f}%\n\nCompra hoy: **${b_be:.2f}**")

    with r2:
        color_msg = "✅ OPORTUNIDAD" if cp_input <= b_ba and cp_input > 0 else "❌ CARA"
        st.success(f"📊 **Base Case**\n\nPrecio Futuro: ${pt_ba:.2f}\n\nCAGR: {c_ba:.2f}%\n\nCompra hoy: **${b_ba:.2f}**\n\n{color_msg}")

    with r3:
        st.info(f"🚀 **Bull Case**\n\nPrecio Futuro: ${pt_bu:.2f}\n\nCAGR: {c_bu:.2f}%\n\nCompra hoy: **${b_bu:.2f}**")


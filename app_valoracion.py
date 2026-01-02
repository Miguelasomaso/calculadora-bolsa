import streamlit as st
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Stocks Value", page_icon="💎", layout="wide")

API_KEY = "EWVJNFHOMIH4QW49"

# Memoria de la sesión
if 'data' not in st.session_state:
    st.session_state.data = {
        'price': 0.0, 'rev': 0.0, 'shares': 0.0, 
        'pe': 0.0, 'margin': 0.0, 'ticker': ""
    }

st.title("Stocks Value 💎")
st.caption("Conexión Profesional vía Alpha Vantage")

# =========================================
# 1. BUSCADOR PROFESIONAL (SIN BLOQUEOS)
# =========================================
st.header("1. Datos Actuales")

col_ticker, col_btn = st.columns([3, 1])
ticker_input = col_ticker.text_input("Ticker (ej: META, MSFT, V):", value=st.session_state.data['ticker']).upper()

if col_btn.button("🔍 Obtener Datos", use_container_width=True):
    if ticker_input:
        try:
            with st.spinner(f"Conectando para obtener datos de {ticker_input}..."):
                # Petición 1: Precio Actual
                url_price = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_input}&apikey={API_KEY}'
                r_price = requests.get(url_price).json()
                
                # Petición 2: Datos Fundamentales
                url_fun = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={API_KEY}'
                r_fun = requests.get(url_fun).json()
                
                if "Global Quote" in r_price and "Symbol" in r_fun:
                    price = float(r_price["Global Quote"]["05. price"])
                    rev = float(r_fun["RevenueTTM"]) / 1_000_000
                    shares = float(r_fun["SharesOutstanding"]) / 1_000_000
                    margin = float(r_fun["ProfitMargin"]) * 100
                    pe = float(r_fun["ForwardPE"]) if r_fun["ForwardPE"] != 'None' else 0.0
                    
                    st.session_state.data.update({
                        'price': price, 'rev': rev, 'shares': shares, 
                        'margin': margin, 'pe': pe, 'ticker': ticker_input
                    })
                    st.success(f"¡Datos de {ticker_input} cargados!")
                else:
                    st.error("Ticker no encontrado o límite de API (25 al día) alcanzado.")
        except Exception as e:
            st.error("Error al conectar con la fuente de datos.")

# Formulario (se auto-rellena)
c1, c2, c3 = st.columns(3)
c4, c5, c6 = st.columns(3)

cp_input = c1.number_input("Precio Acción ($)", value=float(st.session_state.data['price']), format="%.2f")
cr_input_mil = c2.number_input("Ingresos Totales (M$)", value=float(st.session_state.data['rev']), format="%.2f")
so_input_mil = c3.number_input("Acciones (M)", value=float(st.session_state.data['shares']), format="%.2f")
pe_actual = c4.number_input("P/E Estimado", value=float(st.session_state.data['pe']), format="%.2f")
pm_input = c5.number_input("Margen (%)", value=float(st.session_state.data['margin']), format="%.2f")
ni_calc = (cr_input_mil * (pm_input/100))
c6.write(f"Beneficio Est. (M$): \n\n **${ni_calc:.2f}**")

# =========================================
# 2. ESCENARIOS
# =========================================
st.markdown("---")
st.header("2. Tus Escenarios de Proyección")

col_y, col_r = st.columns(2)
projection_years = col_y.slider("Años proyección", 1, 15, 5)
desired_return = col_r.number_input("Rentabilidad deseada (%)", value=15.0)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento %", value=d_rev, key=f"r_{title}")
        marg = st.number_input(f"Margen %", value=d_marg, key=f"m_{title}")
        pe = st.number_input(f"P/E Futuro", value=d_pe, key=f"p_{title}")
        sh = st.number_input(f"Acciones %", value=d_sh, key=f"s_{title}")
        return rev, marg, pe, sh

col1, col2, col3 = st.columns(3)
bear = create_case(col1, "Bear Case", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(col2, "Base Case", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(col3, "Bull Case", "🚀", 15.0, 20.0, 30.0, -1.0)

# =========================================
# 3. RESULTADOS (TARJETAS HTML)
# =========================================
if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    def calc_val(inputs):
        rg, fm, fpe, sc = inputs
        f_rev = cr_input_mil * ((1 + rg/100)**projection_years)
        f_ni = f_rev * (fm/100)
        f_mc = f_ni * fpe
        f_sh = so_input_mil * ((1 + sc/100)**projection_years)
        pt = f_mc / f_sh if f_sh > 0 else 0
        cagr = (((pt / cp_input)**(1/projection_years)) - 1) * 100 if cp_input > 0 and pt > 0 else 0
        buy = pt / ((1 + desired_return/100)**projection_years)
        return pt, cagr, buy

    pt_be, c_be, b_be = calc_val(bear)
    pt_ba, c_ba, b_ba = calc_val(base)
    pt_bu, c_bu, b_bu = calc_val(bull)
    
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🐻 Bear Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_be:.2f}</b></p><p>CAGR: <b>{c_be:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_be:.2f}</h3></div>', unsafe_allow_html=True)

    with r2:
        color = "green" if cp_input <= b_ba else "#d32f2f"
        st.markdown(f'<div style="border:2px solid {color}; border-radius:12px; padding:20px; margin-bottom:20px; background-color:#f0fdf4; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><h2 style="color:#1b5e20;">📊 Base Case</h2><p>Precio Futuro ({projection_years}a):<br><b style="font-size:24px;">${pt_ba:.2f}</b></p><p>CAGR: <b>{c_ba:.2f}%</b></p><hr><p style="font-size:14px; font-weight:bold;">COMPRA HOY:</p><h1 style="color:{color};">${b_ba:.2f}</h1></div>', unsafe_allow_html=True)

    with r3:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🚀 Bull Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_bu:.2f}</b></p><p>CAGR: <b>{c_bu:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_bu:.2f}</h3></div>', unsafe_allow_html=True)


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
# 1. BUSCADOR REFORZADO ALPHA VANTAGE
# =========================================
st.header("1. Datos Actuales")

col_ticker, col_btn = st.columns([3, 1])
ticker_input = col_ticker.text_input("Ticker (ej: META, AAPL, MSFT):", value=st.session_state.data['ticker']).upper()

if col_btn.button("🔍 Obtener Datos", use_container_width=True):
    if ticker_input:
        try:
            with st.spinner(f"Buscando {ticker_input} en Alpha Vantage..."):
                # URL 1: Datos de la empresa (OVERVIEW)
                url_ov = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={API_KEY}'
                r_ov = requests.get(url_ov).json()
                
                # Esperamos un segundo para no saturar la API gratuita
                time.sleep(1)
                
                # URL 2: Precio (GLOBAL_QUOTE)
                url_pr = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_input}&apikey={API_KEY}'
                r_pr = requests.get(url_pr).json()

                # Verificamos si la API nos ha dado un mensaje de error o límite
                if "Note" in r_ov or "Note" in r_pr:
                    st.warning("Límite de la API alcanzado (25/día). Espera un minuto o introduce datos a mano.")
                elif "Symbol" in r_ov:
                    # Extraer datos con seguridad
                    price = float(r_pr.get("Global Quote", {}).get("05. price", 0.0))
                    rev = float(r_ov.get("RevenueTTM", 0.0)) / 1_000_000
                    shares = float(r_ov.get("SharesOutstanding", 0.0)) / 1_000_000
                    margin = float(r_ov.get("ProfitMargin", 0.0)) * 100
                    pe = float(r_ov.get("ForwardPE", 0.0)) if r_ov.get("ForwardPE") != 'None' else 0.0
                    
                    st.session_state.data.update({
                        'price': price, 'rev': rev, 'shares': shares, 
                        'margin': margin, 'pe': pe, 'ticker': ticker_input
                    })
                    st.success(f"¡Datos de {ticker_input} cargados con éxito!")
                else:
                    st.error(f"No se encontró el ticker '{ticker_input}'. Asegúrate de que es correcto.")
        except Exception as e:
            st.error("Error al procesar los datos de la API.")

# --- EL RESTO DEL CÓDIGO (FORMULARIO Y TARJETAS) SIGUE IGUAL ---
# (Usa el código que te pasé anteriormente para las secciones 2 y 3)

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
    
    # CSS para que las tarjetas se adapten al móvil
    st.markdown("""
        <style>
        [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        @media (min-width: 768px) {
            [data-testid="column"] {
                width: 33.33% !important;
                min-width: 33.33% !important;
            }
        }
        .card {
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(f'''
        <div class="card" style="border: 1px solid #ccc; background-color: #f9f9f9;">
            <h3 style="margin:0;">🐻 Bear Case</h3>
            <p style="margin: 10px 0 5px 0;">Precio Futuro ({projection_years}a):</p>
            <b style="font-size: 22px;">${pt_be:.2f}</b>
            <p style="margin: 5px 0;">CAGR: <b>{c_be:.2f}%</b></p>
            <hr style="margin: 15px 0;">
            <p style="font-size: 13px; margin:0;">Compra máx. hoy:</p>
            <h3 style="margin:0; color: #555;">${b_be:.2f}</h3>
        </div>
        ''', unsafe_allow_html=True)

    with r2:
        color = "green" if cp_input <= b_ba and cp_input > 0 else "#d32f2f"
        f_color = "#1b5e20" if color == "green" else "#d32f2f"
        st.markdown(f'''
        <div class="card" style="border: 3px solid {color}; background-color: #f0fdf4;">
            <h2 style="margin:0; color: {f_color};">📊 Base Case</h2>
            <p style="margin: 10px 0 5px 0;">Precio Futuro ({projection_years}a):</p>
            <b style="font-size: 28px; color: #000;">${pt_ba:.2f}</b>
            <p style="margin: 5px 0;">CAGR: <b>{c_ba:.2f}%</b></p>
            <hr style="border-top: 1px solid #ccc; margin: 15px 0;">
            <p style="font-size: 15px; font-weight: bold; margin:0;">PRECIO DE COMPRA HOY:</p>
            <h1 style="color: {color}; margin:0; font-size: 40px;">${b_ba:.2f}</h1>
        </div>
        ''', unsafe_allow_html=True)

    with r3:
        st.markdown(f'''
        <div class="card" style="border: 1px solid #ccc; background-color: #f9f9f9;">
            <h3 style="margin:0;">🚀 Bull Case</h3>
            <p style="margin: 10px 0 5px 0;">Precio Futuro ({projection_years}a):</p>
            <b style="font-size: 22px;">${pt_bu:.2f}</b>
            <p style="margin: 5px 0;">CAGR: <b>{c_bu:.2f}%</b></p>
            <hr style="margin: 15px 0;">
            <p style="font-size: 13px; margin:0;">Compra máx. hoy:</p>
            <h3 style="margin:0; color: #555;">${b_bu:.2f}</h3>
        </div>
        ''', unsafe_allow_html=True)

import streamlit as st
import yfinance as yf

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Stocks Value", page_icon="💎", layout="wide")

# --- MEMORIA DE LA APP ---
if 'data' not in st.session_state:
    st.session_state.data = {
        'price': 0.0, 'rev': 0.0, 'shares': 0.0, 
        'pe': 0.0, 'margin': 0.0, 'net_income': 0.0,
        'ticker': ""
    }

st.title("Stocks Value 💎")

# =========================================
# 1. DATOS ACTUALES
# =========================================
st.header("1. Datos Actuales")

col_ticker, col_btn = st.columns([3, 1])
with col_ticker:
    ticker_input = st.text_input("Ticker:", value=st.session_state.data['ticker']).upper()
with col_btn:
    st.write("")
    st.write("")
    search_btn = st.button("🔍 Buscar")

if search_btn and ticker_input:
    try:
        with st.spinner("Buscando..."):
            stock = yf.Ticker(ticker_input)
            info = stock.info
            if info:
                st.session_state.data['price'] = info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
                st.session_state.data['rev'] = (info.get('totalRevenue', 0.0)) / 1_000_000
                st.session_state.data['shares'] = (info.get('sharesOutstanding', 0.0)) / 1_000_000
                st.session_state.data['margin'] = (info.get('profitMargins', 0.0)) * 100
                st.session_state.data['pe'] = info.get('forwardPE') or info.get('trailingPE') or 0.0
                st.session_state.data['ticker'] = ticker_input
                st.success("¡Datos cargados!")
    except:
        st.warning("Yahoo bloqueado. Introduce datos a mano.")

col_d1, col_d2, col_d3 = st.columns(3)
col_d4, col_d5, col_d6 = st.columns(3)

cp_input = col_d1.number_input("Precio Actual ($)", value=float(st.session_state.data['price']))
cr_input_mil = col_d2.number_input("Ingresos (M$)", value=float(st.session_state.data['rev']))
so_input_mil = col_d3.number_input("Acciones (M)", value=float(st.session_state.data['shares']))
pe_estimado = col_d4.number_input("P/E Actual", value=float(st.session_state.data['pe']))
pm_input = col_d5.number_input("Margen (%)", value=float(st.session_state.data['margin']))
ni_input_mil = col_d6.number_input("Beneficio (M$)", value=float(st.session_state.data.get('net_income', 0.0)))

# =========================================
# 2. ESCENARIOS
# =========================================
st.markdown("---")
projection_years = st.slider("Años proyección", 1, 15, 5)
desired_return = st.number_input("Rentabilidad deseada %", value=15.0)

def create_case(column, title, emoji, d_rev, d_marg, d_pe, d_sh):
    with column:
        st.subheader(f"{emoji} {title}")
        rev = st.number_input(f"Crecimiento % - {title}", value=d_rev)
        marg = st.number_input(f"Margen % - {title}", value=d_marg)
        pe = st.number_input(f"P/E Futuro - {title}", value=d_pe)
        sh = st.number_input(f"Acciones % - {title}", value=d_sh)
        return rev, marg, pe, sh

c1, c2, c3 = st.columns(3)
bear = create_case(c1, "Bear Case", "🐻", 4.0, 10.0, 15.0, 1.0)
base = create_case(c2, "Base Case", "📊", 8.0, 15.0, 25.0, 0.0) 
bull = create_case(c3, "Bull Case", "🚀", 15.0, 20.0, 30.0, -1.0)

def calc_safe(inputs):
    rg, fm, fpe, sc = inputs
    try:
        f_rev = cr_input_mil * ((1 + rg/100)**projection_years)
        f_ni = f_rev * (fm/100)
        f_mc = f_ni * fpe
        f_sh = so_input_mil * ((1 + sc/100)**projection_years)
        pt = f_mc / f_sh if f_sh > 0 else 0
        cagr = (((pt / cp_input)**(1/projection_years)) - 1) * 100 if cp_input > 0 and pt > 0 else 0
        buy = pt / ((1 + desired_return/100)**projection_years)
        return float(pt), float(cagr), float(buy)
    except:
        return 0.0, 0.0, 0.0

# =========================================
# 3. RESULTADOS
# =========================================
if st.button("CALCULAR VALOR INTRÍNSECO", type="primary", use_container_width=True):
    pt_be, c_be, b_be = calc_safe(bear)
    pt_ba, c_ba, b_ba = calc_safe(base)
    pt_bu, c_bu, b_bu = calc_safe(bull)
    
    res_oso, res_base, res_toro = st.columns(3)

    with res_oso:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🐻 Bear Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_be:.2f}</b></p><p>CAGR: <b>{c_be:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_be:.2f}</h3></div>', unsafe_allow_html=True)

    with res_base:
        color = "green" if cp_input <= b_ba and cp_input > 0 else "#d32f2f"
        st.markdown(f'<div style="border:2px solid {color}; border-radius:12px; padding:20px; margin-bottom:20px; background-color:#f0fdf4;"><h2 style="color:#1b5e20;">📊 Base Case</h2><p>Precio Futuro ({projection_years}a):<br><b style="font-size:24px;">${pt_ba:.2f}</b></p><p>CAGR: <b>{c_ba:.2f}%</b></p><hr><p style="font-size:14px; font-weight:bold;">COMPRA HOY:</p><h1 style="color:{color};">${b_ba:.2f}</h1></div>', unsafe_allow_html=True)

    with res_toro:
        st.markdown(f'<div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:20px; background-color:#f9f9f9;"><h3>🚀 Bull Case</h3><p>Precio Futuro ({projection_years}a):<br><b>${pt_bu:.2f}</b></p><p>CAGR: <b>{c_bu:.2f}%</b></p><hr><p style="font-size:12px">Compra hoy:</p><h3>${b_bu:.2f}</h3></div>', unsafe_allow_html=True)


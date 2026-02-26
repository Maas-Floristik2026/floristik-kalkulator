import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V23", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "Gast-Test-123": {"name": "Gastzugang", "valid_until": "2026-02-28"},
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "e0"

# LOGIN LOGIK
if not st.session_state.auth:
    st.title("🔐 Lizenz-Login")
    key_input = st.text_input("Lizenzschluessel", type="password")
    if st.button("Anmelden", use_container_width=True):
        if key_input in LIZENZ_DATENBANK:
            st.session_state.auth = True
            st.session_state.user_name = LIZENZ_DATENBANK[key_input]["name"]
            st.rerun()
    st.stop()

# --- CSS FÜR KOMPAKT-LOOK & FARBEN ---
st.markdown("""
<style>
    /* Hauptbuttons */
    div.stButton > button { 
        height: 3.2em !important; 
        font-weight: bold !important; 
        font-size: 0.9em !important;
        border-radius: 8px !important; 
    }
    /* Mini-Minus Buttons */
    .minus-container button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 1.8em !important;
        width: 1.8em !important;
        min-width: 1.8em !important;
        padding: 0px !important;
        font-size: 0.7em !important;
        margin-top: 5px !important;
        border: none !important;
    }
    /* Numpad Styling */
    .numpad button {
        height: 3em !important;
        background-color: #f0f2f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# INITIALISIERUNG
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gruen' not in st.session_state: st.session_state.c_gruen = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Chico": 0}
if 'c_schleife' not in st.session_state: st.session_state.c_schleife = {"Schleife kurz/schmal": 0, "Schleife lang/breit": 0}
if 'c_labor' not in st.session_state: st.session_state.c_labor = 0
if 'e0' not in st.session_state: st.session_state.e0 = 0.0
if 'e1' not in st.session_state: st.session_state.e1 = 0.0
if 'e2' not in st.session_state: st.session_state.e2 = 0.0

def reset_callback():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gruen: st.session_state.c_gruen[k] = 0
    for k in st.session_state.c_schleife: st.session_state.c_schleife[k] = 0
    st.session_state.c_labor = 0
    st.session_state.e0, st.session_state.e1, st.session_state.e2 = 0.0, 0.0, 0.0

# --- HILFSFUNKTION FÜR NUMPAD ---
def add_digit(digit):
    field = st.session_state.active_field
    current = str(st.session_state[field])
    if current == "0.0": current = ""
    new_val = current + str(digit)
    try: st.session_state[field] = float(new_val)
    except: pass

# --- UI ---
st.title("🌿 Floristik Kalkulator Pro")

# SEITENLEISTE MIT VIRTUELLEM NUMPAD
with st.sidebar:
    st.subheader("Zusatzkosten (Touch)")
    
    # Auswahl des Feldes
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("Gefaess", type="primary" if st.session_state.active_field=="e0" else "secondary"): st.session_state.active_field="e0"
    if col_b.button("Extra 1", type="primary" if st.session_state.active_field=="e1" else "secondary"): st.session_state.active_field="e1"
    if col_c.button("Extra 2", type="primary" if st.session_state.active_field=="e2" else "secondary"): st.session_state.active_field="e2"
    
    st.write(f"Editierung: **{st.session_state.active_field}**")
    val_disp = st.empty()
    val_disp.code(f"{st.session_state[st.session_state.active_field]:.2f} EUR", language="text")

    # Das Numpad
    st.markdown('<div class="numpad">', unsafe_allow_html=True)
    n_cols = st.columns(3)
    for i in range(1, 10):
        if n_cols[(i-1)%3].button(str(i), key=f"num_{i}"):
            f = st.session_state.active_field
            st.session_state[f] = float(f"{int(st.session_state[f]*100)}{i}")/100
            st.rerun()
    if n_cols[0].button("0", key="num_0"):
        f = st.session_state.active_field
        st.session_state[f] = float(f"{int(st.session_state[f]*100)}0")/100
        st.rerun()
    if n_cols[1].button(".", key="num_dot"): pass # Vereinfacht auf 2 Nachkommastellen autom.
    if n_cols[2].button("C", key="num_clear"):
        st.session_state[st.session_state.active_field] = 0.0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# BERECHNUNGEN
gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Chico": 1.20}
schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}
mat_sum = sum(k * v for k, v in st.session_state.c_mat.items())
gruen_sum = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
schleif_sum = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
labor_sum = st.session_state.c_labor * 0.80
grand_total = mat_sum + gruen_sum + schleif_sum + labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# ANZEIGE
c1, c2, c3 = st.columns(3)
c1.metric("Blumen & Gruen", f"{mat_sum + gruen_sum:.2f} EUR")
c2.metric("Extras & Arbeit", f"{labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2 + schleif_sum:.2f} EUR")
c3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()
t1, t2, t3, t4 = st.tabs(["🌸 Preise", "🌿 Gruen", "🎀 Extras", "📋 Beleg"])

with t1:
    rows = [sorted(st.session_state.c_mat.keys())[i:i+8] for i in range(0, len(st.session_state.c_mat), 8)]
    for row in rows:
        cols = st.columns(8)
        for i, p_val in enumerate(row):
            with cols[i]:
                # Haupt-Button
                st.button(f"{p_val:.2f}", key=f"m_{p_val}", on_click=lambda p=p_val: st.session_state.c_mat.update({p: st.session_state.c_mat[p] + 1}), use_container_width=True)
                
                # Kompakter Counter & Minus
                if st.session_state.c_mat[p_val] > 0:
                    c_left, c_right = st.columns([1,1])
                    c_left.caption(f"**{st.session_state.c_mat[p_val]}x**")
                    with c_right:
                        st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_m_{p_val}"):
                            st.session_state.c_mat[p_val] -= 1
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

with t2:
    g_cols = st.columns(5)
    g_names = list(gruen_p.keys())
    for i, name in enumerate(g_names):
        with g_cols[i]:
            st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True, on_click=lambda n=name: st.session_state.c_gruen.update({n: st.session_state.c_gruen[n] + 1}))
            if st.session_state.c_gruen[name] > 0:
                c_l, c_r = st.columns([1,1])
                c_l.write(f"**{st.session_state.c_gruen[name]}x**")
                with c_r:
                    st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                    if st.button("—", key=f"min_g_{name}"):
                        st.session_state.c_gruen[name] -= 1
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

with t3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeit")
        st.button("➕ 1 Min", key="btn_labor", on_click=lambda: st.session_state.update({"c_labor": st.session_state.c_labor + 1}))
        st.write(f"Zeit: {st.session_state.c_labor} Min")
        if st.session_state.c_labor > 0:
            st.markdown('<div class="minus-container">', unsafe_allow_html=True)
            if st.button("— 1 Min", key="min_labor"):
                st.session_state.c_labor -= 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    with cb:
        st.subheader("Schleifen")
        for s_name, s_price in schleif_p.items():
            st.button(f"{s_name} ({s_price}€)", key=f"s_{s_name}", on_click=lambda n=s_name: st.session_state.c_schleife.update({n: st.session_state.c_schleife[n] + 1}))
            if st.session_state.c_schleife[s_name] > 0:
                st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                if st.button(f"— {s_name}", key=f"min_s_{s_name}"):
                    st.session_state.c_schleife[s_name] -= 1
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# RESET & PDF (In Tab 4 für maximale Übersicht)
with t4:
    st.button("ALLES LOESCHEN (RESET)", key="reset_btn", on_click=reset_callback, use_container_width=True)
    # Beleg-Tabelle
    dt = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    # ... (Rest der dt befüllung)
    if dt: st.table(pd.DataFrame(dt))

st.markdown('</div>', unsafe_allow_html=True)

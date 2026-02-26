import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="Floristik Kalkulator V36", layout="wide")

# --- 2. LOGIN ---
LIZENZ_DB = {
    "Florist-1": {"name": "Florist-1-Laden", "bis": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "bis": "2030-12-31"},
    "FDF-Duisburg": {"name": "FDF Gast", "bis": "2026-12-31"}
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'active_f' not in st.session_state: st.session_state.active_f = "e0"

if not st.session_state.auth:
    st.title("🔐 Login")
    schluessel = st.text_input("Lizenzschlüssel", type="password")
    if st.button("Anmelden", use_container_width=True):
        if schluessel in LIZENZ_DB:
            st.session_state.auth = True
            st.session_state.user = LIZENZ_DB[schluessel]["name"]
            st.rerun()
    st.stop()

# --- 3. CSS (FÜR DEN TOUCH-PC OPTIMIERT) ---
st.markdown("""
<style>
    /* Zwingt alle Spalten auf eine einheitliche Höhe */
    [data-testid="column"] {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px !important;
        min-height: 110px !important;
        margin-bottom: 5px !important;
    }
    /* Buttons */
    div.stButton > button {
        height: 3em !important;
        font-weight: bold !important;
    }
    /* Minus-Bereich */
    .minus-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 5px;
    }
    /* Numpad Display */
    .lcd-display {
        background-color: #000;
        color: #39FF14;
        padding: 15px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 2em;
        text-align: right;
        border: 3px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. DATEN INITIALISIEREN ---
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gr' not in st.session_state: st.session_state.c_gr = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Chico": 0}
if 'c_sch' not in st.session_state: st.session_state.c_sch = {"Schleife klein": 0, "Schleife groß": 0}
if 'c_lab' not in st.session_state: st.session_state.c_lab = 0
if 'e0' not in st.session_state: st.session_state.e0 = 0.0
if 'e1' not in st.session_state: st.session_state.e1 = 0.0
if 'e2' not in st.session_state: st.session_state.e2 = 0.0

def reset_all():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gr: st.session_state.c_gr[k] = 0
    for k in st.session_state.c_sch: st.session_state.c_sch[k] = 0
    st.session_state.c_lab = 0
    st.session_state.e0 = st.session_state.e1 = st.session_state.e2 = 0.0

# --- 5. SIDEBAR (NUMPAD) ---
with st.sidebar:
    st.subheader("Zusatzkosten (Touch)")
    # Einfachere Auswahl für mehr Geschwindigkeit
    wahl = st.radio("Feld:", ["Gefäß", "Extra 1", "Extra 2"], horizontal=True)
    mapping = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    target = mapping[wahl]
    
    st.markdown(f'<div class="lcd-display">{st.session_state[target]:.2f} €</div>', unsafe_allow_html=True)
    
    # Schnelles Numpad (ohne Buffer, direktes Rechnen)
    for r in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, val in enumerate(r):
            if cols[i].button(str(val), key=f"num_{val}", use_container_width=True):
                st.session_state[target] = round(st.session_state[target] * 10 + val * 0.01, 2)
                st.rerun()
    
    cb = st.columns(3)
    if cb[0].button("0", use_container_width=True):
        st.session_state[target] = round(st.session_state[target] * 10, 2)
        st.rerun()
    if cb[1].button("C", use_container_width=True):
        st.session_state[target] = 0.0
        st.rerun()
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# --- 6. BERECHNUNG ---
p_gr = {"Pistazie": 1.5, "Euka": 2.5, "Salal": 1.5, "Baergras": 0.6, "Chico": 1.2}
p_sch = {"Schleife klein": 15.0, "Schleife groß": 20.0}

sum_mat = sum(k * v for k, v in st.session_state.c_mat.items())
sum_gr = sum(st.session_state.c_gr[n] * p_gr[n] for n in st.session_state.c_gr)
sum_sch = sum(st.session_state.c_sch[n] * p_sch[n] for n in st.session_state.c_sch)
sum_lab = st.session_state.c_lab * 0.8
total = sum_mat + sum_gr + sum_sch + sum_lab + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- 7. UI ---
c1, c2, c3 = st.columns(3)
c1.metric("Blumen & Grün", f"{sum_mat + sum_gr:.2f} €")
c2.metric("Extras & Arbeit", f"{sum_lab + sum_sch + st.session_state.e0 + st.session_state.e1 + st.session_state.e2:.2f} €")
c3.subheader(f"GESAMT: {total:.2f} €")

st.divider()
tabs = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Beleg"])

with tabs[0]:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p = p_keys[i+j]
                with cols[j]:
                    if st.button(f"{p:.2f}", key=f"p_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1
                        st.rerun()
                    anz = st.session_state.c_mat[p]
                    if anz > 0:
                        # Einfache Zeile für Anzahl und Minus
                        st.write(f"**{anz}x**")
                        if st.button("—", key=f"m_{p}", use_container_width=True):
                            st.session_state.c_mat[p] -= 1
                            st.rerun()

with tabs[1]:
    g_cols = st.columns(5)
    for i, name in enumerate(p_gr.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{p_gr[name]:.2f}", key=f"gr_{name}", use_container_width=True):
                st.session_state.c_gr[name] += 1
                st.rerun()
            anz = st.session_state.c_gr[name]
            if anz > 0:
                st.write(f"**{anz}x**")
                if st.button("—", key=f"mgr_{name}", use_container_width=True):
                    st.session_state.c_gr[name] -= 1
                    st.rerun()

with tabs[2]:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button("➕ 1 Minute (0,80 €)", use_container_width=True):
            st.session_state.c_lab += 1
            st.rerun()
        if st.session_state.c_lab > 0:
            st.info(f"{st.session_state.c_lab} Min = {sum_lab:.2f} €")
            if st.button("— Minute abziehen", use_container_width=True):
                st.session_state.c_lab -= 1
                st.rerun()
    with cb:
        st.subheader("Schleifen")
        for sn, sp in p_sch.items():
            if st.button(f"{sn} ({sp:.2f} €)", key=f"sch_{sn}", use_container_width=True):
                st.session_state.c_sch[sn] += 1
                st.rerun()
            if st.session_state.c_sch[sn] > 0:
                st.write(f"**{st.session_state.c_sch[sn]}x**")
                if st.button(f"— {sn} weg", key=f"msch_{sn}", use_container_width=True):
                    st.session_state.c_sch[sn] -= 1
                    st.rerun()

with tabs[3]:
    st.button("♻️ ALLES LÖSCHEN", on_click=reset_all, use_container_width=True)
    li = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: li.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gr.items():
        if c > 0: li.append({"Pos": n, "Anz": c, "Sum": c*p_gr[n]})
    # ... weitere Positionen
    if li:
        st.table(pd.DataFrame(li))
        def make_pdf():
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulation", ln=True, align="C")
            pdf.set_font("Arial", "", 12)
            for d in li:
                pdf.cell(200, 10, f"{d['Pos']} | {d['Anz']}x | {d['Sum']:.2f} EUR", ln=True)
            pdf.cell(200, 10, f"GESAMT: {total:.2f} EUR", ln=True)
            return pdf.output(dest="S").encode("latin-1")
        st.download_button("Beleg speichern", data=make_pdf(), file_name="Beleg.pdf", use_container_width=True)

st.divider()
if st.button("ZENTRALER RESET", key="master_res", on_click=reset_all): pass

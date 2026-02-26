import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- 1. GRUNDEINSTELLUNGEN ---
st.set_page_config(page_title="Floristik Kalkulator V35", layout="wide")

# --- 2. LOGIN DATEN ---
LIZENZ_DB = {
    "Florist-1": {"name": "Florist-1-Laden", "bis": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "bis": "2030-12-31"},
    "FDF-Duisburg": {"name": "FDF Gast", "bis": "2026-12-31"}
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'f_active' not in st.session_state: st.session_state.f_active = "Gefäß"
if 'buf' not in st.session_state: st.session_state.buf = ""

if not st.session_state.auth:
    st.title("🔐 Login")
    schlüssel = st.text_input("Lizenzschlüssel", type="password")
    if st.button("Anmelden", use_container_width=True):
        if schlüssel in LIZENZ_DB:
            st.session_state.auth = True
            st.session_state.user = LIZENZ_DB[schlüssel]["name"]
            st.rerun()
    st.stop()

# --- 3. CSS FÜR DAS UNBEUGSAME GITTER ---
st.markdown("""
<style>
    /* Fixiert die Höhe der gesamten Kachel-Zelle */
    [data-testid="column"] {
        min-height: 110px !important;
        max-height: 110px !important;
        background-color: #fcfcfc;
        border: 1px solid #eee;
        border-radius: 10px;
        padding: 5px !important;
        margin-bottom: 5px !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }

    /* Der Preis Button oben */
    div.stButton > button {
        height: 2.8em !important;
        font-weight: bold !important;
        font-size: 1em !important;
        margin-bottom: 0px !important;
    }

    /* Der Kontroll-Bereich (Anzahl & Minus) */
    .control-row {
        height: 35px; /* Reserviert den Platz IMMER */
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 5px;
        padding: 0 4px;
        background-color: transparent;
    }
    
    .active-row {
        background-color: #f0f2f6;
        border-radius: 6px;
    }

    /* Der Minus-Button als kleine rote Pille */
    .minus-pill button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 1.8em !important;
        width: 1.8em !important;
        min-width: 1.8em !important;
        padding: 0 !important;
        line-height: 1 !important;
        border-radius: 50% !important;
        border: none !important;
        font-size: 0.8em !important;
    }
    
    /* Digitalanzeige Numpad */
    .lcd {
        background-color: #000;
        color: #39FF14;
        padding: 12px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #333;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. WERTE INITIALISIEREN ---
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gr' not in st.session_state: st.session_state.c_gr = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Chico": 0}
if 'c_sch' not in st.session_state: st.session_state.c_sch = {"Schleife klein": 0, "Schleife groß": 0}
if 'c_lab' not in st.session_state: st.session_state.c_lab = 0
if 'e0' not in st.session_state: st.session_state.e0 = 0.0
if 'e1' not in st.session_state: st.session_state.e1 = 0.0
if 'e2' not in st.session_state: st.session_state.e2 = 0.0

def reset():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gr: st.session_state.c_gr[k] = 0
    for k in st.session_state.c_sch: st.session_state.c_sch[k] = 0
    st.session_state.c_lab = 0
    st.session_state.e0 = st.session_state.e1 = st.session_state.e2 = 0.0
    st.session_state.buf = ""

# --- 5. TURBO-SIDEBAR ---
@st.fragment
def render_numpad():
    st.subheader("Zusatzkosten (Touch)")
    choice = st.radio("Bearbeiten:", ["Gefäß", "Extra 1", "Extra 2"], horizontal=True, label_visibility="collapsed")
    mapping = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    target = mapping[choice]
    
    st.markdown(f'<div class="lcd">{st.session_state[target]:.2f} €</div>', unsafe_allow_html=True)
    
    for r in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, v in enumerate(r):
            if cols[i].button(str(v), key=f"n_{v}", use_container_width=True):
                st.session_state.buf += str(v)
                st.session_state[target] = float(st.session_state.buf) / 100
                st.rerun()
    
    c_bot = st.columns(3)
    if c_bot[0].button("0", use_container_width=True):
        st.session_state.buf += "0"
        st.session_state[target] = float(st.session_state.buf) / 100
        st.rerun()
    if c_bot[1].button("C", use_container_width=True):
        st.session_state[target] = 0.0
        st.session_state.buf = ""
        st.rerun()
    st.divider()
    if st.button("Abmelden"): st.session_state.auth = False; st.rerun()

with st.sidebar:
    render_numpad()

# --- 6. RECHNUNG ---
p_gr = {"Pistazie": 1.5, "Euka": 2.5, "Salal": 1.5, "Baergras": 0.6, "Chico": 1.2}
p_sch = {"Schleife klein": 15.0, "Schleife groß": 20.0}

s_mat = sum(k * v for k, v in st.session_state.c_mat.items())
s_gr = sum(st.session_state.c_gr[n] * p_gr[n] for n in st.session_state.c_gr)
s_sch = sum(st.session_state.c_sch[n] * p_sch[n] for n in st.session_state.c_sch)
s_lab = st.session_state.c_lab * 0.8
total = s_mat + s_gr + s_sch + s_lab + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- 7. UI METRIKEN ---
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{s_mat + s_gr:.2f} €")
m2.metric("Extras & Arbeit", f"{s_lab + s_sch + st.session_state.e0 + st.session_state.e1 + st.session_state.e2:.2f} €")
m3.subheader(f"GESAMT: {total:.2f} €")

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
                    if st.button(f"{p:.2f}", key=f"btn_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1
                        st.rerun()
                    
                    anz = st.session_state.c_mat[p]
                    if anz > 0:
                        st.markdown(f'<div class="control-row active-row"><span>{anz}x</span>', unsafe_allow_html=True)
                        st.markdown('<div class="minus-pill">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_{p}"):
                            st.session_state.c_mat[p] -= 1
                            st.rerun()
                        st.markdown('</div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="control-row"></div>', unsafe_allow_html=True)

with tabs[1]:
    g_cols = st.columns(5)
    for i, name in enumerate(p_gr.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{p_gr[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gr[name] += 1
                st.rerun()
            anz = st.session_state.c_gr[name]
            if anz > 0:
                st.markdown(f'<div class="control-row active-row"><span>{anz}x</span>', unsafe_allow_html=True)
                st.markdown('<div class="minus-pill">', unsafe_allow_html=True)
                if st.button("—", key=f"min_g_{name}"):
                    st.session_state.c_gr[name] -= 1
                    st.rerun()
                st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="control-row"></div>', unsafe_allow_html=True)

with tabs[2]:
    el, er = st.columns(2)
    with el:
        st.subheader("Arbeitszeit")
        if st.button("➕ 1 Minute (0,80 EUR)", use_container_width=True):
            st.session_state.c_lab += 1
            st.rerun()
        if st.session_state.c_lab > 0:
            st.info(f"{st.session_state.c_lab} Min = {s_lab:.2f} €")
            if st.button("— Minute abziehen", use_container_width=True):
                st.session_state.c_lab -= 1
                st.rerun()
    with er:
        st.subheader("Schleifen")
        for sn, sp in p_sch.items():
            if st.button(f"{sn} ({sp:.2f} €)", key=f"sch_{sn}", use_container_width=True):
                st.session_state.c_sch[sn] += 1
                st.rerun()
            if st.session_state.c_sch[sn] > 0:
                st.write(f"**{st.session_state.c_sch[sn]}x**")
                if st.button(f"— {sn} entfernen", key=f"m_sch_{sn}", use_container_width=True):
                    st.session_state.c_sch[sn] -= 1
                    st.rerun()

with tabs[3]:
    st.button("♻️ ALLES LÖSCHEN", on_click=reset, use_container_width=True)
    li = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: li.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gr.items():
        if c > 0: li.append({"Pos": n, "Anz": c, "Sum": c*p_gr[n]})
    if li:
        st.table(pd.DataFrame(li))
        def gen_pdf():
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulations-Beleg", ln=True, align="C")
            pdf.set_font("Arial", "", 12)
            for d in li:
                txt = f"{d['Pos']} | {d['Anz']}x | {d['Sum']:.2f} EUR"
                pdf.cell(200, 10, txt, ln=True)
            pdf.cell(200, 10, f"GESAMT: {total:.2f} EUR", ln=True)
            return pdf.output(dest="S").encode("latin-1")
        st.download_button("Beleg speichern", data=gen_pdf(), file_name="Beleg.pdf", use_container_width=True)

st.divider()
if st.button("ZENTRALER RESET", key="master_res", on_click=reset): pass

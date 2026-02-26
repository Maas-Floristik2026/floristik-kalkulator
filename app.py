import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- 1. BASIS EINSTELLUNGEN ---
st.set_page_config(page_title="Floristik Kalkulator V33", layout="wide")

# --- 2. LOGIN DATEN ---
LIZENZ_DB = {
    "Florist-1": {"name": "Florist-1-Laden", "bis": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "bis": "2030-12-31"},
    "FDF-Duisburg": {"name": "FDF Gast", "bis": "2026-12-31"}
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'field' not in st.session_state: st.session_state.field = "e0"
if 'buf' not in st.session_state: st.session_state.buf = ""

# Login Prüfung
if not st.session_state.auth:
    st.title("🔐 Login")
    schluessel = st.text_input("Lizenzschlüssel", type="password")
    if st.button("Anmelden", use_container_width=True):
        if schluessel in LIZENZ_DB:
            st.session_state.auth = True
            st.session_state.user = LIZENZ_DB[schluessel]["name"]
            st.rerun()
        else:
            st.error("Schlüssel ungültig!")
    st.stop()

# --- 3. CSS FÜR EIN STABILES DESIGN ---
st.markdown("""
<style>
    /* Fixiert die Höhe der Spalten, damit nichts springt */
    [data-testid="column"] {
        min-height: 130px !important;
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 5px !important;
        margin-bottom: 5px !important;
    }
    /* Preis Buttons */
    div.stButton > button {
        height: 3em !important;
        font-weight: bold !important;
        border: 1px solid #ccc !important;
    }
    /* Minus Buttons */
    .m-btn button {
        background-color: #ffebee !important;
        color: #c62828 !important;
        height: 1.8em !important;
        font-size: 0.8em !important;
        border: 1px solid #c62828 !important;
    }
    /* Digitalanzeige Numpad */
    .disp {
        background-color: #000;
        color: #39FF14;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 1.8em;
        text-align: right;
        margin-bottom: 10px;
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

def alles_loeschen():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gr: st.session_state.c_gr[k] = 0
    for k in st.session_state.c_sch: st.session_state.c_sch[k] = 0
    st.session_state.c_lab = 0
    st.session_state.e0 = st.session_state.e1 = st.session_state.e2 = 0.0
    st.session_state.buf = ""

# --- 5. SIDEBAR (NUMPAD) ---
@st.fragment
def sidebar_logic():
    st.subheader("Zusatzkosten")
    wahl = st.radio("Feld wählen:", ["Gefäß", "Extra 1", "Extra 2"], horizontal=True)
    mapping = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    f_key = mapping[wahl]
    
    st.markdown(f'<div class="disp">{st.session_state[f_key]:.2f} €</div>', unsafe_allow_html=True)
    
    # Numpad Tasten
    for r in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, v in enumerate(r):
            if cols[i].button(str(v), key=f"n_{v}", use_container_width=True):
                st.session_state.buf += str(v)
                st.session_state[f_key] = float(st.session_state.buf) / 100
                st.rerun()
    
    c3 = st.columns(3)
    if c3[0].button("0", use_container_width=True):
        st.session_state.buf += "0"
        st.session_state[f_key] = float(st.session_state.buf) / 100
        st.rerun()
    if c3[1].button("C", use_container_width=True):
        st.session_state[f_key] = 0.0
        st.session_state.buf = ""
        st.rerun()
    
    st.divider()
    if st.button("Abmelden"):
        st.session_state.auth = False
        st.rerun()

with st.sidebar:
    sidebar_logic()

# --- 6. BERECHNUNGEN ---
p_gr = {"Pistazie": 1.5, "Euka": 2.5, "Salal": 1.5, "Baergras": 0.6, "Chico": 1.2}
p_sch = {"Schleife klein": 15.0, "Schleife groß": 20.0}

sum_mat = sum(k * v for k, v in st.session_state.c_mat.items())
sum_gr = sum(st.session_state.c_gr[n] * p_gr[n] for n in st.session_state.c_gr)
sum_sch = sum(st.session_state.c_sch[n] * p_sch[n] for n in st.session_state.c_sch)
sum_lab = st.session_state.c_lab * 0.8
total = sum_mat + sum_gr + sum_sch + sum_lab + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- 7. UI ANZEIGE ---
c1, c2, c3 = st.columns(3)
c1.metric("Blumen & Grün", f"{sum_mat + sum_gr:.2f} €")
c2.metric("Extras & Arbeit", f"{sum_lab + sum_sch + st.session_state.e0 + st.session_state.e1 + st.session_state.e2:.2f} €")
c3.subheader(f"GESAMT: {total:.2f} €")

st.divider()
t_preise, t_gruen, t_extra, t_beleg = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Beleg"])

with t_preise:
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
                        st.write(f"**{anz}x**")
                        st.markdown('<div class="m-btn">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_{p}", use_container_width=True):
                            st.session_state.c_mat[p] -= 1
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

with t_gruen:
    g_cols = st.columns(5)
    for i, name in enumerate(p_gr.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{p_gr[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gr[name] += 1
                st.rerun()
            anz = st.session_state.c_gr[name]
            if anz > 0:
                st.write(f"**{anz}x**")
                st.markdown('<div class="m-btn">', unsafe_allow_html=True)
                if st.button("—", key=f"min_g_{name}", use_container_width=True):
                    st.session_state.c_gr[name] -= 1
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

with t_extra:
    el, er = st.columns(2)
    with el:
        st.subheader("Arbeitszeit")
        if st.button("➕ 1 Min (0,80 €)", key="add_l", use_container_width=True):
            st.session_state.c_lab += 1
            st.rerun()
        if st.session_state.c_lab > 0:
            st.info(f"{st.session_state.c_lab} Min = {sum_lab:.2f} €")
            if st.button("— Min abziehen", key="min_l", use_container_width=True):
                st.session_state.c_lab -= 1
                st.rerun()
    with er:
        st.subheader("Schleifen")
        for sn, sp in p_sch.items():
            if st.button(f"{sn} ({sp:.2f} €)", key=f"s_{sn}", use_container_width=True):
                st.session_state.c_sch[sn] += 1
                st.rerun()
            if st.session_state.c_sch[sn] > 0:
                st.write(f"**{st.session_state.c_sch[sn]}x**")
                if st.button(f"— {sn} weg", key=f"min_s_{sn}", use_container_width=True):
                    st.session_state.c_sch[sn] -= 1
                    st.rerun()

with t_beleg:
    st.button("♻️ ALLES LÖSCHEN", on_click=alles_loeschen, use_container_width=True)
    liste = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: liste.append({"Pos": f"Material {p:.2f} €", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gr.items():
        if c > 0: liste.append({"Pos": n, "Anz": c, "Sum": c*p_gr[n]})
    # ... (weitere Positionen)
    if liste:
        st.table(pd.DataFrame(liste))
        # Einfache PDF Funktion (ohne Euro Symbol wegen Fehlerrisiko)
        def erstelle_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulation", ln=True, align="C")
            pdf.set_font("Arial", "", 12)
            for d in liste:
                txt = f"{d['Pos']} | {d['Anz']}x | {d['Sum']:.2f} EUR".replace("€", "EUR")
                pdf.cell(200, 10, txt, ln=True)
            pdf.cell(200, 10, f"GESAMT: {total:.2f} EUR", ln=True)
            return pdf.output(dest="S").encode("latin-1")
        st.download_button("Beleg speichern", data=erstelle_pdf(), file_name="Beleg.pdf", use_container_width=True)

st.divider()
if st.button("ZENTRALER RESET", key="glob_res", on_click=alles_loeschen): pass

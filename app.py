import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V21", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "Gast-Test-123": {"name": "Gastzugang", "valid_until": "2026-06-30"},
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""

# LOGIN LOGIK
if not st.session_state.auth:
    st.title("🔐 Lizenz-Login")
    key_input = st.text_input("Lizenzschluessel eingeben:", type="password")
    if st.button("Anmelden", use_container_width=True):
        if key_input in LIZENZ_DATENBANK:
            nutzer = LIZENZ_DATENBANK[key_input]
            if datetime.now() <= datetime.strptime(nutzer["valid_until"], "%Y-%m-%d"):
                st.session_state.auth = True
                st.session_state.user_name = nutzer["name"]
                st.rerun()
            else:
                st.error("Lizenz abgelaufen.")
        else:
            st.error("Falscher Schluessel.")
    st.stop()

# --- APP STARTET ---
st.markdown('<div translate="no">', unsafe_allow_html=True)

# CSS für Buttons
st.markdown("""
<style>
    div.stButton > button { height: 4em; font-weight: bold; border-radius: 10px; border: 1px solid #ccc !important; }
</style>
""", unsafe_allow_html=True)

# INITIALISIERUNG
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gruen' not in st.session_state: st.session_state.c_gruen = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Aralien": 0}
if 'c_schleife' not in st.session_state: st.session_state.c_schleife = {"Schleife kurz/schmal": 0, "Schleife lang/breit": 0}
if 'c_labor' not in st.session_state: st.session_state.c_labor = 0

def reset_callback():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gruen: st.session_state.c_gruen[k] = 0
    for k in st.session_state.c_schleife: st.session_state.c_schleife[k] = 0
    st.session_state.c_labor = 0
    st.session_state.e0, st.session_state.e1, st.session_state.e2 = 0.0, 0.0, 0.0

def generate_pdf(details, total, user):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Kalkulations-Beleg", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    # Vermeidung von Umlauten und Sonderzeichen im PDF-Header
    pdf.cell(200, 10, f"Erstellt von: {user} | {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 8, "Position", border=1); pdf.cell(35, 8, "Anzahl", border=1); pdf.cell(45, 8, "Summe", border=1, ln=True)
    pdf.set_font("Arial", "", 12)
    for d in details:
        # Wir ersetzen das € Symbol durch EUR fuer die PDF-Generierung
        pos_text = str(d['Pos']).replace("€", "EUR")
        pdf.cell(100, 8, pos_text, border=1)
        pdf.cell(35, 8, str(d['Anz']), border=1)
        pdf.cell(45, 8, f"{d['Sum']:.2f} EUR", border=1, ln=True)
    pdf.ln(10); pdf.set_font("Arial", "B", 14)
    pdf.cell(180, 10, f"GESAMTBETRAG: {total:.2f} EUR", ln=True, align="R")
    # latin-1 encoding ist Standard fuer FPDF
    return pdf.output(dest="S").encode("latin-1")

# --- UI ---
st.title("🌿 Floristik Kalkulator")
st.info(f"👤 Nutzer: {st.session_state.user_name}")

with st.sidebar:
    st.header("Zusatzkosten")
    e0 = st.number_input("Unterlage / Gefaess (EUR)", min_value=0.0, step=0.1, key="e0")
    e1 = st.number_input("Extra 1 (EUR)", min_value=0.0, step=0.1, key="e1")
    e2 = st.number_input("Extra 2 (EUR)", min_value=0.0, step=0.1, key="e2")
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# Daten sammeln
dt = []
mat_sum = sum(k * v for k, v in st.session_state.c_mat.items())
for p, c in st.session_state.c_mat.items():
    if c > 0: dt.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})

gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Aralien": 0.90}
gruen_sum = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
for n, c in st.session_state.c_gruen.items():
    if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})

schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}
schleif_sum = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
for n, c in st.session_state.c_schleife.items():
    if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*schleif_p[n]})

labor_sum = st.session_state.c_labor * 0.80
if st.session_state.c_labor > 0: dt.append({"Pos": "Arbeitszeit", "Anz": st.session_state.c_labor, "Sum": labor_sum})

if e0 > 0: dt.append({"Pos": "Unterlage/Gefaess", "Anz": 1, "Sum": e0})
if e1 > 0: dt.append({"Pos": "Extra 1", "Anz": 1, "Sum": e1})
if e2 > 0: dt.append({"Pos": "Extra 2", "Anz": 1, "Sum": e2})

grand_total = mat_sum + gruen_sum + schleif_sum + labor_sum + e0 + e1 + e2

# METRIKEN
c1, c2, c3 = st.columns(3)
c1.metric("Blumen & Gruen", f"{mat_sum + gruen_sum:.2f} EUR")
c2.metric("Zubehoer & Arbeit", f"{labor_sum + e0 + e1 + e2 + schleif_sum:.2f} EUR")
c3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()

# TABS
t1, t2, t3, t4 = st.tabs(["🌸 Preise", "🌿 Gruen", "🎀 Extras", "📋 Beleg-Vorschau"])

with t1:
    cols = st.columns(8)
    for i, p_val in enumerate(sorted(st.session_state.c_mat.keys())):
        with cols[i % 8]:
            if st.button(f"{p_val:.2f} EUR", key=f"m_{p_val}"):
                st.session_state.c_mat[p_val] += 1
                st.rerun()
            if st.session_state.c_mat[p_val] > 0: st.caption(f"Anz: {st.session_state.c_mat[p_val]}")

with t2:
    g_cols = st.columns(5)
    g_icons = ["Pistazie", "Euka", "Salal", "Baergras", "Aralien"]
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            if st.button(f"{g_icons[i]}\n{gruen_p[name]:.2f} EUR", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1
                st.rerun()
            st.write(f"Anz: **{st.session_state.c_gruen[name]}**")

with t3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button("1 Minute hinzufuegen", key="btn_labor"):
            st.session_state.c_labor += 1
            st.rerun()
        st.info(f"Zeit: {st.session_state.c_labor} Min = {labor_sum:.2f} EUR")
    with cb:
        st.subheader("Schleifen")
        if st.button("Schleife kurz (15 EUR)", key="s_kurz", use_container_width=True):
            st.session_state.c_schleife["Schleife kurz/schmal"] += 1
            st.rerun()
        if st.button("Schleife lang (20 EUR)", key="s_lang", use_container_width=True):
            st.session_state.c_schleife["Schleife lang/breit"] += 1
            st.rerun()

with t4:
    st.subheader("Aktuelle Positionen")
    if dt:
        st.table(pd.DataFrame(dt))
    else:
        st.write("Noch keine Positionen erfasst.")

# FUSSZEILE
st.divider()
f1, f2 = st.columns(2)
with f1:
    st.button("ALLES LOESCHEN (RESET)", key="reset_btn", on_click=reset_callback, use_container_width=True)

with f2:
    if dt:
        pdf_b = generate_pdf(dt, grand_total, st.session_state.user_name)
        st.download_button("PDF-BELEG SPEICHERN", data=pdf_b, file_name=f"Beleg_{datetime.now().strftime('%H%M')}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("PDF (Liste leer)", disabled=True, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


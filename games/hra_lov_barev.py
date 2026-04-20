import random
import time

import streamlit as st


MOZNOSTI = ["🟥 ČERVENÁ", "🟦 MODRÁ", "🟩 ZELENÁ", "🟨 ŽLUTÁ", "🟪 FIALOVÁ", "🟧 ORANŽOVÁ"]


def spustit_hru(zivoty: int = 5, kola: int = 20):
    st.session_state.lov_barev = {
        "aktivni": True,
        "hotovo": False,
        "zivoty": zivoty,
        "max_zivoty": zivoty,
        "kola_zbyva": kola,
        "kola_celkem": kola,
        "skore": 0,
        "cil": random.choice(MOZNOSTI),
        "feedback": "",
        "posledni_akce_cas": time.time(),
    }


def _dalsi_kolo():
    hra = st.session_state.lov_barev
    hra["kola_zbyva"] -= 1
    if hra["kola_zbyva"] <= 0 or hra["zivoty"] <= 0:
        hra["aktivni"] = False
        hra["hotovo"] = True
    else:
        hra["cil"] = random.choice(MOZNOSTI)
    hra["posledni_akce_cas"] = time.time()
    st.session_state.lov_barev = hra


def vyhodnot(volba: str):
    hra = st.session_state.lov_barev
    if hra["hotovo"]:
        return

    if volba == hra["cil"]:
        hra["skore"] += 1
        hra["feedback"] = "Trefa! 🌈"
    else:
        hra["zivoty"] -= 1
        hra["feedback"] = "Ups, to nebyla hledaná barva."
    st.session_state.lov_barev = hra
    _dalsi_kolo()


def _zpracuj_timeout():
    hra = st.session_state.lov_barev
    if hra["hotovo"]:
        return
    if time.time() - hra.get("posledni_akce_cas", 0) < 2:
        return
    hra["feedback"] = "Barva se změnila. Bez ztráty života."
    st.session_state.lov_barev = hra
    _dalsi_kolo()


def render_hru():
    hra = st.session_state.get("lov_barev")
    if not hra:
        return

    st.subheader("🌈 Lov barev")
    st.caption("Po 2 sekundách se hledaná barva změní bez ztráty života.")
    _zpracuj_timeout()
    hra = st.session_state.get("lov_barev")
    if not hra:
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Skóre", hra["skore"])
    c2.metric("Životy", f"{'❤️' * max(hra['zivoty'], 0)}")
    c3.metric("Kola", f"{hra['kola_celkem'] - hra['kola_zbyva']}/{hra['kola_celkem']}")

    st.progress(
        (hra["kola_celkem"] - hra["kola_zbyva"]) / hra["kola_celkem"],
        text="Průběh hry",
    )

    st.markdown(f"<div class='word-box'>Najdi: <b>{hra['cil']}</b></div>", unsafe_allow_html=True)

    for i in range(0, len(MOZNOSTI), 3):
        cols = st.columns(3)
        for j, volba in enumerate(MOZNOSTI[i : i + 3]):
            if cols[j].button(volba, key=f"lov_{i}_{j}", use_container_width=True):
                vyhodnot(volba)
                st.rerun()

    if hra["feedback"]:
        if hra["feedback"].startswith("Trefa"):
            st.success(hra["feedback"])
        elif hra["feedback"].startswith("Barva se změnila"):
            st.info(hra["feedback"])
        else:
            st.error(hra["feedback"])

    if st.button("🛑 Konec hry", key="lov_stop", use_container_width=True):
        st.session_state.lov_barev = None
        st.rerun()


def render_vysledek():
    hra = st.session_state.get("lov_barev")
    if not hra or not hra.get("hotovo"):
        return

    st.header("🌈 Výsledek - Lov barev")
    st.write(f"Tvoje skóre: **{hra['skore']}**")
    uspesnost = round((hra["skore"] / max(hra["kola_celkem"], 1)) * 100, 1)
    st.write(f"Úspěšnost: **{uspesnost} %**")

    if uspesnost >= 70:
        st.success("Super postřeh! Barevný lov byl úspěšný.")
    else:
        st.info("Dobrá hra! Dej si ještě jedno kolo.")

    if st.button("🎯 Hrát znovu", key="lov_replay", use_container_width=True):
        spustit_hru(zivoty=hra["max_zivoty"], kola=hra["kola_celkem"])
        st.rerun()

    if st.button("⬅️ Zpět do miniher", key="lov_back", use_container_width=True):
        st.session_state.lov_barev = None
        st.rerun()

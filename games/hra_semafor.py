import random

import streamlit as st


BARVY = [
    ("🟢 ZELENÁ", "JEĎ"),
    ("🟡 ŽLUTÁ", "POZOR"),
    ("🔴 ČERVENÁ", "STŮJ"),
]


def spustit_hru(zivoty: int = 4, kola: int = 16):
    st.session_state.semafor = {
        "aktivni": True,
        "hotovo": False,
        "zivoty": zivoty,
        "max_zivoty": zivoty,
        "kola_zbyva": kola,
        "kola_celkem": kola,
        "skore": 0,
        "krok": random.choice(BARVY),
        "feedback": "",
    }


def _dalsi_kolo():
    hra = st.session_state.semafor
    hra["kola_zbyva"] -= 1
    if hra["kola_zbyva"] <= 0 or hra["zivoty"] <= 0:
        hra["aktivni"] = False
        hra["hotovo"] = True
    else:
        hra["krok"] = random.choice(BARVY)
    st.session_state.semafor = hra


def vyhodnot(akce: str):
    hra = st.session_state.semafor
    if hra["hotovo"]:
        return

    _, spravna_akce = hra["krok"]
    if akce == spravna_akce:
        hra["skore"] += 1
        hra["feedback"] = "Správně! 🚗"
    else:
        hra["zivoty"] -= 1
        hra["feedback"] = f"Ouha. Správně bylo: {spravna_akce}"
    st.session_state.semafor = hra
    _dalsi_kolo()


def render_hru():
    hra = st.session_state.get("semafor")
    if not hra:
        return

    st.header("🚦 Semafor sprint")
    st.write("Klikni na správnou akci podle barvy semaforu.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Skóre", hra["skore"])
    c2.metric("Životy", f"{'❤️' * max(hra['zivoty'], 0)}")
    c3.metric("Kola", f"{hra['kola_celkem'] - hra['kola_zbyva']}/{hra['kola_celkem']}")

    st.progress(
        (hra["kola_celkem"] - hra["kola_zbyva"]) / hra["kola_celkem"],
        text="Průběh hry",
    )

    barva, _ = hra["krok"]
    st.markdown(f"<div class='word-box'><b>{barva}</b></div>", unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    if a1.button("🏁 JEĎ", key="semafor_jed", use_container_width=True):
        vyhodnot("JEĎ")
        st.rerun()
    if a2.button("⚠️ POZOR", key="semafor_pozor", use_container_width=True):
        vyhodnot("POZOR")
        st.rerun()
    if a3.button("🛑 STŮJ", key="semafor_stuj", use_container_width=True):
        vyhodnot("STŮJ")
        st.rerun()

    if hra["feedback"]:
        if hra["feedback"].startswith("Správně"):
            st.success(hra["feedback"])
        else:
            st.error(hra["feedback"])

    if st.button("🛑 Konec hry", key="semafor_stop", use_container_width=True):
        st.session_state.semafor = None
        st.rerun()


def render_vysledek():
    hra = st.session_state.get("semafor")
    if not hra or not hra.get("hotovo"):
        return

    st.header("🚦 Výsledek - Semafor sprint")
    st.write(f"Tvoje skóre: **{hra['skore']}**")
    uspesnost = round((hra["skore"] / max(hra["kola_celkem"], 1)) * 100, 1)
    st.write(f"Úspěšnost: **{uspesnost} %**")

    if uspesnost >= 65:
        st.success("Paráda! Jízda byla bezpečná i rychlá.")
    else:
        st.info("To nevadí, dej si další sprint.")

    if st.button("🎯 Hrát znovu", key="semafor_replay", use_container_width=True):
        spustit_hru(zivoty=hra["max_zivoty"], kola=hra["kola_celkem"])
        st.rerun()

    if st.button("⬅️ Zpět do miniher", key="semafor_back", use_container_width=True):
        st.session_state.semafor = None
        st.rerun()

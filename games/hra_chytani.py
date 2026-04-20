import random

import streamlit as st


def spustit_hru(zivoty: int, kola: int):
    st.session_state.arcade = {
        "aktivni": True,
        "zivoty": zivoty,
        "max_zivoty": zivoty,
        "kola_zbyva": kola,
        "kola_celkem": kola,
        "skore": 0,
        "cil": random.randint(0, 8),
        "hotovo": False,
        "feedback": "",
    }


def _dalsi_kolo():
    hra = st.session_state.arcade
    hra["kola_zbyva"] -= 1
    if hra["kola_zbyva"] <= 0 or hra["zivoty"] <= 0:
        hra["hotovo"] = True
        hra["aktivni"] = False
    else:
        hra["cil"] = random.randint(0, 8)
    st.session_state.arcade = hra


def klik_policko(index: int):
    hra = st.session_state.arcade
    if hra["hotovo"]:
        return
    if index == hra["cil"]:
        hra["skore"] += 1
        hra["feedback"] = "Správně! ⭐"
    else:
        hra["zivoty"] -= 1
        hra["feedback"] = "Netrefa. Život ubývá jen za špatný klik."
    st.session_state.arcade = hra
    _dalsi_kolo()


def render_hru():
    hra = st.session_state.get("arcade")
    if not hra:
        return

    st.subheader("🕹️ Chytání hvězdiček")
    st.caption("Klikni na políčko se ⭐. Každý klik posune hru do dalšího kola.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Skóre", hra["skore"])
    c2.metric("Životy", f"{'❤️' * max(hra['zivoty'], 0)}")
    c3.metric("Kola", f"{hra['kola_celkem'] - hra['kola_zbyva']}/{hra['kola_celkem']}")

    st.progress(
        (hra["kola_celkem"] - hra["kola_zbyva"]) / hra["kola_celkem"],
        text="Průběh hry",
    )

    for radek in range(3):
        col1, col2, col3 = st.columns(3)
        sloupce = [col1, col2, col3]
        for sloupec in range(3):
            index = radek * 3 + sloupec
            popisek = "⭐" if index == hra["cil"] else "☁️"
            with sloupce[sloupec]:
                if st.button(popisek, key=f"arcade_{index}", use_container_width=True):
                    klik_policko(index)
                    st.rerun()

    if hra.get("feedback"):
        if hra["feedback"].startswith("Správně"):
            st.success(hra["feedback"])
        elif hra["feedback"].startswith("Hvězdička utekla"):
            st.info(hra["feedback"])
        else:
            st.error(hra["feedback"])

    if st.button("🛑 Konec hry", use_container_width=True):
        st.session_state.arcade = None
        st.rerun()


def render_vysledek():
    hra = st.session_state.get("arcade")
    if not hra or not hra.get("hotovo"):
        return

    st.header("🎮 Konec hry")
    st.write(f"Tvoje skóre: **{hra['skore']}**")
    uspesnost = round((hra["skore"] / max(hra["kola_celkem"], 1)) * 100, 1)
    st.write(f"Úspěšnost zásahů: **{uspesnost} %**")

    if uspesnost >= 60:
        st.success("Super! Tohle byla parádní jízda 🚀")
        st.balloons()
    else:
        st.info("Dobrá hra! Dej si další pokus a překonej své skóre.")

    if st.button("🎯 Hrát znovu", use_container_width=True):
        zivoty = hra["max_zivoty"]
        kola = hra["kola_celkem"]
        spustit_hru(zivoty=zivoty, kola=kola)
        st.rerun()

    if st.button("⬅️ Zpět do miniher", use_container_width=True):
        st.session_state.arcade = None
        st.rerun()

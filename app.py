import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st


SOUBOR_STATISTIK = Path("statistiky_vyjmenovana_slova.json")
PISMENA = ["Všechna", "B", "L", "M", "P", "S", "V", "Z"]

VYJMENOVANA = {
    "B": [
        "být",
        "bydlet",
        "obyvatel",
        "bydliště",
        "příbytek",
        "nábytek",
        "dobytek",
        "obyčej",
        "bystrý",
        "bylina",
        "kobyla",
        "býk",
        "babyka",
    ],
    "L": [
        "lyže",
        "lýtko",
        "lýko",
        "lýt",
        "lykat",
        "plynout",
        "plytký",
        "plyš",
        "plýtvat",
        "blýskat se",
        "polykat",
        "pelyněk",
    ],
    "M": [
        "my",
        "mýt",
        "mýlit se",
        "hmyz",
        "myš",
        "hlemýžď",
        "mýtit",
        "zamykat",
        "smýkat",
        "dmýchat",
        "chmýří",
        "nachomýtnout se",
    ],
    "P": [
        "pýcha",
        "pytel",
        "pysk",
        "pyl",
        "kopyto",
        "klopýtat",
        "třpytit se",
        "zpytovat",
        "pýřit se",
        "netopýr",
    ],
    "S": ["syn", "sytý", "sýr", "syrový", "sychravý", "usychat", "sýkora", "sýček", "syčet", "sypat"],
    "V": ["vy", "vysoký", "výt", "výskat", "zvykat", "žvýkat", "vydra", "vyžle", "povyk", "výr"],
    "Z": ["brzy", "jazyk", "nazývat (se)", "ozývat (se)", "Ruzyně"],
}

TEST_IY_PO_PISMENE = {
    "B": ["bydlet", "obyčej", "bystrý", "kobyla", "býk"],
    "L": ["lyže", "plynout", "plýtvat", "polykat"],
    "M": ["myš", "hmyz", "mýtit", "zamykat", "dmýchat"],
    "P": ["pytel", "pyl", "kopyto"],
    "S": ["syn", "sýkora", "syrový"],
    "V": ["vysoký", "vydra", "vyžle"],
    "Z": ["jazyk", "brzy"],
}

BEZNA_I_SLOVA = [
    "bílý",
    "pivo",
    "list",
    "mlít",
    "miska",
    "vidět",
    "zima",
    "silný",
    "pilot",
    "minuta",
    "divadlo",
    "kino",
    "pila",
]

NEVYJMENOVANA_POZNAVACKA = [
    "bílý",
    "milý",
    "kino",
    "pilot",
    "digitální",
    "minuta",
    "sirka",
    "divadlo",
    "list",
    "zima",
    "vidina",
    "pila",
    "sníh",
    "míč",
]


def maskuj_i_y(slovo: str):
    for i, ch in enumerate(slovo):
        if ch in "iíIÍ":
            return slovo[:i] + "_" + slovo[i + 1 :], "i"
        if ch in "yýYÝ":
            return slovo[:i] + "_" + slovo[i + 1 :], "y"
    return slovo, ""


def prazdne_statistiky():
    return {"celkem": 0, "spravne": 0, "spatne": 0, "historie": []}


def nacti_statistiky():
    if not SOUBOR_STATISTIK.exists():
        return prazdne_statistiky()
    try:
        with SOUBOR_STATISTIK.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return prazdne_statistiky()


def uloz_statistiky(data):
    with SOUBOR_STATISTIK.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pridej_vysledek(otazek, spravne, spatne, typ):
    data = nacti_statistiky()
    data["celkem"] += otazek
    data["spravne"] += spravne
    data["spatne"] += spatne
    uspesnost = round((spravne / otazek) * 100, 1) if otazek else 0.0
    data["historie"].append(
        {
            "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "typ": typ,
            "otazek": otazek,
            "spravne": spravne,
            "spatne": spatne,
            "uspesnost": uspesnost,
        }
    )
    data["historie"] = data["historie"][-30:]
    uloz_statistiky(data)


def init_state():
    if "sekce" not in st.session_state:
        st.session_state.sekce = "Domů"
    if "menu_sekce" not in st.session_state:
        st.session_state.menu_sekce = st.session_state.sekce
    if "test" not in st.session_state:
        st.session_state.test = None


def priprav_test_iy(vyber):
    if vyber == "Všechna":
        vyj_slova = [s for arr in TEST_IY_PO_PISMENE.values() for s in arr]
    else:
        vyj_slova = TEST_IY_PO_PISMENE.get(vyber, [])

    vyj_cast = [(s, "y") for s in vyj_slova]
    kolik_i = min(len(BEZNA_I_SLOVA), max(5, len(vyj_cast) // 2))
    i_cast = [(s, "i") for s in random.sample(BEZNA_I_SLOVA, k=kolik_i)]
    otazky = vyj_cast + i_cast
    random.shuffle(otazky)

    st.session_state.test = {
        "typ": "iy",
        "nazev": f"doplň i/y ({vyber})",
        "otazky": otazky[:20],
        "idx": 0,
        "spravne": 0,
        "spatne": 0,
        "feedback": "",
    }


def priprav_poznavacku(vyber):
    if vyber == "Všechna":
        vyj_slova = [s for arr in VYJMENOVANA.values() for s in arr]
    else:
        vyj_slova = VYJMENOVANA.get(vyber, [])

    vyj_k = min(14, len(vyj_slova))
    vyj_cast = random.sample(vyj_slova, k=vyj_k) if vyj_k > 0 else []
    nevyj_k = min(14, len(NEVYJMENOVANA_POZNAVACKA))
    nevyj_cast = random.sample(NEVYJMENOVANA_POZNAVACKA, k=nevyj_k)

    otazky = [(s, "V") for s in vyj_cast] + [(s, "N") for s in nevyj_cast]
    random.shuffle(otazky)

    st.session_state.test = {
        "typ": "poznavacka",
        "nazev": f"poznávačka ({vyber})",
        "otazky": otazky,
        "idx": 0,
        "spravne": 0,
        "spatne": 0,
        "feedback": "",
    }


def vyhodnot(odpoved):
    test = st.session_state.test
    slovo, spravna = test["otazky"][test["idx"]]
    if odpoved == spravna:
        test["spravne"] += 1
        test["feedback"] = "Správně!"
    else:
        test["spatne"] += 1
        if test["typ"] == "iy":
            test["feedback"] = f"Špatně. Správně je '{spravna}' -> {slovo}"
        elif spravna == "V":
            test["feedback"] = f"Špatně. '{slovo}' je vyjmenované/odvozené."
        else:
            test["feedback"] = f"Špatně. '{slovo}' není vyjmenované slovo."

    test["idx"] += 1
    st.session_state.test = test


def zprava_za_vysledek(uspesnost):
    if uspesnost >= 90:
        return "🌟 Jsi hvězda pravopisu! Jen tak dál!"
    if uspesnost >= 75:
        return "👏 Paráda! Ještě pár kol a bude to úplně top."
    return "💪 Nic se neděje, trénink dělá mistra. Zkus další kolo!"


def odznak_za_uspesnost(uspesnost):
    if uspesnost >= 90:
        return "🥇 Zlatý odznak"
    if uspesnost >= 75:
        return "🥈 Stříbrný odznak"
    return "🥉 Bronzový odznak"


def dnesni_skore():
    data = nacti_statistiky()
    dnes = datetime.now().strftime("%d.%m.%Y")
    denni = [z for z in data.get("historie", []) if str(z.get("datum", "")).startswith(dnes)]
    otazek = sum(int(z.get("otazek", 0)) for z in denni)
    spravne = sum(int(z.get("spravne", 0)) for z in denni)
    uspesnost = round((spravne / otazek) * 100, 1) if otazek else 0.0
    return {"pocet_testu": len(denni), "otazek": otazek, "spravne": spravne, "uspesnost": uspesnost}


def hvezdicky_za_spravne(pocet_spravnych):
    hvezdy = pocet_spravnych // 10
    dalsi_meta = 10 - (pocet_spravnych % 10)
    if dalsi_meta == 10:
        dalsi_meta = 0
    return hvezdy, dalsi_meta


def text_hvezdicek(pocet_hvezd):
    if pocet_hvezd <= 0:
        return "Zatím žádná hvězdička"
    max_zobrazit = min(pocet_hvezd, 10)
    text = "⭐" * max_zobrazit
    if pocet_hvezd > 10:
        text += f" +{pocet_hvezd - 10}"
    return text


def render_domu():
    st.markdown(
        """
        <div class="hero-box">
            <h1>🎒 Vyjmenovaná slova hrou</h1>
            <p>
                Vítej! Tady si procvičíš vyjmenovaná slova zábavně a bez stresu.
                Aplikace je připravená pro 2. a 3. třídu.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🧠 Co umím</h3>
                <p>
                    • Přehled vyjmenovaných slov<br>
                    • Cvičení Doplň i/y<br>
                    • Poznávačku slov<br>
                    • Statistiky tvého pokroku
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🚀 Jak začít</h3>
                <p>
                    1) Vyber v levém menu písmeno.<br>
                    2) Spusť test.<br>
                    3) Sbírej body a sleduj, jak se zlepšuješ!
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### ⚡ Rychlý start")
    s1, s2, s3 = st.columns(3)
    if s1.button("📝 Doplň i/y", use_container_width=True):
        priprav_test_iy("Všechna")
        st.session_state.sekce = "Test"
        st.session_state.menu_sekce = "Test"
        st.rerun()
    if s2.button("🔎 Poznávačka", use_container_width=True):
        priprav_poznavacku("Všechna")
        st.session_state.sekce = "Test"
        st.session_state.menu_sekce = "Test"
        st.rerun()
    if s3.button("📚 Přehled slov", use_container_width=True):
        st.session_state.sekce = "Přehled slov"
        st.session_state.menu_sekce = "Přehled slov"
        st.rerun()

    dnes = dnesni_skore()
    st.markdown("### 🗓️ Dnešní skóre")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Testů dnes", dnes["pocet_testu"])
    d2.metric("Otázek dnes", dnes["otazek"])
    d3.metric("Správně dnes", dnes["spravne"])
    d4.metric("Úspěšnost dnes", f"{dnes['uspesnost']} %")
    hvezdy, chybi = hvezdicky_za_spravne(dnes["spravne"])
    st.markdown(f"### ⭐ Hvězdičky dnes: {text_hvezdicek(hvezdy)}")
    if chybi > 0:
        st.caption(f"Do další hvězdičky chybí už jen {chybi} správných odpovědí.")
    else:
        st.caption("Skvělé! Zrovna jsi získal(a) další hvězdičku.")

    st.info("💡 Tip: Nejdřív otevři Přehled slov, pak spusť test.")


def render_prehled():
    st.header("📚 Přehled vyjmenovaných slov")
    for p in ["B", "L", "M", "P", "S", "V", "Z"]:
        st.markdown(
            f"""
            <div class="letter-card">
                <h3>Po {p}</h3>
                <p>{", ".join(VYJMENOVANA[p])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_test():
    test = st.session_state.test
    if not test:
        st.warning("Nejdřív spusť test v levém menu.")
        return

    if test["idx"] >= len(test["otazky"]):
        celkem = test["spravne"] + test["spatne"]
        uspesnost = round((test["spravne"] / celkem) * 100, 1) if celkem else 0.0
        pridej_vysledek(celkem, test["spravne"], test["spatne"], test["nazev"])

        st.header("🏁 Výsledek testu")
        c1, c2, c3 = st.columns(3)
        c1.metric("Otázek", celkem)
        c2.metric("Správně", test["spravne"])
        c3.metric("Úspěšnost", f"{uspesnost} %")
        st.markdown(f"### {odznak_za_uspesnost(uspesnost)}")
        st.success(zprava_za_vysledek(uspesnost))
        if st.button("Nová sada otázek"):
            st.session_state.test = None
            st.session_state.sekce = "Domů"
            st.session_state.menu_sekce = "Domů"
            st.rerun()
        return

    slovo, _ = test["otazky"][test["idx"]]
    progress = f"{test['idx'] + 1}/{len(test['otazky'])}"
    st.progress(test["idx"] / len(test["otazky"]), text=f"Průběh testu: {progress}")

    if test["typ"] == "iy":
        maska, _ = maskuj_i_y(slovo)
        st.header(f"📝 Doplň i/y ({progress})")
        st.markdown(f"<div class='word-box'>Slovo: <b>{maska}</b></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("🔵 i", use_container_width=True):
            vyhodnot("i")
            st.rerun()
        if c2.button("🟣 y", use_container_width=True):
            vyhodnot("y")
            st.rerun()
    else:
        st.header(f"🔎 Poznávačka ({progress})")
        st.markdown(f"<div class='word-box'>Slovo: <b>{slovo}</b></div>", unsafe_allow_html=True)
        st.write("Je to vyjmenované nebo odvozené slovo?")
        c1, c2 = st.columns(2)
        if c1.button("✅ V = vyjmenované", use_container_width=True):
            vyhodnot("V")
            st.rerun()
        if c2.button("❌ N = nevyjmenované", use_container_width=True):
            vyhodnot("N")
            st.rerun()

    if test["feedback"]:
        if test["feedback"].startswith("Správně"):
            st.success(test["feedback"])
        else:
            st.error(test["feedback"])


def render_statistiky():
    st.header("📊 Statistiky")
    data = nacti_statistiky()
    celkem = data.get("celkem", 0)
    spravne = data.get("spravne", 0)
    spatne = data.get("spatne", 0)
    usp = round((spravne / celkem) * 100, 1) if celkem else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Celkem otázek", celkem)
    c2.metric("Celkem správně", spravne)
    c3.metric("Úspěšnost", f"{usp} %")
    st.markdown(f"### Aktuální odznak: {odznak_za_uspesnost(usp)}")
    hvezdy_celkem, chybi_celkem = hvezdicky_za_spravne(spravne)
    st.markdown(f"### ⭐ Hvězdičky celkem: {text_hvezdicek(hvezdy_celkem)}")
    if chybi_celkem > 0:
        st.caption(f"Do další hvězdičky chybí {chybi_celkem} správných odpovědí.")
    else:
        st.caption("Paráda! Máš přesně hranici pro novou hvězdičku.")
    st.write(f"Celkem špatně: {spatne}")

    historie = list(reversed(data.get("historie", [])))
    if historie:
        st.dataframe(historie, use_container_width=True)
    else:
        st.info("Historie je zatím prázdná.")

    if st.button("Vymazat statistiky"):
        uloz_statistiky(prazdne_statistiky())
        st.success("Statistiky byly smazány.")
        st.rerun()

    if st.button("Začít nový test hned teď"):
        priprav_test_iy("Všechna")
        st.session_state.sekce = "Test"
        st.session_state.menu_sekce = "Test"
        st.rerun()


def nastav_vzhled():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f8fbff 0%, #edf8ff 45%, #fff9ef 100%);
        }
        .block-container {padding-top: 4.4rem; max-width: 1280px;}
        @media (max-width: 900px) {
            .block-container {padding-top: 5rem;}
        }
        h1, h2, h3 {font-weight: 800 !important;}
        h1 {font-size: 2.4rem !important;}
        h2 {font-size: 1.8rem !important;}
        p, li, label, .stMarkdown, .stAlert {font-size: 1.2rem !important; line-height: 1.5;}
        [data-testid="stSidebar"] * {font-size: 1.08rem !important;}
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #5f7cff 0%, #6c63ff 100%);
            color: white;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
            color: white !important;
        }
        .stButton > button {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            min-height: 3.3rem !important;
            border-radius: 14px !important;
            border: none !important;
            background: linear-gradient(90deg, #ff7eb6 0%, #ff9f5f 100%) !important;
            color: #14213d !important;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08) !important;
        }
        .stButton > button:hover {filter: brightness(1.05);}
        .stRadio label p {font-size: 1.18rem !important; font-weight: 600 !important;}
        .hero-box {
            background: linear-gradient(135deg, #6a89ff 0%, #ff7eb6 100%);
            color: white;
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            margin-bottom: 1rem;
        }
        .hero-box h1 {margin: 0 0 0.4rem 0; color: white;}
        .feature-card, .letter-card, .word-box {
            background: white;
            border: 2px solid #d8e3ff;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 6px 14px rgba(40, 62, 120, 0.08);
        }
        .word-box {
            font-size: 2rem;
            text-align: center;
            border: 3px solid #9ec5ff;
            background: #f4f9ff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    random.seed()
    st.set_page_config(page_title="Vyjmenovaná slova", page_icon="📘", layout="wide")
    init_state()
    nastav_vzhled()

    st.sidebar.title("🎯 Menu aplikace")
    sekce_options = ["Domů", "Přehled slov", "Statistiky", "Test"]
    if st.session_state.menu_sekce not in sekce_options:
        st.session_state.menu_sekce = "Domů"
    if st.session_state.sekce not in sekce_options:
        st.session_state.sekce = "Domů"

    st.sidebar.markdown("### 🎮 Spuštění testu")
    vyber = st.sidebar.selectbox("Písmeno pro test", PISMENA, index=0)
    if st.sidebar.button("Spustit test Doplň i/y", use_container_width=True):
        priprav_test_iy(vyber)
        st.session_state.sekce = "Test"
        st.session_state.menu_sekce = "Test"
        st.rerun()
    if st.sidebar.button("Spustit Poznávačku", use_container_width=True):
        priprav_poznavacku(vyber)
        st.session_state.sekce = "Test"
        st.session_state.menu_sekce = "Test"
        st.rerun()

    st.sidebar.radio("Sekce", sekce_options, key="menu_sekce")
    st.session_state.sekce = st.session_state.menu_sekce

    if st.session_state.sekce == "Domů":
        render_domu()
    elif st.session_state.sekce == "Přehled slov":
        render_prehled()
    elif st.session_state.sekce == "Statistiky":
        render_statistiky()
    else:
        if st.session_state.test is None:
            st.info("Zatím nemáš aktivní test. Spusť ho v levém panelu.")
        else:
            render_test()


if __name__ == "__main__":
    main()

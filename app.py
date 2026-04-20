import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st


SOUBOR_STATISTIK = Path("statistiky_vyjmenovana_slova.json")
PISMENA = ["Vsechna", "B", "L", "M", "P", "S", "V", "Z"]

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
        st.session_state.sekce = "Domu"
    if "test" not in st.session_state:
        st.session_state.test = None


def priprav_test_iy(vyber):
    if vyber == "Vsechna":
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
        "nazev": f"dopln i/y ({vyber})",
        "otazky": otazky[:20],
        "idx": 0,
        "spravne": 0,
        "spatne": 0,
        "feedback": "",
    }


def priprav_poznavacku(vyber):
    if vyber == "Vsechna":
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
        "nazev": f"poznavacka ({vyber})",
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
        test["feedback"] = "Spravne!"
    else:
        test["spatne"] += 1
        if test["typ"] == "iy":
            test["feedback"] = f"Spatne. Spravne je '{spravna}' -> {slovo}"
        elif spravna == "V":
            test["feedback"] = f"Spatne. '{slovo}' je vyjmenovane/odvozene."
        else:
            test["feedback"] = f"Spatne. '{slovo}' neni vyjmenovane slovo."

    test["idx"] += 1
    st.session_state.test = test


def render_domu():
    st.header("Vyjmenovana slova")
    st.write("Program pro vyuku vyjmenovanych slov.")
    st.markdown(
        "\n".join(
            [
                "- Prehled vyjmenovanych slov po B, L, M, P, S, V, Z",
                "- Cviceni Dopln i/y",
                "- Poznavacka: vyjmenovane vs. nevyjmenovane slovo",
                "- Ukladani vysledku (statistiky)",
            ]
        )
    )
    st.info("Tip: Nejdriv otevri Prehled slov, pak spust test.")


def render_prehled():
    st.header("Prehled vyjmenovanych slov")
    for p in ["B", "L", "M", "P", "S", "V", "Z"]:
        st.subheader(f"Po {p}")
        st.write(", ".join(VYJMENOVANA[p]))


def render_test():
    test = st.session_state.test
    if not test:
        st.warning("Nejdriv zaloz test.")
        return

    if test["idx"] >= len(test["otazky"]):
        celkem = test["spravne"] + test["spatne"]
        uspesnost = round((test["spravne"] / celkem) * 100, 1) if celkem else 0.0
        pridej_vysledek(celkem, test["spravne"], test["spatne"], test["nazev"])

        st.header("Vysledek testu")
        st.write(f"Otazek: {celkem}")
        st.write(f"Spravne: {test['spravne']}")
        st.write(f"Spatne: {test['spatne']}")
        st.write(f"Uspesnost: {uspesnost} %")
        st.success("Vyborne!" if uspesnost >= 85 else "Dobra prace, trenovat dal.")
        if st.button("Nova sada otazek"):
            st.session_state.test = None
            st.session_state.sekce = "Domu"
            st.rerun()
        return

    slovo, _ = test["otazky"][test["idx"]]
    progress = f"{test['idx'] + 1}/{len(test['otazky'])}"

    if test["typ"] == "iy":
        maska, _ = maskuj_i_y(slovo)
        st.header(f"Dopln i/y ({progress})")
        st.subheader(f"Slovo: {maska}")
        c1, c2 = st.columns(2)
        if c1.button("i", use_container_width=True):
            vyhodnot("i")
            st.rerun()
        if c2.button("y", use_container_width=True):
            vyhodnot("y")
            st.rerun()
    else:
        st.header(f"Poznavacka ({progress})")
        st.subheader(f"Slovo: {slovo}")
        st.write("Je to vyjmenovane/odvozene slovo?")
        c1, c2 = st.columns(2)
        if c1.button("V = vyjmenovane", use_container_width=True):
            vyhodnot("V")
            st.rerun()
        if c2.button("N = nevyjmenovane", use_container_width=True):
            vyhodnot("N")
            st.rerun()

    if test["feedback"]:
        if test["feedback"].startswith("Spravne"):
            st.success(test["feedback"])
        else:
            st.error(test["feedback"])


def render_statistiky():
    st.header("Statistiky")
    data = nacti_statistiky()
    celkem = data.get("celkem", 0)
    spravne = data.get("spravne", 0)
    spatne = data.get("spatne", 0)
    usp = round((spravne / celkem) * 100, 1) if celkem else 0.0

    st.write(f"Celkem otazek: {celkem}")
    st.write(f"Celkem spravne: {spravne}")
    st.write(f"Celkem spatne: {spatne}")
    st.write(f"Dlouhodoba uspesnost: {usp} %")

    historie = list(reversed(data.get("historie", [])))
    if historie:
        st.dataframe(historie, use_container_width=True)
    else:
        st.info("Historie je zatim prazdna.")

    if st.button("Vymazat statistiky"):
        uloz_statistiky(prazdne_statistiky())
        st.success("Statistiky byly smazany.")
        st.rerun()


def main():
    random.seed()
    st.set_page_config(page_title="Vyjmenovana slova", page_icon="📘", layout="centered")
    init_state()

    st.sidebar.title("Menu")
    sekce_options = ["Domu", "Prehled slov", "Statistiky", "Test"]
    if st.session_state.sekce not in sekce_options:
        st.session_state.sekce = "Domu"
    sekce_index = sekce_options.index(st.session_state.sekce)
    sekce = st.sidebar.radio("Sekce", sekce_options, index=sekce_index)
    st.session_state.sekce = sekce

    st.sidebar.divider()
    vyber = st.sidebar.selectbox("Pismeno pro test", PISMENA, index=0)
    if st.sidebar.button("Spustit test Dopln i/y", use_container_width=True):
        priprav_test_iy(vyber)
        st.session_state.sekce = "Test"
        st.rerun()
    if st.sidebar.button("Spustit Poznavacku", use_container_width=True):
        priprav_poznavacku(vyber)
        st.session_state.sekce = "Test"
        st.rerun()

    if st.session_state.sekce == "Domu":
        render_domu()
    elif st.session_state.sekce == "Prehled slov":
        render_prehled()
    elif st.session_state.sekce == "Statistiky":
        render_statistiky()
    else:
        if st.session_state.test is None:
            st.info("Zatim nemas aktivni test. Spust ho v levem panelu.")
        else:
            render_test()


if __name__ == "__main__":
    main()

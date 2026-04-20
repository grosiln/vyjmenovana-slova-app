import json
import random
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st
from games.hra_chytani import render_hru, render_vysledek, spustit_hru
from games.hra_lov_barev import (
    render_hru as render_hru_lov_barev,
    render_vysledek as render_vysledek_lov_barev,
    spustit_hru as spustit_hru_lov_barev,
)
from games.hra_semafor import (
    render_hru as render_hru_semafor,
    render_vysledek as render_vysledek_semafor,
    spustit_hru as spustit_hru_semafor,
)


SOUBOR_STATISTIK = Path("statistiky_vyjmenovana_slova.json")
SLOZKA_OBRAZKU_SLOVA = Path("assets/images/slova")
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

EMOJI_NAPOVEDA = {
    "býk": "🐂",
    "kobyla": "🐎",
    "lyže": "🎿",
    "myš": "🐭",
    "vydra": "🦦",
    "pytel": "🧺",
    "kopyto": "🐾",
    "sýkora": "🐦",
    "netopýr": "🦇",
    "hmyz": "🐞",
    "jazyk": "👅",
    "brzy": "⏰",
    "vysoký": "📏",
}


def maskuj_i_y(slovo: str):
    for i, ch in enumerate(slovo):
        if ch in "iíIÍ":
            return slovo[:i] + "_" + slovo[i + 1 :], "i"
        if ch in "yýYÝ":
            return slovo[:i] + "_" + slovo[i + 1 :], "y"
    return slovo, ""


def normalizuj_nazev_slova(slovo: str):
    zaklad = slovo.split(" (")[0].strip().lower()
    bez_dia = unicodedata.normalize("NFKD", zaklad).encode("ascii", "ignore").decode("ascii")
    bez_dia = bez_dia.replace(" ", "_").replace("-", "_")
    return "".join(ch for ch in bez_dia if ch.isalnum() or ch == "_")


def najdi_obrazek_ke_slovu(slovo: str):
    slug = normalizuj_nazev_slova(slovo)
    for pripona in (".png", ".jpg", ".jpeg", ".webp"):
        cesta = SLOZKA_OBRAZKU_SLOVA / f"{slug}{pripona}"
        if cesta.exists():
            return cesta
    return None


def prazdne_statistiky():
    return {"celkem": 0, "spravne": 0, "spatne": 0, "historie": []}


def nacti_statistiky():
    if not SOUBOR_STATISTIK.exists():
        data = prazdne_statistiky()
        data["hvezdy_utracene"] = 0
        return data
    try:
        with SOUBOR_STATISTIK.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if "hvezdy_utracene" not in data:
                data["hvezdy_utracene"] = 0
            return data
    except Exception:
        data = prazdne_statistiky()
        data["hvezdy_utracene"] = 0
        return data


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


def ziskane_hvezdy_celkem():
    data = nacti_statistiky()
    return data.get("spravne", 0) // 10


def dostupne_hvezdy():
    data = nacti_statistiky()
    ziskane = data.get("spravne", 0) // 10
    utracene = data.get("hvezdy_utracene", 0)
    return max(0, ziskane - utracene)


def utrat_hvezdy(pocet):
    data = nacti_statistiky()
    ziskane = data.get("spravne", 0) // 10
    utracene = data.get("hvezdy_utracene", 0)
    dostupne = max(0, ziskane - utracene)
    if dostupne < pocet:
        return False
    data["hvezdy_utracene"] = utracene + pocet
    uloz_statistiky(data)
    return True


def pridej_test_hvezdy(pocet_hvezd):
    """Navysi pocet spravnych odpovedi tak, aby pribyly hvezdicky pro testovani miniher."""
    if pocet_hvezd <= 0:
        return
    data = nacti_statistiky()
    data["spravne"] = data.get("spravne", 0) + (pocet_hvezd * 10)
    uloz_statistiky(data)


def vynuluj_utracene_hvezdy():
    data = nacti_statistiky()
    data["hvezdy_utracene"] = 0
    uloz_statistiky(data)


def init_state():
    if "sekce" not in st.session_state:
        st.session_state.sekce = "Domů"
    if "menu_sekce" not in st.session_state:
        st.session_state.menu_sekce = st.session_state.sekce
    if "menu_sekce_widget" not in st.session_state:
        st.session_state.menu_sekce_widget = st.session_state.menu_sekce
    if "test" not in st.session_state:
        st.session_state.test = None
    if "vyber_pismeno" not in st.session_state:
        st.session_state.vyber_pismeno = "Všechna"
    if "arcade" not in st.session_state:
        st.session_state.arcade = None
    if "semafor" not in st.session_state:
        st.session_state.semafor = None
    if "lov_barev" not in st.session_state:
        st.session_state.lov_barev = None


def nastav_sekci(cil):
    st.session_state.sekce = cil
    st.session_state.menu_sekce = cil
    st.session_state.menu_sekce_widget = cil


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


def vykresli_hvezdy(pocet_hvezd, max_hvezd=5):
    plne = "⭐" * min(pocet_hvezd, max_hvezd)
    prazdne = "☆" * max(0, max_hvezd - min(pocet_hvezd, max_hvezd))
    return f"{plne}{prazdne}"


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
        nastav_sekci("Test")
        st.rerun()
    if s2.button("🔎 Poznávačka", use_container_width=True):
        priprav_poznavacku("Všechna")
        nastav_sekci("Test")
        st.rerun()
    if s3.button("📚 Přehled slov", use_container_width=True):
        nastav_sekci("Přehled slov")
        st.rerun()

    st.info("💡 Tip: Nejdřív otevři Přehled slov, pak spusť test.")


def render_prehled():
    st.header("📚 Přehled vyjmenovaných slov")
    st.info("Vyber písmeno, přečti si slova a hned si je můžeš procvičit.")
    for p in ["B", "L", "M", "P", "S", "V", "Z"]:
        slova = VYJMENOVANA[p]
        pocet = len(slova)
        st.markdown(
            f"""
            <div class="letter-card">
                <h3>Po {p}</h3>
                <p><b>Počet slov:</b> {pocet}</p>
                <p>{", ".join(slova)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        if c1.button(f"📝 Trénovat i/y po {p}", key=f"iy_{p}", use_container_width=True):
            priprav_test_iy(p)
            nastav_sekci("Test")
            st.rerun()
        if c2.button(f"🔎 Poznávačka po {p}", key=f"pozn_{p}", use_container_width=True):
            priprav_poznavacku(p)
            nastav_sekci("Test")
            st.rerun()


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
            nastav_sekci("Domů")
            st.rerun()
        return

    slovo, _ = test["otazky"][test["idx"]]
    progress = f"{test['idx'] + 1}/{len(test['otazky'])}"
    st.progress(test["idx"] / len(test["otazky"]), text=f"Průběh testu: {progress}")

    if test["typ"] == "iy":
        maska, _ = maskuj_i_y(slovo)
        st.header(f"📝 Doplň i/y ({progress})")
        obrazek = najdi_obrazek_ke_slovu(slovo)
        emoji = EMOJI_NAPOVEDA.get(slovo, "🧩")
        cword, cimg = st.columns([2, 1])
        with cword:
            st.markdown(f"<div class='word-box'>Slovo: <b>{maska}</b></div>", unsafe_allow_html=True)
        with cimg:
            if obrazek:
                st.image(str(obrazek), use_container_width=True)
                st.caption("Obrázková nápověda")
            else:
                st.markdown(
                    f"<div class='hint-emoji-box'>{emoji}</div>",
                    unsafe_allow_html=True,
                )
                st.caption("Vizuální nápověda (obrázek se připravuje)")
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
    st.markdown(f"### ⭐ Celkem: {text_hvezdicek(hvezdy_celkem)}")
    st.markdown(
        f"""
        <div class="star-counter-box">
            <div class="star-label">⭐ Dostupné pro minihry</div>
            <div class="star-number">{dostupne_hvezdy()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        nastav_sekci("Test")
        st.rerun()


def render_minihry():
    arcade_aktivni = bool(st.session_state.arcade and st.session_state.arcade.get("aktivni"))
    semafor_aktivni = bool(st.session_state.semafor and st.session_state.semafor.get("aktivni"))
    lov_aktivni = bool(st.session_state.lov_barev and st.session_state.lov_barev.get("aktivni"))
    if not (arcade_aktivni or semafor_aktivni or lov_aktivni):
        st.header("🎮 Minihry - odměna")
        st.write("Tady se už neučíš. Tady si jen hraješ.")

        ziskane = ziskane_hvezdy_celkem()
        dostupne = dostupne_hvezdy()
        st.markdown(
            f"""
            <div class="star-row">
                <div class="star-counter-box">
                    <div class="star-label">⭐ Získané celkem</div>
                    <div class="star-number">{ziskane}</div>
                </div>
                <div class="star-counter-box">
                    <div class="star-label">⭐ Dostupné teď</div>
                    <div class="star-number">{dostupne}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("🧪 Testovací hvězdičky (pro vývoj)", expanded=False):
            st.caption("Rychlé přidání hvězdiček jen pro test miniher.")
            t1, t2, t3 = st.columns(3)
            if t1.button("+5 ⭐", key="test_plus_5", use_container_width=True):
                pridej_test_hvezdy(5)
                st.success("Přidáno 5 hvězdiček pro testování.")
                st.rerun()
            if t2.button("+20 ⭐", key="test_plus_20", use_container_width=True):
                pridej_test_hvezdy(20)
                st.success("Přidáno 20 hvězdiček pro testování.")
                st.rerun()
            if t3.button("Obnovit utracené", key="test_reset_spent", use_container_width=True):
                vynuluj_utracene_hvezdy()
                st.success("Utracené hvězdičky byly vynulovány.")
                st.rerun()

    if st.session_state.arcade and st.session_state.arcade.get("hotovo"):
        render_vysledek()
        return

    if st.session_state.arcade and st.session_state.arcade.get("aktivni"):
        render_hru()
        return

    if st.session_state.semafor and st.session_state.semafor.get("hotovo"):
        render_vysledek_semafor()
        return

    if st.session_state.semafor and st.session_state.semafor.get("aktivni"):
        render_hru_semafor()
        return

    if st.session_state.lov_barev and st.session_state.lov_barev.get("hotovo"):
        render_vysledek_lov_barev()
        return

    if st.session_state.lov_barev and st.session_state.lov_barev.get("aktivni"):
        render_hru_lov_barev()
        return

    st.markdown("### Vyber minihru")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🕹️ Chytání hvězdiček</h3>
                <p>Chytej hvězdu v mřížce.<br>Cena: ⭐⭐⭐<br>Životy: ❤️❤️❤️<br>Kola: 18</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Hrát: Chytání hvězdiček (3 ⭐)", key="menu_chytani", use_container_width=True):
            if utrat_hvezdy(3):
                st.session_state.semafor = None
                st.session_state.lov_barev = None
                spustit_hru(zivoty=3, kola=18)
                st.rerun()
            st.error("Nemáš dost hvězdiček.")

    with r2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🚦 Semafor sprint</h3>
                <p>Reaguj na barvy semaforu.<br>Cena: ⭐⭐⭐⭐<br>Životy: ❤️❤️❤️❤️<br>Kola: 16</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Hrát: Semafor sprint (4 ⭐)", key="menu_semafor", use_container_width=True):
            if utrat_hvezdy(4):
                st.session_state.arcade = None
                st.session_state.lov_barev = None
                spustit_hru_semafor(zivoty=4, kola=16)
                st.rerun()
            st.error("Nemáš dost hvězdiček.")

    with r3:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🌈 Lov barev</h3>
                <p>Najdi správnou barvu.<br>Cena: ⭐⭐⭐⭐⭐<br>Životy: ❤️❤️❤️❤️❤️<br>Kola: 20</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Hrát: Lov barev (5 ⭐)", key="menu_lov_barev", use_container_width=True):
            if utrat_hvezdy(5):
                st.session_state.arcade = None
                st.session_state.semafor = None
                spustit_hru_lov_barev(zivoty=5, kola=20)
                st.rerun()
            st.error("Nemáš dost hvězdiček.")

    st.info("Hry jsou odměna za trénink. Za každých 10 správných odpovědí získáš 1 hvězdičku.")


def render_dnesni_skore():
    st.header("🗓️ Dnešní skóre")
    dnes = dnesni_skore()

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

    c1, c2 = st.columns(2)
    if c1.button("📝 Spustit Doplň i/y", use_container_width=True):
        priprav_test_iy("Všechna")
        nastav_sekci("Test")
        st.rerun()
    if c2.button("🔎 Spustit Poznávačku", use_container_width=True):
        priprav_poznavacku("Všechna")
        nastav_sekci("Test")
        st.rerun()


def nastav_vzhled():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f8fbff 0%, #edf8ff 45%, #fff9ef 100%);
        }
        /* Globalni reset layoutu - zabrani useknuti obsahu */
        html, body, .stApp {
            height: auto !important;
            min-height: 100% !important;
            overflow-y: auto !important;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] .main,
        section.main {
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
            min-height: 100vh !important;
        }
        [data-testid="stAppViewContainer"] .main {
            overflow-y: auto !important;
        }
        [data-testid="stAppViewContainer"] .block-container {
            padding-bottom: 2rem !important;
        }
        /* Po navratu z miniher zajisti zobrazeni standardniho rozhrani */
        [data-testid="stSidebar"], [data-testid="collapsedControl"], header[data-testid="stHeader"] {
            display: initial !important;
        }
        .block-container {padding-top: 1.2rem; max-width: 1280px; padding-left: 1.4rem; padding-right: 1.4rem;}
        h1, h2, h3 {font-weight: 800 !important;}
        h1 {font-size: clamp(1.7rem, 2.6vw, 2.45rem) !important;}
        h2 {font-size: clamp(1.45rem, 2.2vw, 1.9rem) !important;}
        p, li, label, .stMarkdown, .stAlert {font-size: clamp(1rem, 1.3vw, 1.2rem) !important; line-height: 1.5;}
        /* Ochrana proti orezani diakritiky (hacky/carky) */
        h1, h2, h3 {
            overflow: visible !important;
            line-height: 1.2 !important;
            padding-top: 0.04em;
            text-rendering: geometricPrecision;
        }
        p, li, label, .stMarkdown p, .stMarkdown li, .stAlert p {
            overflow: visible !important;
            line-height: 1.45 !important;
            text-rendering: geometricPrecision;
        }
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {
            overflow: visible !important;
        }
        [data-testid="stSidebar"] * {font-size: clamp(1rem, 1.1vw, 1.08rem) !important;}
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #5f7cff 0%, #6c63ff 100%);
            color: white;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
            color: white !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #1f2937 !important;
        }
        .stButton > button {
            font-size: clamp(1.05rem, 1.7vw, 1.35rem) !important;
            font-weight: 700 !important;
            min-height: clamp(2.35rem, 5.4vh, 2.9rem) !important;
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
        .star-row {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin-bottom: 0.9rem;
        }
        .star-counter-box {
            background: linear-gradient(135deg, #fff7d1 0%, #ffe9a3 100%);
            border: 2px solid #ffd76a;
            border-radius: 16px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 6px 14px rgba(120, 96, 20, 0.1);
        }
        .star-label {
            font-size: clamp(1rem, 1.3vw, 1.22rem);
            font-weight: 800;
            color: #5b4600;
            margin-bottom: 0.2rem;
        }
        .star-number {
            font-size: clamp(1.9rem, 3.6vw, 2.7rem);
            font-weight: 900;
            color: #3f2f00;
            line-height: 1.05;
        }
        .word-box {
            font-size: clamp(1.45rem, 3.4vw, 2.1rem);
            text-align: center;
            border: 3px solid #9ec5ff;
            background: #f4f9ff;
        }
        .hint-emoji-box {
            font-size: clamp(2.2rem, 5vw, 3.4rem);
            text-align: center;
            background: linear-gradient(135deg, #fff8dd 0%, #ffeeb1 100%);
            border: 2px solid #ffd97a;
            border-radius: 14px;
            padding: 0.6rem;
            min-height: 84px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        /* Tablet */
        @media (max-width: 1024px) {
            .block-container {
                padding-top: 0.95rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .feature-card, .letter-card, .word-box {
                border-radius: 14px;
                padding: 0.8rem 0.85rem;
            }
        }
        /* Mobil */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 0.75rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }
            [data-testid="stSidebar"] {
                min-width: 78vw !important;
                max-width: 82vw !important;
            }
            .stButton > button {
                min-height: 3.2rem !important;
                border-radius: 12px !important;
            }
            .hero-box {padding: 0.9rem 1rem;}
            .star-row {grid-template-columns: 1fr;}
            .word-box {
                border-width: 2px;
                border-radius: 12px;
                padding: 0.6rem 0.5rem;
            }
        }
        /* Velmi malé displeje */
        @media (max-width: 480px) {
            .block-container {
                padding-top: 0.6rem;
                padding-left: 0.55rem;
                padding-right: 0.55rem;
            }
            h1 {letter-spacing: 0.1px;}
            .hero-box, .feature-card, .letter-card, .word-box {
                margin-bottom: 0.55rem;
            }
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
    sekce_options = ["Domů", "Dnešní skóre", "Přehled slov", "Statistiky", "Test", "Minihry"]
    if st.session_state.menu_sekce not in sekce_options:
        nastav_sekci("Domů")
    if st.session_state.sekce not in sekce_options:
        nastav_sekci("Domů")
    if st.session_state.menu_sekce_widget not in sekce_options:
        st.session_state.menu_sekce_widget = st.session_state.menu_sekce

    st.sidebar.markdown("### 🎮 Spuštění testu")
    vyber = st.sidebar.selectbox("Písmeno pro test", PISMENA, key="vyber_pismeno")
    if st.sidebar.button("Spustit test Doplň i/y", use_container_width=True):
        priprav_test_iy(vyber)
        nastav_sekci("Test")
        st.rerun()
    if st.sidebar.button("Spustit Poznávačku", use_container_width=True):
        priprav_poznavacku(vyber)
        nastav_sekci("Test")
        st.rerun()

    st.sidebar.radio("Sekce", sekce_options, key="menu_sekce_widget")
    st.session_state.menu_sekce = st.session_state.menu_sekce_widget
    st.session_state.sekce = st.session_state.menu_sekce

    if st.session_state.sekce == "Domů":
        render_domu()
    elif st.session_state.sekce == "Dnešní skóre":
        render_dnesni_skore()
    elif st.session_state.sekce == "Přehled slov":
        render_prehled()
    elif st.session_state.sekce == "Statistiky":
        render_statistiky()
    elif st.session_state.sekce == "Minihry":
        render_minihry()
    else:
        if st.session_state.test is None:
            st.info("Zatím nemáš aktivní test. Spusť ho tady nebo v levém panelu.")
            c1, c2 = st.columns(2)
            if c1.button("📝 Spustit Doplň i/y", key="test_empty_iy", use_container_width=True):
                priprav_test_iy(st.session_state.vyber_pismeno)
                nastav_sekci("Test")
                st.rerun()
            if c2.button("🔎 Spustit Poznávačku", key="test_empty_pozn", use_container_width=True):
                priprav_poznavacku(st.session_state.vyber_pismeno)
                nastav_sekci("Test")
                st.rerun()
        else:
            render_test()


if __name__ == "__main__":
    main()

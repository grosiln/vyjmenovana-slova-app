import json
import random
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st
from games.hra_space_invaders import (
    render_hru as render_hru_space,
    spustit_hru as spustit_hru_space,
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


MAX_JMENO_ZEBRICEK = 12
LIMIT_ZEBRICKU = 10

# Zaznam her, ktere maji svuj zebricek. Dalsi hry staci pridat sem,
# render_zebricek() je automaticky zobrazi jako zalozky.
HRY_SE_ZEBRICKEM = [
    {"klic": "space", "nazev": "👾 Space Invaders"},
    # Pripraveno pro dalsi dve hry, az je dopiseme:
    # {"klic": "hra2", "nazev": "..."},
    # {"klic": "hra3", "nazev": "..."},
]


def ziskej_zebricek(hra="space"):
    data = nacti_statistiky()
    zeb = data.get(f"zebricek_{hra}", [])
    zeb = sorted(zeb, key=lambda z: (-int(z.get("skore", 0)), z.get("datum", "")))
    return zeb[:LIMIT_ZEBRICKU]


def patri_do_zebricku(skore, hra="space"):
    if skore <= 0:
        return False
    zeb = ziskej_zebricek(hra)
    if len(zeb) < LIMIT_ZEBRICKU:
        return True
    nejhorsi = min(int(z.get("skore", 0)) for z in zeb)
    return skore > nejhorsi


def zapis_do_zebricku(jmeno, skore, hvezdy, hra="space"):
    jmeno_cist = (jmeno or "").strip()[:MAX_JMENO_ZEBRICEK] or "Anonym"
    data = nacti_statistiky()
    klic = f"zebricek_{hra}"
    zeb = list(data.get(klic, []))
    zeb.append(
        {
            "jmeno": jmeno_cist,
            "skore": int(skore),
            "hvezdy": int(hvezdy),
            "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
    )
    zeb.sort(key=lambda z: (-int(z.get("skore", 0)), z.get("datum", "")))
    data[klic] = zeb[:LIMIT_ZEBRICKU]
    uloz_statistiky(data)
    return jmeno_cist


def vymaz_zebricek(hra="space"):
    data = nacti_statistiky()
    data[f"zebricek_{hra}"] = []
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
    if "space_invaders" not in st.session_state:
        st.session_state.space_invaders = None
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
    if st.session_state.space_invaders and st.session_state.space_invaders.get("aktivni"):
        render_hru_space()
        return

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

    st.markdown("### Vyber minihru")
    st.markdown(
        """
        <div class="feature-card">
            <h3>👾 Space Invaders</h3>
            <p>
                Jednoduchá klasika - ovládej raketku šipkami a stříle mezerníkem.<br>
                Ničte mimozemšťany a sestřelujte padající hvězdičky jako bonus.<br>
                Cena: ⭐⭐⭐
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Hrát: Space Invaders (3 ⭐)", key="menu_space", use_container_width=True):
        if utrat_hvezdy(3):
            spustit_hru_space()
            st.rerun()
        else:
            st.error("Nemáš dost hvězdiček.")

    st.info("Hry jsou odměna za trénink. Za každých 10 správných odpovědí získáš 1 hvězdičku.")


def _render_tabulka_zebricku(klic_hry, nazev_hry):
    zebricek = ziskej_zebricek(klic_hry)
    st.markdown(f"#### {nazev_hry} — TOP {LIMIT_ZEBRICKU}")

    if not zebricek:
        st.info("Zatím nikdo není v žebříčku této hry.")
    else:
        radky = ""
        for i, z in enumerate(zebricek, start=1):
            if i == 1:
                medaile = "🥇"
            elif i == 2:
                medaile = "🥈"
            elif i == 3:
                medaile = "🥉"
            else:
                medaile = f"{i}."
            jmeno = str(z.get("jmeno", "?"))[:MAX_JMENO_ZEBRICEK]
            skore = int(z.get("skore", 0))
            hvezdy = int(z.get("hvezdy", 0))
            datum = str(z.get("datum", ""))
            radky += f"""
                <div class="lb-row lb-rank-{i}">
                    <div class="lb-rank">{medaile}</div>
                    <div class="lb-name">{jmeno}</div>
                    <div class="lb-score">{skore} b.</div>
                    <div class="lb-stars">⭐ {hvezdy}</div>
                    <div class="lb-date">{datum}</div>
                </div>
            """

        st.markdown(
            f"""
            <div class="lb-wrap">
                <div class="lb-head">
                    <div class="lb-rank">#</div>
                    <div class="lb-name">Jméno</div>
                    <div class="lb-score">Skóre</div>
                    <div class="lb-stars">Hvězdy</div>
                    <div class="lb-date">Datum</div>
                </div>
                {radky}
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_zebricek():
    st.header("🏆 Žebříček miniher")
    st.caption("Hru pustíš přes levé menu → Minihry.")

    if not HRY_SE_ZEBRICKEM:
        st.info("Zatím není žádná hra.")
        return

    if len(HRY_SE_ZEBRICKEM) == 1:
        hra = HRY_SE_ZEBRICKEM[0]
        _render_tabulka_zebricku(hra["klic"], hra["nazev"])
    else:
        nazvy = [h["nazev"] for h in HRY_SE_ZEBRICKEM]
        zalozky = st.tabs(nazvy)
        for zalozka, hra in zip(zalozky, HRY_SE_ZEBRICKEM):
            with zalozka:
                _render_tabulka_zebricku(hra["klic"], hra["nazev"])


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
        .block-container {padding-top: 1.6rem; max-width: 1280px; padding-left: 1.4rem; padding-right: 1.4rem;}
        /* Nadpisy s dostatkem mista pro ceskou diakritiku (hacky, carky) */
        h1, h2, h3, h4 {
            font-weight: 800 !important;
            line-height: 1.5 !important;
            padding-top: 0.25em !important;
            padding-bottom: 0.1em !important;
            margin-top: 0.35em !important;
            overflow: visible !important;
        }
        h1 {font-size: clamp(1.7rem, 2.6vw, 2.45rem) !important;}
        h2 {font-size: clamp(1.45rem, 2.2vw, 1.9rem) !important;}
        h3 {font-size: clamp(1.2rem, 1.8vw, 1.55rem) !important;}
        p, li, label, .stMarkdown, .stAlert {
            font-size: clamp(1rem, 1.3vw, 1.2rem) !important;
            line-height: 1.6 !important;
        }
        /* Prvni nadpis v kontejneru nepotrebuje margin nahoru */
        .block-container h1:first-child,
        .block-container h2:first-child,
        .block-container h3:first-child {
            margin-top: 0 !important;
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
            padding: 1.5rem 1.4rem 1.2rem 1.4rem;
            border-radius: 18px;
            margin-bottom: 1rem;
        }
        .hero-box h1 {
            margin: 0 0 0.4rem 0 !important;
            padding-top: 0.15em !important;
            color: white;
            line-height: 1.4 !important;
        }
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
            line-height: 1.5 !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
        .lb-wrap {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
            margin: 0.6rem 0 1rem 0;
        }
        .lb-head, .lb-row {
            display: grid;
            grid-template-columns: 56px 1fr 110px 90px 150px;
            align-items: center;
            gap: 0.6rem;
            padding: 0.55rem 0.85rem;
            border-radius: 12px;
            background: white;
            border: 2px solid #d8e3ff;
            box-shadow: 0 4px 10px rgba(40, 62, 120, 0.06);
            font-size: clamp(0.98rem, 1.25vw, 1.15rem);
        }
        .lb-head {
            background: #eef3ff;
            font-weight: 800;
            color: #334;
            border-color: #b8c9ff;
        }
        .lb-row .lb-rank {font-size: 1.35rem; font-weight: 900; text-align: center;}
        .lb-row .lb-name {font-weight: 800; color: #1f2640; word-break: break-word;}
        .lb-row .lb-score {font-weight: 800; color: #2e7d32; text-align: right;}
        .lb-row .lb-stars {font-weight: 700; color: #8a6d00; text-align: right;}
        .lb-row .lb-date {color: #556; font-size: 0.92em; text-align: right;}
        .lb-rank-1 {background: linear-gradient(90deg,#fff5cc 0%,#ffe17a 100%); border-color:#e8b800;}
        .lb-rank-2 {background: linear-gradient(90deg,#f1f3f7 0%,#d2d8e0 100%); border-color:#9aa3b0;}
        .lb-rank-3 {background: linear-gradient(90deg,#ffe4cf 0%,#ffbe8a 100%); border-color:#cf7b3a;}
        @media (max-width: 768px) {
            .lb-head, .lb-row {
                grid-template-columns: 42px 1fr 70px 60px;
                gap: 0.4rem;
                padding: 0.5rem 0.6rem;
                font-size: 0.95rem;
            }
            .lb-head .lb-date, .lb-row .lb-date { display: none; }
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


def zpracuj_query_params():
    """Zpracuje navrat z miniher (iframe ulozi skore pres URL).

    Pravidlo: pokud score patri do TOP 10 -> zobraz formular pro jmeno.
    Pokud nepatri -> skoc rovnou do vyberu miniher (bez mezistepu).
    """
    params = st.query_params
    if params.get("si_finished") != "1":
        return
    # Pokud uz mame koncovou obrazovku nastavenou (napr. po rerun),
    # jen vycisti URL a nech stavajici state byt.
    existing = st.session_state.get("space_invaders")
    if existing and existing.get("koncova_obrazovka"):
        try:
            st.query_params.clear()
        except Exception:
            pass
        return
    try:
        skore = int(params.get("si_score", "0"))
    except (TypeError, ValueError):
        skore = 0
    try:
        hvezdy = int(params.get("si_stars", "0"))
    except (TypeError, ValueError):
        hvezdy = 0
    vyhra = params.get("si_won") == "1"

    if patri_do_zebricku(skore, "space"):
        st.session_state.space_invaders = {
            "aktivni": True,
            "start_potvrzen": True,
            "koncova_obrazovka": True,
            "skore": skore,
            "hvezdy": hvezdy,
            "vyhra": vyhra,
            "ulozeno": False,
            "jmeno_ulozene": "",
        }
    else:
        st.session_state.space_invaders = None

    nastav_sekci("Minihry")
    try:
        st.query_params.clear()
    except Exception:
        pass


def main():
    random.seed()
    st.set_page_config(page_title="Vyjmenovaná slova", page_icon="📘", layout="wide")
    init_state()
    nastav_vzhled()
    zpracuj_query_params()

    st.sidebar.title("🎯 Menu aplikace")
    sekce_options = [
        "Domů",
        "Dnešní skóre",
        "Přehled slov",
        "Statistiky",
        "Test",
        "Minihry",
        "Žebříček miniher",
    ]
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

    if st.session_state.sekce != "Minihry" and st.session_state.space_invaders:
        st.session_state.space_invaders = None

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
    elif st.session_state.sekce == "Žebříček miniher":
        render_zebricek()
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

import base64
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import streamlit as st
from database import rechercher_logements_db, verifier_coherence_schema
from llm_pipeline import extraire_criteres_depuis_texte

load_dotenv()

# Configuration de la page en mode Wide
st.set_page_config(
    page_title="Trouve-moi un logement - Casablanca",
    page_icon="🏠",
    layout="wide"
)


def html(s: str) -> str:
    """
    Aplatit un bloc HTML : supprime l'indentation et les lignes vides.
    Indispensable avec st.markdown : une ligne vide termine le bloc HTML,
    et toute ligne indentée de 4 espaces ensuite est rendue comme du CODE
    (c'était la cause du titre/sous-titre qui ne s'affichaient pas).
    """
    return " ".join(line.strip() for line in s.splitlines() if line.strip())


# CSS pur pour un Hero Full Width End-to-End unifié
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

<style>
    /* =========================================
       1. STREAMLIT GLOBAL LAYOUT
    ========================================= */

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
    }

    [data-testid="stAppViewContainer"] {
        overflow-x: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }

    /* =========================================
       2. FULL-SCREEN HERO VIDEO
    ========================================= */

    .hero-container {
        position: relative;
        width: 100%;
        height: 100vh;
        height: 100svh;
        min-height: 650px;

        overflow: hidden;
        margin: 0;
        padding: 0;
    }

    .hero-video {
        position: absolute;
        top: 0;
        left: 0;

        width: 100%;
        height: 100%;

        object-fit: cover;
        object-position: center center;

        z-index: 1;
    }

    /* Dark overlay for readability */

    .hero-overlay {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;

        background: linear-gradient(
            180deg,
            rgba(5,7,10,0.30) 0%,
            rgba(5,7,10,0.30) 40%,
            rgba(5,7,10,0.65) 75%,
            rgba(5,7,10,0.85) 100%
        );

        z-index: 2;
    }

    /* =========================================
       3. HERO TITLE AND SUBTITLE (above the search bar)
    ========================================= */

    .hero-content {
        position: absolute;

        top: 22%;
        left: 50%;
        transform: translateX(-50%);

        z-index: 3;

        text-align: center;

        width: 100%;
        max-width: 950px;

        padding: 0 1.5rem;
        box-sizing: border-box;
    }

    .hero-title {
        font-size: clamp(2.5rem, 5vw, 4.5rem);
        font-weight: 800;

        color: #ffffff;

        letter-spacing: -0.045em;
        line-height: 1.1;

        margin-bottom: 0.8rem;

        text-shadow: 0 4px 25px rgba(0,0,0,0.8);
    }

    .hero-subtitle {
        color: #f0f3f6;

        font-size: clamp(1rem, 2vw, 1.3rem);
        font-weight: 400;

        line-height: 1.6;

        margin-bottom: 0;

        text-shadow: 0 2px 12px rgba(0,0,0,0.8);
    }

    /* =========================================
       4. SEARCH BAR OVER THE VIDEO
    ========================================= */

    .st-key-hero_search {
        position: relative;
        z-index: 10;

        width: calc(100% - 40px);
        max-width: 800px;

        margin: -190px auto 0 !important;
        padding: 0 !important;
    }

    /* Search input */

    .st-key-hero_search .stTextInput {
        width: 100%;
    }

    .st-key-hero_search .stTextInput input {
        background: rgba(15, 20, 28, 0.82) !important;

        color: #ffffff !important;

        border: 1px solid rgba(255,255,255,0.45) !important;
        border-radius: 14px !important;

        padding: 1rem 1.3rem !important;

        font-size: 1.05rem !important;

        min-height: 58px;

        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);

        box-shadow: 0 10px 35px rgba(0,0,0,0.4);
    }

    .st-key-hero_search .stTextInput input::placeholder {
        color: rgba(255,255,255,0.75) !important;
    }

    .st-key-hero_search .stTextInput input:focus {
        border-color: #ffffff !important;

        box-shadow: 0 0 20px rgba(255,255,255,0.2) !important;
    }

    /* =========================================
       5. SUGGESTED SEARCH BUTTONS
    ========================================= */

    .st-key-hero_search .stButton button {
        background: rgba(20,25,32,0.78) !important;

        color: #ffffff !important;

        border: 1px solid rgba(255,255,255,0.28) !important;
        border-radius: 10px !important;

        font-size: 0.85rem !important;
        font-weight: 600 !important;

        min-height: 44px;

        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);

        transition: all 0.25s ease !important;
    }

    .st-key-hero_search .stButton button:hover {
        background: rgba(255,255,255,0.20) !important;

        border-color: #ffffff !important;

        color: #ffffff !important;

        transform: translateY(-2px);
    }

    /* =========================================
       6. MAIN RESULTS SECTION
    ========================================= */

    .main-content {
        max-width: 1300px;

        margin: 0 auto;

        padding: 0 2rem;
    }

    /* =========================================
       7. ACCOMMODATION CARDS
    ========================================= */

    .nomad-card {
        position: relative;

        height: 350px;

        border-radius: 16px;
        overflow: hidden;

        margin-bottom: 1.5rem;

        box-shadow: 0 8px 25px rgba(0,0,0,0.5);

        border: 1px solid rgba(255,255,255,0.1);

        transition:
            transform 0.3s cubic-bezier(0.16,1,0.3,1),
            border-color 0.3s ease;
    }

    .nomad-card:hover {
        transform: translateY(-6px);
        border-color: #58a6ff;
    }

    .nomad-card img {
        width: 100%;
        height: 100%;

        object-fit: cover;

        position: absolute;
        top: 0;
        left: 0;

        z-index: 1;

        transition: transform 0.5s ease;
    }

    .nomad-card:hover img {
        transform: scale(1.06);
    }

    .nomad-overlay {
        position: absolute;

        top: 0;
        left: 0;

        width: 100%;
        height: 100%;

        background: linear-gradient(
            180deg,
            rgba(0,0,0,0.2) 0%,
            rgba(5,7,10,0.3) 35%,
            rgba(5,7,10,0.94) 75%,
            rgba(5,7,10,0.99) 100%
        );

        z-index: 2;
    }

    .nomad-content {
        position: absolute;

        bottom: 0;
        left: 0;

        width: 100%;

        padding: 1.2rem;

        z-index: 3;

        box-sizing: border-box;
    }

    /* =========================================
       8. CARD BADGES
    ========================================= */

    .badge-top-left {
        position: absolute;

        top: 12px;
        left: 12px;

        background: rgba(0,0,0,0.6);

        backdrop-filter: blur(8px);

        color: #ffffff;

        font-size: 0.75rem;
        font-weight: 700;

        padding: 0.25rem 0.65rem;

        border-radius: 20px;

        border: 1px solid rgba(255,255,255,0.15);

        z-index: 4;
    }

    .badge-top-right {
        position: absolute;

        top: 12px;
        right: 12px;

        background: rgba(0,0,0,0.6);

        backdrop-filter: blur(8px);

        color: #3fb950;

        font-size: 0.75rem;
        font-weight: 700;

        padding: 0.25rem 0.65rem;

        border-radius: 20px;

        border: 1px solid rgba(63,185,80,0.3);

        z-index: 4;
    }

    .badge-top-right-busy {
        color: #f85149;
        border-color: rgba(248,81,73,0.3);
    }

    /* =========================================
       9. CARD TEXT
    ========================================= */

    .card-title {
        font-size: 1.05rem;
        font-weight: 700;

        color: #ffffff;

        margin-bottom: 0.2rem;

        line-height: 1.3;

        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }

    .card-price {
        font-size: 1.3rem;
        font-weight: 900;

        color: #3fb950;

        margin-bottom: 0.6rem;

        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }

    /* =========================================
       10. CARD INFORMATION
    ========================================= */

    .badges-grid {
        display: grid;

        grid-template-columns: 1fr 1fr;

        gap: 6px;
    }

    .badge-stack {
        display: flex;

        flex-direction: column;

        gap: 5px;
    }

    .badge-info {
        display: block;

        background: rgba(255,255,255,0.1);

        backdrop-filter: blur(6px);

        color: #e6edf3;

        border: 1px solid rgba(255,255,255,0.15);

        border-radius: 20px;

        padding: 0.2rem 0.6rem;

        font-size: 0.73rem;
        font-weight: 500;

        text-align: center;

        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .badge-info i {
        margin-right: 4px;
        color: #ffffff !important;
    }

    /* =========================================
       10b. SPINNER TEXT (green, readable on light and dark)
    ========================================= */

    [data-testid="stSpinner"],
    [data-testid="stSpinner"] p,
    [data-testid="stSpinner"] span,
    [data-testid="stSpinner"] div {
        color: #16a34a !important;
        font-weight: 600;
    }

    /* =========================================
       11. RESPONSIVE DESIGN
    ========================================= */

    @media (max-width: 768px) {

        .hero-container {
            min-height: 600px;
        }

        .hero-content {
            top: 20%;
            padding: 0 1rem;
        }

        .hero-title {
            font-size: 2.5rem;
        }

        .hero-subtitle {
            font-size: 1rem;
        }

        .st-key-hero_search {
            width: calc(100% - 30px);
            margin-top: -185px !important;
        }

        .st-key-hero_search .stButton button {
            font-size: 0.70rem !important;
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
        }

        .main-content {
            padding: 0 1rem;
        }
    }

    @media (max-width: 480px) {

        .hero-title {
            font-size: 2.1rem;
        }

        .st-key-hero_search .stTextInput input {
            font-size: 0.9rem !important;
        }

        .nomad-card {
            height: 320px;
        }
    }

</style>

""", unsafe_allow_html=True)

# Encodage Base64 de la vidéo du Hero
hero_video_path = Path(__file__).parent / "assets" / "hero.mp4"
hero_video_base64 = ""
if hero_video_path.exists():
    with open(hero_video_path, "rb") as vid_file:
        hero_video_base64 = base64.b64encode(vid_file.read()).decode()

video_tag = (
    f'<video autoplay muted loop playsinline class="hero-video">'
    f'<source src="data:video/mp4;base64,{hero_video_base64}" type="video/mp4">'
    f'</video>'
) if hero_video_base64 else '<div style="position:absolute; width:100%; height:100%; background:#0d1117;"></div>'


# Callback used by the suggested-search buttons
def set_search_query(value):
    st.session_state.search_query = value


# 🎬 HERO VIDEO WITH TEXT
# html() aplatit le bloc : pas de lignes vides ni d'indentation => rendu HTML garanti
st.markdown(html(f"""
<div class="hero-container">
    {video_tag}
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <div class="hero-title">Trouve-moi un logement</div>
        <div class="hero-subtitle">
            Find your perfect student home in Casablanca. <br>
            Describe what you need. <br> We'll find it.
        </div>
    </div>
</div>
"""), unsafe_allow_html=True)


# 🔎 SEARCH BAR AND SUGGESTIONS OVER THE VIDEO
with st.container(key="hero_search"):
    query = st.text_input(
        "Recherche en langage naturel",
        placeholder="Ex: Studio meublé à Maarif avec wifi, budget max 3000 DH...",
        label_visibility="collapsed",
        key="search_query"
    )

    col_ex1, col_ex2, col_ex3 = st.columns(3)

    with col_ex1:
        st.button(
            "✨ Studio meublé Maarif",
            use_container_width=True,
            on_click=set_search_query,
            args=("Je cherche un studio meublé à Maarif avec un budget max de 3500 dirhams.",)
        )

    with col_ex2:
        st.button(
            "🎓 Chambre proche FSAC",
            use_container_width=True,
            on_click=set_search_query,
            args=("Je cherche une chambre disponible à Ain Chock pas loin de la fac.",)
        )

    with col_ex3:
        st.button(
            "📶 Appartement avec Wi-Fi",
            use_container_width=True,
            on_click=set_search_query,
            args=("Appartement à Sidi Maarouf avec wifi",)
        )


# Read the current value after normal typing or a suggested-search callback.
query = st.session_state.get("search_query", "")

# Space between the hero and the results section.
st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)


# Début du conteneur principal pour les cartes de résultats
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.divider()

if query:
    with st.spinner("⚡ Analyse de la requête..."):
        criteres, erreur = extraire_criteres_depuis_texte(query)

    if erreur:
        st.warning(f"⚠️ {erreur}")
    elif criteres.est_vide():
        message_vide = "⚠️ Aucun critère exploitable détecté. Essayez de préciser un quartier, un type de bien ou un budget en DH."
        if criteres.precision_manquante:
            message_vide += f" (Notion trop vague : {criteres.precision_manquante}.)"
        st.warning(message_vide)
    else:
        # Critères compris par le modèle, affichés pour que l'utilisateur puisse vérifier
        chips = "".join(
            f"<span style='display:inline-block; background:rgba(22,163,74,0.12); color:#16a34a; "
            f"border:1px solid rgba(22,163,74,0.35); border-radius:20px; padding:0.15rem 0.7rem; "
            f"margin:0 0.4rem 0.4rem 0; font-size:0.85rem; font-weight:600;'>{texte}</span>"
            for texte in criteres.en_texte()
        )
        st.markdown(
            html(f"<div style='margin-bottom:0.6rem;'><span style='font-weight:700; margin-right:0.5rem;'>Critères compris :</span>{chips}</div>"),
            unsafe_allow_html=True
        )

        if criteres.precision_manquante:
            st.info(
                f"ℹ️ Notion vague non filtrée : {criteres.precision_manquante}. "
                "Donnez une valeur chiffrée (budget en DH, durée en minutes) pour affiner."
            )

        erreur_db = None
        resultats = []
        try:
            resultats = rechercher_logements_db(criteres)
            for incoherence in verifier_coherence_schema():
                st.warning(f"🛠️ Cohérence schéma/base : {incoherence}")
        except (FileNotFoundError, sqlite3.Error) as erreur_lecture:
            erreur_db = f"Impossible de lire la base de données : {erreur_lecture}"

        if erreur_db:
            st.error(erreur_db)
        elif not resultats:
            st.info("Aucun logement ne correspond à vos critères.")
        else:
            st.markdown(
                f"<h3 style='color: #16a34a; font-weight: 700; margin-bottom: 1.2rem;'>⚡ {len(resultats)} logement(s) trouvé(s)</h3>",
                unsafe_allow_html=True
            )

            cols = st.columns(3)
            for idx, logement in enumerate(resultats):
                col = cols[idx % 3]

                logement_id = logement["id"]
                img_path = Path(__file__).parent / "assets" / f"{logement_id}.jpg"

                img_base64 = ""
                if img_path.exists():
                    with open(img_path, "rb") as img_file:
                        img_base64 = base64.b64encode(img_file.read()).decode()

                titre_nettoye = logement['titre'].split('–')[0].split('-')[0].strip()

                dispo_is_ok = logement["disponible"] == 1
                dispo_badge_class = "badge-top-right" if dispo_is_ok else "badge-top-right badge-top-right-busy"
                dispo_texte = "🟢 Disponible" if dispo_is_ok else "🔴 Occupé"

                meuble_texte = '<i class="bi bi-house-check"></i> Meublé' if logement["meuble"] == 1 else '<i class="bi bi-box-seam"></i> Non meublé'
                wifi_texte = '<i class="bi bi-wifi"></i> Wi-Fi' if logement["wifi"] == 1 else '<i class="bi bi-wifi-off"></i> Sans Wi-Fi'

                with col:
                    if img_base64:
                        img_tag = f'<img src="data:image/jpeg;base64,{img_base64}">'
                    else:
                        img_tag = '<div style="width:100%; height:100%; background:#161b22; display:flex; align-items:center; justify-content:center; color:#8b949e; position:absolute; top:0; left:0; z-index:1;">Pas d\'image</div>'

                    st.markdown(html(f"""
                    <div class="nomad-card">
                        <div class="badge-top-left">#{logement_id}</div>
                        <div class="{dispo_badge_class}">{dispo_texte}</div>
                        {img_tag}
                        <div class="nomad-overlay"></div>
                        <div class="nomad-content">
                            <div class="card-title">{titre_nettoye}</div>
                            <div class="card-price">{logement['loyer']} DH <span style="font-size:0.75rem; color:#8b949e; font-weight:400;">/ mois</span></div>
                            <div class="badges-grid">
                                <div class="badge-stack">
                                    <span class="badge-info">{wifi_texte}</span>
                                    <span class="badge-info"><i class="bi bi-clock"></i> {logement['distance_fac_min']} min FSAC</span>
                                </div>
                                <div class="badge-stack">
                                    <span class="badge-info">{meuble_texte}</span>
                                    <span class="badge-info"><i class="bi bi-geo-alt"></i> {logement['quartier']}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
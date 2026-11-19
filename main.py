# =========================================================
# MAIN.PY — POINT D'ENTRÉE TERMINAL DE L'APPLICATION LOGEMENT
# Usage : python main.py "Je cherche un studio meublé à Maarif, 2500 DH max"
# =========================================================

import sqlite3
import sys
from dotenv import load_dotenv
from database import rechercher_logements_db
from llm_pipeline import extraire_criteres_depuis_texte

# Charge la clé OPENAI_API_KEY depuis le fichier .env
load_dotenv()


def traiter_demande(message_client: str):
    """Traitement d'une requête utilisateur complète : extraction LLM -> validation Pydantic -> filtrage SQLite."""
    print(f'\n📩 Requête utilisateur : "{message_client}"')
    print("⏳ Analyse de la demande par le LLM...")

    # Étape 1 : Extraction et validation par le LLM (via llm_pipeline.py et schemas.py)
    criteres, erreur = extraire_criteres_depuis_texte(message_client)

    if erreur:
        print(f"\n⚠️ {erreur}")
        return

    # Contrôle de robustesse : Vérification si des critères exploitables ont été extraits
    if criteres.est_vide():
        print("\n⚠️ Aucun critère de logement exploitable n'a été détecté dans votre demande.")
        if criteres.precision_manquante:
            print(f"   (Notion trop vague : {criteres.precision_manquante})")
        print("💡 Conseil : Précisez un quartier (Maarif, Ain Chock, etc.), un budget max en DH, ou un type de bien (studio, chambre, appartement).")
        return

    print("\n✅ Critères compris :")
    for ligne in criteres.en_texte():
        print(f"   • {ligne}")
    if criteres.precision_manquante:
        print(f"ℹ️ Notion vague non filtrée : {criteres.precision_manquante}")

    # Étape 2 : Interrogation de la base de données SQLite (via database.py)
    try:
        resultats = rechercher_logements_db(criteres)
    except (FileNotFoundError, sqlite3.Error) as erreur_db:
        print(f"\n❌ Impossible de lire la base de données : {erreur_db}")
        return

    if not resultats:
        print("\n🏠 0 logement trouvé correspondant à vos critères dans la base de données.")
        return

    print(f"\n🏠 {len(resultats)} logement(s) trouvé(s) dans la base de données :")
    print("-" * 60)
    for logement in resultats:
        # Conversion explicite des booléens SQLite (1/0)
        meuble_str = "Oui" if logement["meuble"] == 1 else "Non"
        wifi_str = "Oui" if logement["wifi"] == 1 else "Non"
        dispo_str = "Disponible" if logement["disponible"] == 1 else "Non disponible"

        print(f"• ID {logement['id']} | {logement['titre']}")
        print(f"  📍 Quartier : {logement['quartier']} | 💰 Loyer : {logement['loyer']} DH | ⏱️ FSAC : {logement['distance_fac_min']} min")
        print(f"  🛏️ Meublé : {meuble_str} | 📶 Wi-Fi : {wifi_str} | 📌 Statut : {dispo_str}")
        print("-" * 60)


def main():
    # Message passé en argument, sinon message de test par défaut
    message_test = " ".join(sys.argv[1:]) or "Je cherche un chambre par chere a lusaka"
    traiter_demande(message_test)


if __name__ == "__main__":
    main()
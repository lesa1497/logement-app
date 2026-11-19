import sqlite3
from contextlib import closing
from pathlib import Path
from schemas import CriteresLogement, QUARTIERS, TYPES

# Chemin vers la base de données dans data/logements.db
CHEMIN_BD = Path(__file__).parent / "data" / "logements.db"


def _connecter() -> sqlite3.Connection:
    # sqlite3.connect crée un fichier vide si le chemin n'existe pas : on vérifie avant
    if not CHEMIN_BD.exists():
        raise FileNotFoundError(f"Base de données introuvable : {CHEMIN_BD}")
    connexion = sqlite3.connect(CHEMIN_BD)
    connexion.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return connexion


def rechercher_logements_db(criteres: CriteresLogement):
    # Requête SQL de base (toujours paramétrée : jamais de texte du LLM collé dans le SQL)
    requete = "SELECT * FROM logements WHERE 1=1"
    parametres = []

    # Application dynamique des critères extraits par le LLM
    if criteres.type is not None:
        requete += " AND type = ?"
        parametres.append(criteres.type)

    if criteres.quartier is not None:
        requete += " AND quartier = ?"
        parametres.append(criteres.quartier)

    if criteres.loyer_max is not None:
        requete += " AND loyer <= ?"
        parametres.append(criteres.loyer_max)

    if criteres.distance_fac_max_min is not None:
        requete += " AND distance_fac_min <= ?"
        parametres.append(criteres.distance_fac_max_min)

    if criteres.meuble is not None:
        requete += " AND meuble = ?"
        parametres.append(1 if criteres.meuble else 0)

    if criteres.wifi is not None:
        requete += " AND wifi = ?"
        parametres.append(1 if criteres.wifi else 0)

    if criteres.disponible is not None:
        requete += " AND disponible = ?"
        parametres.append(1 if criteres.disponible else 0)

    requete += " ORDER BY loyer ASC, distance_fac_min ASC"

    with closing(_connecter()) as connexion:
        return connexion.execute(requete, parametres).fetchall()


def verifier_coherence_schema() -> list[str]:
    """
    Compare les valeurs réellement présentes dans la base avec celles du schéma Pydantic.
    Retourne une liste de problèmes (vide si tout est cohérent).
    """
    problemes = []

    with closing(_connecter()) as connexion:
        quartiers_db = {
            ligne[0] for ligne in connexion.execute("SELECT DISTINCT quartier FROM logements")
            if ligne[0] is not None
        }
        types_db = {
            ligne[0] for ligne in connexion.execute("SELECT DISTINCT type FROM logements")
            if ligne[0] is not None
        }

    quartiers_absents_du_schema = quartiers_db - set(QUARTIERS)
    if quartiers_absents_du_schema:
        problemes.append(
            "quartiers présents en base mais absents du schéma : "
            + ", ".join(sorted(quartiers_absents_du_schema))
        )

    types_absents_du_schema = types_db - set(TYPES)
    if types_absents_du_schema:
        problemes.append(
            "types présents en base mais absents du schéma : "
            + ", ".join(sorted(types_absents_du_schema))
        )

    quartiers_sans_logement = set(QUARTIERS) - quartiers_db
    if quartiers_sans_logement:
        problemes.append(
            "quartiers du schéma absents de la base : "
            + ", ".join(sorted(quartiers_sans_logement))
        )

    types_sans_logement = set(TYPES) - types_db
    if types_sans_logement:
        problemes.append(
            "types du schéma absents de la base : "
            + ", ".join(sorted(types_sans_logement))
        )

    return problemes
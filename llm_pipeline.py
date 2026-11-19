import json
import re
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import ValidationError
from schemas import CriteresLogement, QUARTIERS, TYPES

load_dotenv()  # Charger les variables du .env AVANT d'initialiser le client

MODELE = "gpt-4o-mini"
LONGUEUR_MAX_DEMANDE = 500

# Le code (pas le LLM) a le dernier mot sur les notions « vagues » : un drapeau du modèle
# n'est retenu que si l'utilisateur a réellement employé un mot de ce type.
# (\b évite les faux positifs : « cherche » ne contient pas le mot « cher »)
MOTS_BUDGET_VAGUE = re.compile(
    r"\b(ch[eè]re?s?|abordables?|[ée]conomiques?|bon march[ée]|petit budget|budget serr[ée]|cheap|affordable)\b",
    re.IGNORECASE,
)
MOTS_PROXIMITE_VAGUE = re.compile(
    r"\b(proches?|pr[eè]s|loin|c[oô]t[eé]|close|near|nearby)\b",
    re.IGNORECASE,
)

_client = None


def _obtenir_client() -> OpenAI:
    """Client créé au premier appel : une clé API manquante ne plante pas l'import."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _construire_consigne() -> str:
    return (
        "Tu extrais les critères de recherche d'un logement étudiant à Casablanca "
        "à partir de la demande de l'utilisateur (français, parfois avec des fautes).\n\n"
        "Règles :\n"
        "1. Réponds uniquement en JSON conforme au JSON Schema donné plus bas.\n"
        "2. Mets null pour tout critère que l'utilisateur ne mentionne pas explicitement. "
        "N'invente JAMAIS de valeur et ne déduis aucune valeur par défaut.\n"
        f"3. type : uniquement parmi {list(TYPES)}.\n"
        f"4. quartier : uniquement parmi {list(QUARTIERS)}. Corrige les fautes de frappe et "
        "variantes d'orthographe (ex. « maarif », « Maârif » -> « Maarif »). "
        "Si l'utilisateur cite un quartier qui n'est PAS dans cette liste, laisse quartier à null "
        "et écris le nom cité dans quartier_inconnu.\n"
        "5. loyer_max : entier en DH, uniquement si un montant est donné.\n"
        "6. distance_fac_max_min : entier en minutes, uniquement si un nombre est donné.\n"
        "7. meuble et wifi : true si l'utilisateur les veut, false seulement s'il veut explicitement "
        "l'inverse (non meublé, sans wifi), sinon null.\n"
        "8. disponible : true seulement si l'utilisateur demande un logement disponible/libre, sinon null.\n"
        "9. budget_vague : true UNIQUEMENT si l'utilisateur emploie lui-même une expression vague sur le prix "
        "(pas cher, abordable, petit budget...). Ne pas parler de budget n'est PAS vague : dans ce cas null. "
        "proximite_vague : true UNIQUEMENT si l'utilisateur emploie lui-même une expression vague sur la "
        "proximité (proche, pas loin...) ; sinon null. Laisse toujours precision_manquante à null.\n"
        "10. Si la demande n'a aucun rapport avec la recherche d'un logement, "
        "tous les champs valent null.\n\n"
        "JSON Schema :\n"
        + json.dumps(CriteresLogement.model_json_schema(), ensure_ascii=False)
    )


def extraire_criteres_depuis_texte(
    message_client: str,
) -> tuple[CriteresLogement | None, str | None]:
    """
    Retourne (criteres, None) si l'extraction a réussi,
    ou (None, message_pour_l_utilisateur) en cas de problème.
    """
    message_client = (message_client or "").strip()

    if not message_client:
        return None, "Votre demande est vide. Décrivez le logement que vous cherchez."

    if len(message_client) > LONGUEUR_MAX_DEMANDE:
        return None, f"Votre demande est trop longue ({LONGUEUR_MAX_DEMANDE} caractères maximum)."

    try:
        reponse = _obtenir_client().chat.completions.create(
            model=MODELE,
            temperature=0,
            messages=[
                {"role": "system", "content": _construire_consigne()},
                {"role": "user", "content": message_client},
            ],
            response_format={"type": "json_object"},
        )
        texte_json = reponse.choices[0].message.content
    except OpenAIError as erreur:
        print(f"\n❌ Erreur API OpenAI : {erreur}")
        return None, (
            "Le service d'analyse est momentanément indisponible "
            "(clé API ou connexion). Réessayez dans un instant."
        )

    if not texte_json:
        return None, "Le modèle n'a renvoyé aucune réponse. Réessayez ou reformulez votre demande."

    try:
        criteres = CriteresLogement.model_validate_json(texte_json)
    except ValidationError as erreur:
        print("\n❌ Erreur de validation Pydantic :")
        for detail in erreur.errors():
            champ = detail["loc"][0] if detail["loc"] else "(réponse)"
            print(f"   - {champ} : {detail['msg']}")
        return None, "Je n'ai pas réussi à comprendre votre demande. Essayez de la reformuler."

    # Le modèle peut ranger un quartier VALIDE dans quartier_inconnu : on le récupère
    if criteres.quartier is None and criteres.quartier_inconnu:
        for quartier_valide in QUARTIERS:
            if quartier_valide.lower() == criteres.quartier_inconnu.strip().lower():
                criteres.quartier = quartier_valide
                criteres.quartier_inconnu = None
                break

    # Quartier cité mais absent de la base : on le dit honnêtement
    if criteres.quartier_inconnu and criteres.quartier is None:
        return None, (
            f"Le quartier « {criteres.quartier_inconnu} » n'est pas dans notre base. "
            f"Quartiers disponibles : {', '.join(QUARTIERS)}."
        )

    # Notes affichées à l'utilisateur, calculées par le CODE (pas par le LLM) :
    # un drapeau « vague » ne compte que si le critère chiffré correspondant est vide.
    notes = []
    if (criteres.budget_vague and criteres.loyer_max is None
            and MOTS_BUDGET_VAGUE.search(message_client)):
        notes.append("budget sans montant précis")
    if (criteres.proximite_vague and criteres.distance_fac_max_min is None
            and MOTS_PROXIMITE_VAGUE.search(message_client)):
        notes.append("proximité de la fac sans durée précise")
    if criteres.quartier_inconnu:  # un quartier valide ET un autre cité : on cherche sur le valide
        autre = criteres.quartier_inconnu
        if autre.strip().lower() in {q.lower() for q in QUARTIERS}:
            notes.append(f"plusieurs quartiers cités : seul « {criteres.quartier} » est pris en compte")
        else:
            notes.append(f"quartier « {autre} » absent de la base (ignoré)")

    criteres.precision_manquante = "; ".join(notes) if notes else None

    return criteres, None
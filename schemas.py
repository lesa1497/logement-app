from typing import Literal, get_args
from pydantic import BaseModel, ConfigDict, Field, field_validator

TypeLogement = Literal["studio", "chambre", "appartement"]
Quartier = Literal["Maarif", "Ain Chock", "Hay Hassani", "Sidi Maarouf", "Oulfa"]

# Valeurs autorisées (réutilisées dans le prompt et dans la vérification de la base)
TYPES = get_args(TypeLogement)
QUARTIERS = get_args(Quartier)

# Champs qui servent réellement à filtrer la base
# (quartier_inconnu et precision_manquante sont des champs d'information, pas des filtres)
CHAMPS_RECHERCHE = (
    "type",
    "quartier",
    "loyer_max",
    "meuble",
    "wifi",
    "distance_fac_max_min",
    "disponible",
)


class CriteresLogement(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    type: TypeLogement | None = None
    quartier: Quartier | None = None
    loyer_max: int | None = Field(
        default=None, ge=0, description="Loyer maximum en DH, seulement si un montant est donné"
    )
    meuble: bool | None = None
    wifi: bool | None = None
    distance_fac_max_min: int | None = Field(
        default=None,
        ge=0,
        description="Distance max en minutes jusqu'à la FSAC, seulement si un nombre est donné",
    )
    disponible: bool | None = None

    # Champs d'information (non utilisés pour filtrer)
    quartier_inconnu: str | None = Field(
        default=None,
        description="Nom du quartier cité par l'utilisateur s'il n'est pas dans la liste autorisée",
    )
    budget_vague: bool | None = Field(
        default=None,
        description="true si le prix est évoqué de façon vague (pas cher, abordable...), sinon null",
    )
    proximite_vague: bool | None = Field(
        default=None,
        description="true si la proximité de la fac est évoquée de façon vague (proche, pas loin...), sinon null",
    )
    precision_manquante: str | None = Field(
        default=None,
        description="Réservé au code : laisse toujours null",
    )

    @field_validator("loyer_max", "distance_fac_max_min", mode="before")
    @classmethod
    def _accepter_entier_ecrit_en_float(cls, valeur):
        """Le LLM peut renvoyer 2500.0 au lieu de 2500 : on l'accepte s'il s'agit bien d'un entier."""
        if isinstance(valeur, float) and valeur.is_integer():
            return int(valeur)
        return valeur

    @field_validator("quartier_inconnu", "precision_manquante", mode="before")
    @classmethod
    def _chaine_vide_devient_none(cls, valeur):
        if isinstance(valeur, str) and not valeur.strip():
            return None
        return valeur

    def est_vide(self) -> bool:
        """Retourne True si aucun critère de FILTRAGE n'a été renseigné."""
        return all(getattr(self, champ) is None for champ in CHAMPS_RECHERCHE)

    def en_texte(self) -> list[str]:
        """Liste lisible des critères compris (pour les montrer à l'utilisateur)."""
        lignes = []
        if self.type:
            lignes.append(f"Type : {self.type}")
        if self.quartier:
            lignes.append(f"Quartier : {self.quartier}")
        if self.loyer_max is not None:
            lignes.append(f"Loyer max : {self.loyer_max} DH")
        if self.distance_fac_max_min is not None:
            lignes.append(f"≤ {self.distance_fac_max_min} min de la FSAC")
        if self.meuble is not None:
            lignes.append("Meublé" if self.meuble else "Non meublé")
        if self.wifi is not None:
            lignes.append("Wi-Fi" if self.wifi else "Sans Wi-Fi")
        if self.disponible is not None:
            lignes.append("Disponible" if self.disponible else "Occupé")
        return lignes
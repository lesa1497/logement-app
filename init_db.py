# =========================================================
# INITIALISATION DE LA BASE DE DONNÉES — LOGEMENTS
# =========================================================

import sqlite3
from pathlib import Path

# Chemin vers la base de données (dans le dossier data/)
CHEMIN_BD = Path(__file__).parent / "data" / "logements.db"

# S'assure que le dossier 'data/' existe, sinon le crée
CHEMIN_BD.parent.mkdir(parents=True, exist_ok=True)

# Connexion à la base de données (la crée si elle n'existe pas)
connexion = sqlite3.connect(CHEMIN_BD)
cursor = connexion.cursor()

# Création de la table avec tes contraintes exactes
cursor.execute("""
CREATE TABLE IF NOT EXISTS logements (
    id INTEGER PRIMARY KEY,
    titre TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('studio','chambre','appartement')),
    quartier TEXT NOT NULL CHECK (quartier IN ('Maarif','Ain Chock','Hay Hassani','Sidi Maarouf','Oulfa')),
    loyer INTEGER NOT NULL,
    meuble INTEGER NOT NULL CHECK (meuble IN (0,1)),
    wifi INTEGER NOT NULL CHECK (wifi IN (0,1)),
    distance_fac_min INTEGER NOT NULL,
    disponible INTEGER NOT NULL CHECK (disponible IN (0,1))
);
""")

# Insertion des 40 annonces du prof
logements_data = [
    (1, 'Studio meublé au rez-de-chaussée – Hay Hassani', 'studio', 'Hay Hassani', 3200, 1, 0, 20, 1),
    (2, 'Studio meublé au rez-de-chaussée – Maarif', 'studio', 'Maarif', 3350, 1, 0, 40, 0),
    (3, 'Appartement 2 pièces meublé – Ain Chock', 'appartement', 'Ain Chock', 4750, 1, 0, 4, 1),
    (4, 'Appartement 2 pièces – Oulfa', 'appartement', 'Oulfa', 5150, 0, 1, 21, 1),
    (5, 'Studio lumineux – Oulfa', 'studio', 'Oulfa', 2850, 0, 1, 24, 1),
    (6, 'Appartement 2 pièces meublé – Maarif', 'appartement', 'Maarif', 6850, 1, 1, 28, 1),
    (7, 'Chambre au 3e étage – Maarif', 'chambre', 'Maarif', 1950, 0, 1, 38, 0),
    (8, 'Studio meublé au rez-de-chaussée – Hay Hassani', 'studio', 'Hay Hassani', 1950, 1, 0, 17, 1),
    (9, 'Studio meublé neuf – Oulfa', 'studio', 'Oulfa', 2100, 1, 1, 18, 1),
    (10, 'Chambre meublé lumineux – Ain Chock', 'chambre', 'Ain Chock', 1750, 1, 0, 7, 1),
    (11, 'Studio meublé lumineux – Ain Chock', 'studio', 'Ain Chock', 3350, 1, 1, 14, 1),
    (12, 'Studio meublé rénové – Oulfa', 'studio', 'Oulfa', 2450, 1, 1, 25, 1),
    (13, 'Studio meublé neuf – Hay Hassani', 'studio', 'Hay Hassani', 2900, 1, 1, 21, 0),
    (14, 'Chambre meublé avec terrasse – Hay Hassani', 'chambre', 'Hay Hassani', 1200, 1, 0, 14, 1),
    (15, 'Studio meublé proche tram – Maarif', 'studio', 'Maarif', 3300, 1, 1, 29, 1),
    (16, 'Chambre meublé avec balcon – Ain Chock', 'chambre', 'Ain Chock', 1300, 1, 1, 5, 1),
    (17, 'Chambre meublé au 3e étage – Ain Chock', 'chambre', 'Ain Chock', 1550, 1, 0, 4, 1),
    (18, 'Chambre meublé au 3e étage – Oulfa', 'chambre', 'Oulfa', 1250, 1, 1, 19, 1),
    (19, 'Appartement 3 pièces – Hay Hassani', 'appartement', 'Hay Hassani', 5350, 0, 1, 21, 1),
    (20, 'Chambre meublé lumineux – Sidi Maarouf', 'chambre', 'Sidi Maarouf', 1250, 1, 1, 22, 1),
    (21, 'Studio meublé proche tram – Maarif', 'studio', 'Maarif', 2850, 1, 1, 26, 1),
    (22, 'Studio meublé proche tram – Oulfa', 'studio', 'Oulfa', 2800, 1, 0, 20, 1),
    (23, 'Appartement 3 pièces – Sidi Maarouf', 'appartement', 'Sidi Maarouf', 5100, 0, 1, 25, 1),
    (24, 'Appartement 2 pièces – Sidi Maarouf', 'appartement', 'Sidi Maarouf', 4700, 0, 1, 25, 1),
    (25, 'Appartement 3 pièces – Hay Hassani', 'appartement', 'Hay Hassani', 5050, 0, 0, 16, 1),
    (26, 'Chambre meublé proche tram – Sidi Maarouf', 'chambre', 'Sidi Maarouf', 1400, 1, 1, 28, 0),
    (27, 'Chambre meublé au rez-de-chaussée – Sidi Maarouf', 'chambre', 'Sidi Maarouf', 1150, 1, 1, 34, 1),
    (28, 'Chambre lumineux – Ain Chock', 'chambre', 'Ain Chock', 1450, 0, 0, 14, 1),
    (29, 'Studio neuf – Oulfa', 'studio', 'Oulfa', 2500, 0, 1, 28, 1),
    (30, 'Chambre meublé avec terrasse – Sidi Maarouf', 'chambre', 'Sidi Maarouf', 1100, 1, 0, 26, 1),
    (31, 'Appartement 2 pièces – Sidi Maarouf', 'appartement', 'Sidi Maarouf', 4100, 0, 1, 28, 1),
    (32, 'Appartement 3 pièces – Ain Chock', 'appartement', 'Ain Chock', 3450, 0, 0, 15, 0),
    (33, 'Appartement 2 pièces meublé – Ain Chock', 'appartement', 'Ain Chock', 4300, 1, 0, 8, 0),
    (34, 'Studio meublé lumineux – Oulfa', 'studio', 'Oulfa', 2300, 1, 1, 30, 1),
    (35, 'Studio meublé neuf – Maarif', 'studio', 'Maarif', 2300, 1, 1, 28, 1),
    (36, 'Chambre meublé avec balcon – Maarif', 'chambre', 'Maarif', 1750, 1, 1, 26, 0),
    (37, 'Appartement 3 pièces meublé – Sidi Maarouf', 'appartement', 'Sidi Maarouf', 5500, 1, 1, 23, 1),
    (38, 'Appartement 2 pièces meublé – Hay Hassani', 'appartement', 'Hay Hassani', 4050, 1, 0, 17, 1),
    (39, 'Studio meublé au rez-de-chaussée – Maarif', 'studio', 'Maarif', 3200, 1, 1, 28, 1),
    (40, 'Chambre meublé lumineux – Hay Hassani', 'chambre', 'Hay Hassani', 1250, 1, 1, 17, 1)
]

# Utilisationn de INSERT OR IGNORE pour éviter les doublons si on relance le script
cursor.executemany("""
INSERT OR IGNORE INTO logements (id, titre, type, quartier, loyer, meuble, wifi, distance_fac_min, disponible)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", logements_data)

connexion.commit()
connexion.close()

print("✅ Base de données initialisée avec succès ! 40 annonces insérées.")
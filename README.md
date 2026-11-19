# 🏠Trouve-moi un logement

Find a student home in Casablanca by simplly writing what you need in plain language.

for example "Je cherche un studio meublé à Maarif, 2 500 DH max"

The app understands the request, searches a local SQLite database of 40 listings, and displays the matching ones as cards. The interface is in French to match the db.

---------------------------------------------------------------------------------------------------------------------------------------

## How it works

Free-text request
      │
      ▼
 LLM (gpt-4o-mini)  ──►  extracts search criteria as JSON
      │
      ▼
 Pydantic (strict)  ──►  validates the criteria (allowed quartiers, types, integers...)
      │
      ▼
 SQLite (SQL with parameters)  ──►  fetches the matching listings
      │
      ▼
 Streamlit cards  ──►  every listing shown comes from the database



NB : The model never invents listings. It only turns the sentence into criteria. The results always come from "logements.db".

The app also reacts to imperfect requests:

| Situation | Example | What the app does |

| Typos / other spellings | `studio a maarrif` | Understood as Maarif |
| Vague notion | `chambre pas chère` | Searches chambres and tells you no budget was given |
| Neighborhood not in the base | `chambre à Lusaka` | Says it isn't in the base and lists the available ones |
| Off-topic | `Raconte-moi une blague` | Says no usable criteria were found |
| Empty request / API failure | | Clear message, no crash |

---

## Prerequisites

- **Python 3.10 or newer**
- An **OpenAI API key or Simply use ollama** but the app calls `gpt-4o-mini`; a few cents are enough for testing
- The database file `data/logements.db` provided 

---

## Installation

### 1. Get the project

Put all the files in one folder and open a terminal in it.


### 2. Install the dependencies

pip install -r requirements.txt


### 3. Add your OpenAI API key

Create a file named **`.env`** in the project folder (same level as `app.py`) containing:


OPENAI_API_KEY=sk-your-key-here


- Get a key at <https://platform.openai.com/api-keys>.
- **Never share or commit this file.** Add `.env` to your `.gitignore` if you use Git.

### 4. Check the folder structure


logement-app/
├── app.py               # Streamlit interface
├── main.py              # Same pipeline in the terminal
├── llm_pipeline.py      # LLM call + prompt + validation
├── schemas.py           # Pydantic model of the search criteria
├── database.py          # SQL queries on SQLite
├── evaluation.py        # Automated test set (28 requests)
├── requirements.txt
├── .env                 # your API key (you create it)
├── data/
│   └── logements.db     # the 40 listings
└── assets/              # optional
    ├── hero.mp4         # background video of the home page
    └── <id>.jpg         # one photo per listing (1.jpg, 2.jpg, ...)


The `assets/` folder is optional: without `hero.mp4` the page uses a dark background, and without a photo the card shows "Pas d'image".

---

## Run the web app (Streamlit)


python -m streamlit run app.py


Then open **<http://localhost:8501>** in your browser (Streamlit usually opens it for you).

Type a request in the search bar, or click one of the three suggestion buttons. Press `Ctrl + C` in the terminal to stop the app.

> Using `python -m streamlit` instead of `streamlit` avoids the "command not found" error when the Scripts folder isn't in your PATH.

### Requests to try

- `Je cherche un studio meublé à Maarif, 3500 dirhams max`
- `Logement disponible à Oulfa`
- `chambre a maârif`
- `chambre pas chère`
- `chambre à moins de 10 min de la fac`
- `chambre à Lusaka` (neighborhood not in the base)
- `Raconte-moi une blague` (off-topic)

> The database has only 40 listings, so some perfectly valid requests return **0 results**. That is expected: it means the base contains nothing matching, not that the app is broken.

---

## Run in the terminal (no browser)

```bash
python main.py "Je cherche un studio meublé à Maarif, 2500 DH max"


Without an argument, it runs a default test sentence.

---

## Run the evaluation

python evaluation.py              # one run per request
python evaluation.py --repeats 3  # three runs per request (measures stability)


It sends 28 varied requests (clear, typos, vague, off-topic, unknown neighborhood, empty, known limits) through the real pipeline and checks:

- the extracted criteria against the expected ones,
- that every listing returned by the database really respects those criteria,
- that vague notions are flagged only when they should be.

Results appear in the terminal and are saved in `evaluation_resultats.md`. Each run makes about 28 small API calls (×3 with `--repeats 3`). Statuses: `OK`, `ÉCHEC`, and `LIMITE` (a failure on a limit of the design that is known and documented).

---


## Known limits

- One neighborhood and one type per request (`Maarif ou Oulfa` keeps only the first, and tells you).
- Only a maximum rent, no minimum (`entre 2000 et 3000 DH` keeps only the 3000 upper bound).
- Contradictory requests (`meublé mais pas meublé`) are not detected.
- Vague words ("pas cher", "proche") are recognized from a short keyword list, so a rare synonym may not be flagged.
- The neighborhoods and types are written in `schemas.py`; a new one in the database requires updating that file.

---

## Tech stack

Python · Streamlit · OpenAI API (`gpt-4o-mini`, JSON mode) · Pydantic v2 (strict validation) · SQLite

*Course mini-project "Trouve-moi un logement" — natural-language querying of a database (ISI M2, LLM et agents IA).*

##By DAKA Nkosi Siyabonga & LESA Mwaba Emmanuel
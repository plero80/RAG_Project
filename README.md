# RAG Project

A Python project for extracting text from PDF documents, cleaning pages, and
splitting the text into overlapping chunks for retrieval-augmented generation.
The Gemini client setup is included for future embedding work.

## Setup

Tested with Python 3.11. Run these commands from the project directory in
PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env` before using the Gemini client. The local `.env`
file and virtual environment are excluded from Git.

## Database

Start Docker Desktop. Set the `POSTGRES_*` variables and `DATABASE_URL` in
`.env` using `.env.example` as a reference. Set `POSTGRES_PASSWORD` before the
first database startup; the example password is a placeholder.

The Docker database is available at `127.0.0.1:55432` by default. This avoids
conflicting with a Windows PostgreSQL installation using port `5432`. Keep
`POSTGRES_PORT` and the port in `DATABASE_URL` in sync. PostgreSQL still uses
port `5432` inside the container.

Install the database dependencies in your active virtual environment, then
start the database and initialize its schema:

```powershell
python -m pip install "psycopg[binary]" pgvector
docker compose up -d postgres
python init_database.py
```

If you change the host port, run `docker compose up -d postgres` again to apply
the mapping. The existing `postgres_data` volume is retained. Changes to
`POSTGRES_USER`, `POSTGRES_DB`, or `POSTGRES_PASSWORD` in `.env` only configure
a new, empty data volume; they do not update an existing database.

## Run

The sample scripts use the bundled `data/apple.pdf` document:

```powershell
python app/ingestion/parser.py
python inspection_clean.py
python inspect_chunking.py
```

The parser extracts text and page metadata. The inspection scripts display
cleaned text and overlapping chunks.

## Files

- `app/ingestion/parser.py`: extract pages from a PDF or a directory of PDFs.
- `app/ingestion/cleaner.py`: normalize and clean extracted text.
- `app/ingestion/chunker.py`: create overlapping text chunks with page metadata.
- `app/ingestion/embedder.py`: initialize the Gemini client.
- `data/`: sample annual report PDFs.

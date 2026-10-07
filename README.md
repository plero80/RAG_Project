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

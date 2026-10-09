# Document Indexing and Semantic Search

A Python CLI for indexing PDF and DOCX documents and retrieving relevant passages.
It extracts and cleans text, applies one of three chunking strategies, creates
768-dimensional embeddings with Gemini `gemini-embedding-001`, and stores them in
PostgreSQL with pgvector. Search embeds a question and ranks stored chunks by
cosine similarity. It returns source passages and metadata, without generating
an answer with an LLM.

## Requirements

- Python 3.12 (verified locally with Python 3.12.2).
- Docker with Docker Compose; start Docker Desktop when using Windows.
- A Gemini API key with access and available quota for `gemini-embedding-001`.

Python dependencies are pinned in `requirements.txt`. Docker uses the
pgvector-enabled PostgreSQL image configured in `docker-compose.yml`.

## Setup

Run these PowerShell commands from the directory containing `index_documents.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For the first setup, create your local configuration:

```powershell
Copy-Item .env.example .env
```

If `.env` already exists, edit it instead of replacing it. Set the API key and
replace the password placeholder in both `POSTGRES_PASSWORD` and `POSTGRES_URL`.
The `.env` file is excluded from Git; `.env.example` contains placeholders only.
If activation is unavailable, use `.\.venv\Scripts\python.exe` in place of
`python` in subsequent commands.

### Environment variables

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | API key used to embed documents and search queries. |
| `POSTGRES_URL` | Application connection string, e.g. `postgresql://rag_user:YOUR_PASSWORD@127.0.0.1:55432/rag_db`. |
| `POSTGRES_DB` | Database created by Docker; example: `rag_db`. |
| `POSTGRES_USER` | Database user created by Docker; example: `rag_user`. |
| `POSTGRES_PASSWORD` | Password assigned to that user on the first database startup. |
| `POSTGRES_PORT` | Host port exposed by Docker; example: `55432`. |

The application reads `POSTGRES_URL`; the other `POSTGRES_*` variables configure
Docker. Keep the user, password, database, and port in the URL consistent with
those settings. URL-encode special characters in the password portion of the URL.

### Start PostgreSQL

```powershell
docker compose up -d postgres
docker compose ps
```

Wait for PostgreSQL to finish starting. To inspect startup problems, run:

```powershell
docker compose logs postgres
```

The default connection is `127.0.0.1:55432`; PostgreSQL uses port `5432` inside the
container. Indexing automatically creates the `vector` extension and `chunks`
table before requesting embeddings. No separate initialization script is needed.
An existing PostgreSQL server must have pgvector installed and allow the configured
user to initialize the schema.

Data persists in the `postgres_data` volume. Changing the database name, user, or
password in `.env` does not update an already initialized database volume.

## Index documents

Each command accepts one PDF or DOCX file. For the bundled PDF:

```powershell
python index_documents.py --file .\data\apple.pdf --strategy sentence
```

The bundled 80-page `apple.pdf` produces 634 sentence chunks at the default
settings. The local database was verified to contain those 634 rows. The expected
completion message is:

```text
Indexed apple.pdf: 634 chunks using 'sentence'.
```

Other strategy examples:

```powershell
python index_documents.py --file .\data\apple.pdf --strategy fixed-size --chunk-size 500 --overlap 50
python index_documents.py --file .\data\apple.pdf --strategy paragraph
```

For DOCX, supply your own file path, quoting paths that contain spaces:

```powershell
python index_documents.py --file "C:\path\to\your document.docx" --strategy paragraph
```

### Chunking strategies

Sizes and overlap are measured in **characters**, not tokens.

| Indexing `--strategy` | Behavior | Search `--split-strategy` |
| --- | --- | --- |
| `fixed-size` | Up to `--chunk-size` characters with `--overlap` characters shared between adjacent chunks. Defaults: 500 and 50. | `fixed` |
| `sentence` | Groups sentences toward `--chunk-size` characters (default 500). A single long sentence can exceed that size. Overlap is unused. | `sentence` |
| `paragraph` | Uses parser blocks and blank-line boundaries. Size and overlap options are unused. | `paragraph` |

Fixed-size chunking requires a positive size and `0 <= overlap < chunk_size`.
Sentence chunking requires a positive size. PDF chunks stay within individual
pages. DOCX content is treated as one document without page numbers.

Repeating an identical indexing run updates matching chunk IDs instead of adding
duplicates, but generates embeddings again. Different strategies coexist in the
same table. Changing content or chunking settings can leave earlier chunks in
the database; indexing does not delete superseded rows.

## Search

Wrap the entire query in quotes:

```powershell
python search.py --query "What were Apple's total net sales?"
```

Search returns up to five results by default. Use a positive `--limit` to change
the count, and optionally filter by the stored strategy:

```powershell
python search.py --query "What were Apple's total net sales?" --limit 2 --split-strategy sentence
```

Omitting `--split-strategy` searches all strategies and prints a notice about
potentially overlapping passages. Fixed-size chunks use the filter value `fixed`.
Results include the filename, PDF page number (or `N/A` for DOCX), similarity,
strategy, and chunk text. Higher similarity ranks first; this score is not a
confidence percentage.

### Recorded database results

The following two results come from an existing successful retrieval trace;
their text was read from PostgreSQL using the recorded chunk IDs. That search
returned five results. The trace does not store the original query, so this
excerpt is not presented as the response to the example query above.

```text
Result 1
Document: apple.pdf
Page: 34
Similarity: 0.7078
Strategy: sentence
Apple Inc.

Result 2
Document: apple.pdf
Page: 35
Similarity: 0.7078
Strategy: sentence
Apple Inc.
```

These results also illustrate a current limitation: repeated PDF headings can
become separate chunks and appear in search results. A fresh run of the example
query during documentation verification encountered a Gemini API error, so no
successful output for that specific query is claimed here.

## Database schema

| Column | Type / role |
| --- | --- |
| `id` | `BIGSERIAL` primary key. |
| `chunk_id` | Unique UUID used for upserts. |
| `document_id` | SHA-256 hash of the source file contents. |
| `filename` | Source filename. |
| `page_number` | PDF page number; null for DOCX. |
| `chunk_index` | Zero-based chunk position in the indexing run. |
| `chunk_text` | Cleaned chunk text. |
| `split_strategy` | `fixed`, `sentence`, or `paragraph`. |
| `embedding` | `VECTOR(768)`. |
| `created_at` | Timestamp assigned by PostgreSQL on insertion. |

Search uses pgvector cosine distance (`<=>`) and displays `1 - distance` as
similarity. Updating an existing chunk preserves its original `created_at`.
Initialization creates missing objects but does not migrate an existing table
with an older schema.

## Indexing progress and traces

Indexing prints a trace ID, start/completion messages for each stage, and elapsed
seconds. Parsing, cleaning, chunking, database initialization, embedding setup,
embedding, database saving, and the total run are timed separately. Each chunk
shows its position in the embedding run. Slow operations print a `waiting`
message every 10 seconds, including while the Gemini SDK waits or retries.

Example progress format (times are illustrative):

```text
[embedding chunk 12/634] started | 0.00s
[embedding chunk 12/634] waiting | 10.00s
[embedding chunk 12/634] waiting | 20.00s
[embedding chunk 12/634] completed | 23.41s
```

Structured events are appended to `logs/traces.jsonl`. Filter on the printed
`trace_id` to inspect one run; indexing stages have the `indexing.` prefix.
Each event records a status and `latency_ms`. Chunk events also record the chunk
ID, position, character count, completed count, and model. Failures record the
exception type and numeric error code when available, without exception bodies,
document text, vectors, or credentials. Stage durations are nested: `total`
already includes embedding time, so do not add all event durations together.
Request timings include SDK retries and backoff; individual retry attempts are
not timed separately.

To follow the log in another PowerShell terminal:

```powershell
Get-Content .\logs\traces.jsonl -Tail 20 -Wait
```

If the log cannot be written, indexing reports a warning and continues with
console timings. Pressing Ctrl+C records cancellation and exits with status 130.

## Errors and limitations

- Missing files, unsupported file types, documents with no extractable text,
  invalid chunking arguments, blank queries, and nonpositive limits produce CLI
  errors. Invalid arguments exit with status 2; handled operational failures
  exit with status 1.
- Gemini failures, network failures, and database failures produce error
  messages. An empty result set prints `No results found.`
- Embeddings are requested sequentially, one per chunk. Large documents can take
  several minutes; use the progress output and traces to locate delays. The client
  allows up to six attempts for HTTP 429 and selected server errors, with an
  initial retry delay of 5 seconds and a maximum delay of 60 seconds. Persistent
  quota exhaustion can still cause failure. Check the project's available
  Gemini quota and use a smaller document while testing.
- Chunks are inserted only after all document embeddings succeed. A failed
  embedding run does not save partial progress and cannot resume midway.
- Scanned PDFs require OCR before indexing; this project does not perform OCR.
  PDF blocks are not always semantic paragraphs. Sentence boundaries use a
  simple punctuation rule, and paragraph chunks have no size cap. Very long
  chunks may exceed the embedding service's input limit.
- Search returns the nearest available chunks without a relevance threshold.
  Review the returned passages against the source document.

## Project layout

```text
index_documents.py       Indexing CLI and input/error handling
search.py                Search CLI and result formatting
app/parsing/             PDF and DOCX parsers
app/ingestion/cleaner.py  Text and block cleanup
app/ingestion/embedder.py Gemini document/query embeddings and retry settings
app/chunking/            Shared interface, strategies, and factory
app/db/database.py       Schema initialization, upserts, and similarity search
app/rag/retriever.py     Query embedding and database retrieval
app/core/tracer.py       Local JSONL trace events
data/                    Sample PDF documents
logs/traces.jsonl        Generated indexing and search trace log
tests/                   Offline indexing trace and failure-handling checks
docker-compose.yml      PostgreSQL with pgvector
.env.example             Configuration template
requirements.txt         Pinned Python dependencies
```

For the full argument lists:

```powershell
python index_documents.py --help
python search.py --help
```

Run the tracing tests without calling Gemini or modifying the database:

```powershell
python -m unittest discover -s tests -v
```

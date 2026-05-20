#!/usr/bin/env python3
import os
import sys
import sqlite3
import argparse
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_FILE = ".zerostic_rag.db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# ANSI Colors for beautiful UI
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{Colors.OKGREEN}✔ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✘ {msg}{Colors.ENDC}", file=sys.stderr)

# Lazy loading of heavy libraries to keep CLI responsive
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print_info("Loading local SentenceTransformer model (all-MiniLM-L6-v2)...")
        try:
            from sentence_transformers import SentenceTransformer
            # Disable symlink warnings or HuggingFace logs if needed
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except ImportError:
            print_error("Failed to import 'sentence-transformers'. Did you run setup_rag.sh or activate your virtual environment?")
            sys.exit(1)
    return _embedding_model

def get_openai_client():
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
    except ImportError:
        print_error("Failed to import 'openai'. Did you run setup_rag.sh or activate your virtual environment?")
        sys.exit(1)

# SQLite Database Setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Document table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        last_modified REAL
    )
    """)
    
    # Chunk table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        title TEXT,
        content TEXT,
        start_line INTEGER,
        end_line INTEGER,
        embedding BLOB,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# Smart Markdown Chunker
def chunk_markdown_file(file_path: Path):
    """
    Parses a markdown file line by line and chunks it semantically.
    Groups text by markdown headers (#, ##, ###) while capping size.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    chunks = []
    current_header = "General"
    current_lines = []
    start_line = 1
    
    # Standard thresholds
    char_limit = 1500  # Target character size (~250-300 words)
    min_char_limit = 300 # Merge chunks smaller than this
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check if this is a header
        if stripped.startswith("#"):
            # Header level 1, 2, or 3
            header_parts = stripped.split(maxsplit=1)
            if len(header_parts) > 1 and len(header_parts[0]) <= 3:
                # If we already have accumulated content, flush the chunk
                accumulated_text = "".join(current_lines).strip()
                if len(accumulated_text) >= min_char_limit or (accumulated_text and stripped.startswith("# ")):
                    chunks.append({
                        "title": current_header,
                        "content": accumulated_text,
                        "start_line": start_line,
                        "end_line": line_num - 1
                    })
                    current_lines = []
                    start_line = line_num
                
                # Update current header
                current_header = header_parts[1]
                current_lines.append(line)
                continue
                
        current_lines.append(line)
        
        # Split chunk if it becomes too large
        accumulated_text = "".join(current_lines)
        if len(accumulated_text) >= char_limit:
            chunks.append({
                "title": current_header,
                "content": accumulated_text.strip(),
                "start_line": start_line,
                "end_line": line_num
            })
            current_lines = []
            start_line = line_num + 1

    # Flush any remaining text
    accumulated_text = "".join(current_lines).strip()
    if accumulated_text:
        chunks.append({
            "title": current_header,
            "content": accumulated_text,
            "start_line": start_line,
            "end_line": len(lines)
        })
        
    return chunks

# Vector Math Cosine Similarity
def cosine_similarity(v1, v2):
    dot_prod = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_prod / (norm_v1 * norm_v2))

# Subcommand: Ingest
def cmd_ingest(args):
    print_info("Initializing database...")
    init_db()
    
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print_error("The 'docs' directory was not found in the current workspace.")
        return
        
    # Get all markdown files
    md_files = list(docs_dir.glob("**/*.md"))
    if not md_files:
        print_warning("No markdown (.md) files found under 'docs/' directory.")
        return
        
    print_info(f"Found {len(md_files)} markdown files in docs/.")
    model = get_embedding_model()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    changes_made = False
    
    for file_path in md_files:
        rel_path = file_path.relative_to(Path.cwd()) if file_path.is_relative_to(Path.cwd()) else file_path
        mtime = file_path.stat().st_mtime
        
        # Check if file has been modified since last ingest
        cursor.execute("SELECT id, last_modified FROM documents WHERE file_path = ?", (str(rel_path),))
        row = cursor.fetchone()
        
        if row:
            doc_id, last_mod = row
            if last_mod == mtime:
                # No change, skip ingestion
                continue
            else:
                # File modified, delete old chunks first
                print_info(f"File modified: {rel_path}. Re-indexing...")
                cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
                cursor.execute("UPDATE documents SET last_modified = ? WHERE id = ?", (mtime, doc_id))
        else:
            # New file, insert into document table
            print_info(f"New file found: {rel_path}. Indexing...")
            cursor.execute("INSERT INTO documents (file_path, last_modified) VALUES (?, ?)", (str(rel_path), mtime))
            doc_id = cursor.lastrowid
            
        changes_made = True
        chunks = chunk_markdown_file(file_path)
        
        if not chunks:
            continue
            
        # Bulk compute embeddings
        texts = [f"Section: {c['title']}\n\n{c['content']}" for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Insert chunks
        for chunk, embedding in zip(chunks, embeddings):
            # Serialize embedding vector as a standard binary float32 float list
            emb_blob = embedding.astype(np.float32).tobytes()
            cursor.execute("""
            INSERT INTO chunks (document_id, title, content, start_line, end_line, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, chunk["title"], chunk["content"], chunk["start_line"], chunk["end_line"], emb_blob))
            
    conn.commit()
    conn.close()
    
    if changes_made:
        print_success("Ingestion complete. Database is fully up-to-date!")
    else:
        print_success("No changes detected. Database is already fully up-to-date!")

# Subcommand: Query
def cmd_query(args):
    if not Path(DB_FILE).exists():
        print_error("No RAG database found. Please run the ingest command first: python3 jai_rag.py ingest")
        return
        
    query_text = args.query
    top_k = args.top_k
    model_name = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    
    # 1. Embed query locally
    emb_model = get_embedding_model()
    query_emb = emb_model.encode(query_text)
    
    # 2. Fetch all chunks from DB and compute cosine similarity
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT chunks.title, chunks.content, chunks.start_line, chunks.end_line, chunks.embedding, documents.file_path
    FROM chunks
    JOIN documents ON chunks.document_id = documents.id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print_error("No indexed documents found in database. Please index documents first.")
        return
        
    scored_chunks = []
    for title, content, start_line, end_line, emb_blob, file_path in rows:
        chunk_emb = np.frombuffer(emb_blob, dtype=np.float32)
        score = cosine_similarity(query_emb, chunk_emb)
        scored_chunks.append({
            "title": title,
            "content": content,
            "start_line": start_line,
            "end_line": end_line,
            "score": score,
            "file_path": file_path
        })
        
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_retrieved = scored_chunks[:top_k]
    
    # If retrieve-only, print chunks and exit
    if args.retrieve_only:
        print(f"\n{Colors.HEADER}=== Retrieved Chunks (Top {len(top_retrieved)}) ==={Colors.ENDC}")
        for i, item in enumerate(top_retrieved, 1):
            print(f"\n{Colors.BOLD}[Chunk {i}] Score: {item['score']:.4f} | {item['file_path']} (Lines {item['start_line']}-{item['end_line']}){Colors.ENDC}")
            print(f"{Colors.OKBLUE}Section: {item['title']}{Colors.ENDC}")
            print("-" * 60)
            print(item['content'])
            print("=" * 80)
        print()
        return

    # Check if API key is missing. If so, fall back to retrieve-only gracefully.
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print_warning("OPENROUTER_API_KEY is not set in environment or .env. Falling back to retrieved snippets:")
        print(f"\n{Colors.HEADER}=== Retrieved Chunks (Top {len(top_retrieved)}) ==={Colors.ENDC}")
        for i, item in enumerate(top_retrieved, 1):
            print(f"\n{Colors.BOLD}[Chunk {i}] Score: {item['score']:.4f} | {item['file_path']} (Lines {item['start_line']}-{item['end_line']}){Colors.ENDC}")
            print(f"{Colors.OKBLUE}Section: {item['title']}{Colors.ENDC}")
            print("-" * 60)
            print(item['content'])
            print("=" * 80)
        print(f"\n{Colors.WARNING}Please configure your OPENROUTER_API_KEY in the .env file to run full LLM generation.{Colors.ENDC}\n")
        return

    # Check if we have any good matches
    if not top_retrieved or top_retrieved[0]["score"] < 0.15:
        print_warning("No highly relevant documentation found in local database. The model will answer with general knowledge.")
        
    # 3. Create RAG prompt
    context_blocks = []
    for i, item in enumerate(top_retrieved, 1):
        context_blocks.append(
            f"--- Snippet {i} ({item['file_path']} Lines {item['start_line']}-{item['end_line']}) ---\n"
            f"Section: {item['title']}\n"
            f"{item['content']}"
        )
    context_text = "\n\n".join(context_blocks)
    
    system_prompt = (
        "You are JAI, the specialized AI assistant for Zerostic. "
        "You are helping developers or administrators understand Zerostic's codebase, specifications, integrations, and business metrics. "
        "Use the provided documentation snippets to answer the user's question accurately. "
        "Adhere strictly to the facts in the context. Do not hallucinate paths, parameter names, or integrations. "
        "If the information is not present in the snippets, clearly state that it is not documented in the provided files.\n\n"
        "--- START LOCAL DOCUMENTATION CONTEXT ---\n"
        f"{context_text}\n"
        "--- END LOCAL DOCUMENTATION CONTEXT ---"
    )
    
    user_prompt = f"Question: {query_text}"
    
    print_info(f"Querying OpenRouter model '{model_name}'...")
    
    client = get_openai_client()
    
    extra_headers = {
        "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
        "X-Title": "Zerostic JAI RAG Suite"
    }
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers=extra_headers,
            temperature=0.2
        )
        answer = response.choices[0].message.content
        
        # Display the result beautifully
        print("\n" + "=" * 40 + f" {Colors.BOLD}JAI RESPONSE{Colors.ENDC} " + "=" * 40)
        print(answer)
        print("=" * 94)
        
        # Display sources bibliographical card
        print(f"\n{Colors.BOLD}Sources Used:{Colors.ENDC}")
        seen_sources = set()
        for item in top_retrieved:
            source_key = (item['file_path'], item['title'])
            if source_key not in seen_sources and item['score'] > 0.2:
                seen_sources.add(source_key)
                print(f"  • [doc] {Colors.OKBLUE}{item['file_path']}{Colors.ENDC} — Section: \"{item['title']}\" (Lines {item['start_line']}-{item['end_line']}) [Relevance: {item['score']:.2f}]")
        print()
                
    except Exception as e:
        print_error(f"Error communicating with OpenRouter: {str(e)}")

# Main entrypoint CLI parsing
def main():
    parser = argparse.ArgumentParser(
        description="Zerostic Documentation JAI RAG CLI Suite",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # Ingest subcommand
    subparsers.add_parser("ingest", help="Scans, chunks, and indexes all .md files in the docs/ directory locally.")
    
    # Query subcommand
    query_parser = subparsers.add_parser("query", help="Asks JAI a question, retrieving information from the local index.")
    query_parser.add_argument("query", type=str, help="The query or question to ask JAI.")
    query_parser.add_argument("--top_k", "-k", type=int, default=4, help="Number of semantic chunks to retrieve as context (default: 4).")
    query_parser.add_argument("--retrieve-only", action="store_true", help="Only retrieve and print matching documentation chunks, without calling the LLM.")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

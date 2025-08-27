# Migration Scripts

This directory contains scripts for migrating data between different vector databases and cloud services.

## ChromaDB to Pinecone Migration

### migrate_chromadb_to_pinecone.py

Migrates the La Plata County code data from the local ChromaDB instance to Pinecone.

**Prerequisites:**
- Pinecone account with API key
- ChromaDB database with existing county code data
- Python packages: `chromadb`, `pinecone-client`

**Environment Variables:**
```bash
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_ENVIRONMENT="us-west-2"  # Optional, defaults to us-west-2
```

**Usage:**
```bash
cd scripts

# Basic usage (migrates county code collection)
python migrate_chromadb_to_pinecone.py

# Specify collection and index names
python migrate_chromadb_to_pinecone.py \
  --chroma-collection la_plata_county_code \
  --pinecone-index la-plata-county-code

# Dry run to check what would be migrated
python migrate_chromadb_to_pinecone.py --dry-run

# For assessor data (later)
python migrate_chromadb_to_pinecone.py \
  --chroma-collection la_plata_assessor \
  --pinecone-index la-plata-assessor-data

# Custom ChromaDB path
python migrate_chromadb_to_pinecone.py \
  --chroma-path /path/to/custom/chroma_db

# Help for all options
python migrate_chromadb_to_pinecone.py --help
```

**What it does:**
1. Connects to the existing ChromaDB at `../chroma_db`
2. Extracts all vectors, metadata, and IDs from the `la_plata_county_code` collection
3. Creates a new Pinecone index called `la-plata-county-code` (1024 dimensions, cosine similarity)
4. Uploads all vectors to Pinecone in batches of 100
5. Validates the migration by comparing document counts
6. Tests basic index functionality

**Output:**
- Creates Pinecone index: `la-plata-county-code`
- Migrates ~1,298 county code sections
- Each vector retains original metadata including full text content

**Notes:**
- Large text metadata (>40KB) is truncated to fit Pinecone limits
- Uses cosine similarity to match ChromaDB default
- Safe to re-run - will use existing index if present
import json
import os
from pathlib import Path
import numpy as np
from tqdm import tqdm
import chromadb
from sentence_transformers import SentenceTransformer
import mlx.core as mx

def load_json_data(file_path):
    """Load and parse the La Plata County code JSON file"""
    print(f"Loading JSON data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to list of text chunks with metadata
    chunks = []
    for section_id, content in data.items():
        chunks.append({
            'id': section_id,
            'text': content,
            'length': len(content)
        })
    
    print(f"Loaded {len(chunks)} sections")
    return chunks

def setup_model():
    """Load the sentence transformer model"""
    print("Loading sentence transformer model...")
    try:
        # Use BAAI/bge-small-en-v1.5 for enhanced semantic search
        model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        print("Model loaded successfully: BAAI/bge-small-en-v1.5")
        print(f"MLX Metal available: {mx.metal.is_available()}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def create_embeddings(chunks, model, batch_size=32):
    """Generate embeddings for text chunks in batches"""
    print(f"Creating embeddings for {len(chunks)} chunks...")
    
    texts = [chunk['text'] for chunk in chunks]
    all_embeddings = []
    
    # Process in batches to manage memory
    for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
        batch_texts = texts[i:i + batch_size]
        
        # Generate embeddings using sentence-transformers
        batch_embeddings = model.encode(
            batch_texts,
            batch_size=len(batch_texts),
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        all_embeddings.extend(batch_embeddings.tolist())
    
    print(f"Generated {len(all_embeddings)} embeddings")
    return all_embeddings

def setup_chroma_db(db_path="./chroma_db"):
    """Initialize ChromaDB for vector storage"""
    print(f"Setting up ChromaDB at {db_path}...")
    
    # Create directory if it doesn't exist
    Path(db_path).mkdir(exist_ok=True)
    
    # Initialize persistent client
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="la_plata_county_code",
        metadata={"description": "La Plata County Land Use Code embeddings"}
    )
    
    print(f"ChromaDB collection ready: {collection.count()} existing documents")
    return collection

def store_embeddings(collection, chunks, embeddings):
    """Store embeddings and metadata in ChromaDB"""
    print("Storing embeddings in ChromaDB...")
    
    # Prepare data for ChromaDB
    ids = [chunk['id'] for chunk in chunks]
    metadatas = [{
        'text': chunk['text'],  # Store full text without truncation
        'full_text_length': chunk['length'],
        'section_id': chunk['id']
    } for chunk in chunks]
    
    # Store in batches to avoid memory issues
    batch_size = 100
    for i in tqdm(range(0, len(ids), batch_size), desc="Storing batches"):
        batch_ids = ids[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        
        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas
        )
    
    print(f"Stored {collection.count()} documents in ChromaDB")

def main():
    # Configuration
    JSON_FILE = "./la_plata_code/full_code.json"
    BATCH_SIZE = 32  # Adjust based on available RAM
    
    # Step 1: Load data
    chunks = load_json_data(JSON_FILE)
    
    # Step 2: Setup model
    model = setup_model()
    
    # Step 3: Create embeddings
    embeddings = create_embeddings(chunks, model, BATCH_SIZE)
    
    # Step 4: Setup vector database
    collection = setup_chroma_db()
    
    # Step 5: Store embeddings
    store_embeddings(collection, chunks, embeddings)
    
    print("✅ Vector embeddings created successfully!")
    print(f"📊 Total sections processed: {len(chunks)}")
    print(f"🗂️  Database location: ./chroma_db")
    print(f"🔍 Ready for semantic search queries")

if __name__ == "__main__":
    main()
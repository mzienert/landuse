import json
import os
import gc
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
        # Use intfloat/e5-large-v2 for 1024D embeddings - better for legal text
        model = SentenceTransformer('intfloat/e5-large-v2')
        print("Model loaded successfully: intfloat/e5-large-v2 (1024 dimensions)")
        print(f"MLX Metal available: {mx.metal.is_available()}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def create_embeddings(chunks, model, micro_batch_size=1):
    """Generate embeddings for text chunks with ultra-aggressive memory management"""
    print(f"Creating embeddings for {len(chunks)} chunks with micro-batch size: {micro_batch_size}")
    
    texts = [chunk['text'] for chunk in chunks]
    all_embeddings = []
    
    # Process one item at a time with maximum memory cleanup
    for i in tqdm(range(len(texts)), desc="Processing items"):
        text = texts[i]
        
        try:
            # Process single item with forced cleanup
            single_embedding = model.encode(
                [text],
                batch_size=1,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,  # Disable normalization to save memory
                device=None,  # Let it auto-detect MPS
                convert_to_tensor=False  # Return numpy directly
            )
            
            # Immediately convert to list and extend
            all_embeddings.extend(single_embedding.tolist())
            
            # Explicit cleanup after each item
            del single_embedding
            del text
            
            # Force garbage collection every 50 items
            if i % 50 == 0:
                gc.collect()
                if i > 0:
                    print(f"  Processed {i}/{len(texts)} items, memory cleanup performed")
                
        except Exception as e:
            print(f"❌ Error processing item {i+1}: {e}")
            print(f"   Skipping text: {texts[i][:100]}...")
            # Skip this text and continue
            continue
    
    # Final cleanup
    gc.collect()
    print(f"Generated {len(all_embeddings)} embeddings")
    return all_embeddings

def setup_chroma_db(db_path="../../../chroma_db"):
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
    # Configuration for ultra-aggressive memory management
    JSON_FILE = "../../../la_plata_code/full_code.json"
    MICRO_BATCH_SIZE = 1  # Single item processing for 1536D embeddings
    
    print("🚀 Starting embedding generation with ULTRA-aggressive memory management")
    print(f"📦 Micro-batch size: {MICRO_BATCH_SIZE} (single item processing)")
    print("💾 Memory optimization: Maximum (single item + forced cleanup)")
    print("⚠️  This will be slower but should avoid memory issues")
    
    # Step 1: Load data
    chunks = load_json_data(JSON_FILE)
    
    # Step 2: Setup model
    model = setup_model()
    
    # Step 3: Create embeddings with micro-batching
    embeddings = create_embeddings(chunks, model, MICRO_BATCH_SIZE)
    
    # Step 4: Setup vector database
    collection = setup_chroma_db()
    
    # Step 5: Store embeddings
    store_embeddings(collection, chunks, embeddings)
    
    print("✅ Vector embeddings created successfully!")
    print(f"📊 Total sections processed: {len(chunks)}")
    print(f"🔢 Vector dimensions: 1024D (e5-large-v2)")
    print(f"🗂️  Database location: ../../../chroma_db")
    print(f"🔍 Ready for semantic search queries")

if __name__ == "__main__":
    main()
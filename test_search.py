import chromadb
from sentence_transformers import SentenceTransformer

# Load model and database
print("Loading model...")
model = SentenceTransformer('intfloat/e5-large-v2')
print("Connecting to database...")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("la_plata_county_code")

print(f"Database contains {collection.count()} documents")

# Test query
query = "building permits and zoning requirements"
print(f"Generating embedding for query: {query}")
query_embedding = model.encode([query]).tolist()[0]

# Search
print("Searching for relevant sections...")
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10
)

print(f"\nQuery: {query}")
print(f"Found {len(results['documents'][0])} relevant sections:")

# Check if we got valid results
if results['ids'][0] and len(results['ids'][0]) > 0:
    for i, section_id in enumerate(results['ids'][0]):
        print(f"\n{i+1}. Section {section_id}:")
        
        # Try to get content from metadata
        if results['metadatas'][0] and i < len(results['metadatas'][0]):
            metadata = results['metadatas'][0][i]
            if metadata and 'text' in metadata:
                text_content = metadata['text']
                print(f"   {text_content[:200]}...")
                print(f"   [Full length: {metadata.get('full_text_length', 'unknown')} chars]")
            else:
                print(f"   [Metadata available but no text field]")
                print(f"   Available metadata keys: {list(metadata.keys()) if metadata else 'None'}")
        else:
            print(f"   [No metadata available]")
        
        # Show distance/similarity score if available
        if results['distances'][0] and i < len(results['distances'][0]):
            distance = results['distances'][0][i]
            print(f"   Distance: {distance:.4f}")
else:
    print("No results found. This might indicate:")
    print("1. The database is empty")
    print("2. The embeddings weren't stored properly")
    print("3. The query didn't match any content")
    
    # Debug info
    print(f"\nDebug info:")
    print(f"Query embedding shape: {len(query_embedding)}")
    print(f"Database count: {collection.count()}")
    
    # Let's check what's actually in the database
    print("\nSample of database content:")
    sample = collection.peek(limit=2)
    print(f"Sample IDs: {sample['ids']}")
    print(f"Sample metadata keys: {[list(m.keys()) if m else 'None' for m in sample['metadatas']] if sample['metadatas'] else 'No metadata'}")
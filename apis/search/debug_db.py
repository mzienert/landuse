import chromadb

# Connect to database
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("la_plata_county_code")

# Get section 87 specifically
results = collection.get(ids=["87"], include=["metadatas"])

if results['ids']:
    metadata = results['metadatas'][0]
    text = metadata['text']
    print(f"Section 87 stored length: {len(text)}")
    print("Last 200 chars stored in DB:")
    print(text[-200:])
    print("Does stored text end with ...?", text.endswith('...'))
    print(f"Full text length metadata: {metadata.get('full_text_length')}")
else:
    print("Section 87 not found in database")
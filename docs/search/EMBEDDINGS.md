# Embeddings and Data Management Guide

## Overview

This guide covers the creation, management, and optimization of vector embeddings for the La Plata County Search API, including both legal code and property assessment data.

## Embedding Architecture

### Model Selection: intfloat/e5-large-v2

**Why this model**:
- **1024 dimensions**: Good balance of quality vs performance
- **Legal text optimized**: Better performance on formal/technical text
- **Retrieval focused**: Specifically trained for search applications
- **Mature model**: Well-tested, stable, good community support

**Technical Specifications**:
- **Type**: BERT-based encoder optimized for retrieval
- **Size**: ~1.3GB model weights
- **Context**: 512 token maximum input length
- **Output**: 1024-dimensional dense vectors
- **Training**: Contrastive learning on web-scale text pairs

### Alternative Models

| Model | Dimensions | Size | Use Case |
|-------|------------|------|----------|
| `intfloat/e5-large-v2` | 1024 | 1.3GB | **Current choice** - legal text |
| `all-MiniLM-L6-v2` | 384 | 80MB | Lightweight, faster inference |
| `all-mpnet-base-v2` | 768 | 420MB | General purpose, good quality |
| `intfloat/e5-base-v2` | 768 | 440MB | Smaller e5 variant |

## Legal Code Embeddings

### Data Source: La Plata County Municipal Code

**Input Data**: `la_plata_code/full_code.json`
```json
{
  "67-4": "Section 67-4. Minor subdivisions. (a) Applicability. This section applies to land divisions that result in...",
  "67-3": "Section 67-3. Major subdivisions. Major subdivisions involve the division of land into four (4) or more lots..."
}
```

**Processing Strategy**: Section-based chunking
- Each legal section becomes one embedding
- Preserves legal document structure
- Maintains citation traceability
- Avoids artificial splits within regulations

### Creating Legal Code Embeddings

#### Basic Creation Process

```bash
# From project root directory
python apis/search/embeddings/create_legal_embeddings.py
```

**Expected Output**:
```
🚀 Starting embedding generation with ULTRA-aggressive memory management
📦 Micro-batch size: 1 (single item processing)
Loading JSON data from ../../../la_plata_code/full_code.json...
Loaded 1298 sections
Loading sentence transformer model...
Model loaded successfully: intfloat/e5-large-v2 (1024 dimensions)
MLX Metal available: True
Creating embeddings for 1298 chunks with micro-batch size: 1
Processing items: 100%|████████████| 1298/1298 [08:45<00:00,  2.47it/s]
Generated 1298 embeddings
Setting up ChromaDB at ../../../chroma_db...
Storing 1298 documents in ChromaDB...
Stored 1298 documents in ChromaDB
✅ Vector embeddings created successfully!
📊 Total sections processed: 1298
🔢 Vector dimensions: 1024D (e5-large-v2)  
🗂️ Database location: ../../../chroma_db
🔍 Ready for semantic search queries
```

#### Processing Details

**Memory Management**: Ultra-aggressive approach for Apple Silicon
```python
# Single-item processing to minimize memory usage
MICRO_BATCH_SIZE = 1
for i in tqdm(range(len(texts)), desc="Processing items"):
    text = texts[i]
    single_embedding = model.encode(
        [text],
        batch_size=1,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False
    )
    all_embeddings.append(single_embedding[0])
    
    # Aggressive cleanup after each item
    del single_embedding
    gc.collect()
```

**Quality Considerations**:
- **Full section text**: No truncation preserves complete legal context
- **Consistent metadata**: Section IDs maintained for citation
- **Error handling**: Graceful handling of malformed sections

### Property Assessment Embeddings

**Input Data**: `LPC-Assessor-Data-Files/AssessorData.mdb`

**Processing Strategy**: Account-based aggregation
- Combines multiple database tables per property
- Creates comprehensive property descriptions
- Includes ownership, location, and assessment data

#### Creating Assessor Embeddings

```bash
# Requires mdb-tools for Access database processing
python apis/search/embeddings/create_assessor_embeddings.py
```

**Processing Pipeline**:
1. **MDB Export**: Convert Access tables to CSV
   ```bash
   mdb-export 'AssessorData.mdb' 'LEGAL' > assessor_csv/LEGAL.csv
   mdb-export 'AssessorData.mdb' 'MAILADDR' > assessor_csv/MAILADDR.csv
   ```

2. **Data Integration**: Combine related records
   ```python
   property_text = f"""
   Account: {account_number}
   Owner: {owner_name}
   Property: {property_address}
   Description: {legal_description}
   Assessment: ${assessed_value}
   """
   ```

3. **Embedding Generation**: Same model as legal code
   - 1024D vectors for consistency
   - Account-level granularity
   - Rich metadata preservation

**Expected Results**:
- ~46,000 property records processed
- Combined text descriptions averaging 150-300 characters
- Searchable by owner name, address, or property characteristics

## ChromaDB Storage

### Database Schema

#### Legal Code Collection (`la_plata_county_code`)
```python
collection.add(
    documents=[section_text],
    metadatas=[{
        'text': section_text,
        'full_text_length': len(section_text),
        'section_id': section_id,
        'collection': 'la_plata_county_code'
    }],
    ids=[section_id],
    embeddings=[embedding_vector]  # 1024D float32
)
```

#### Property Assessment Collection (`la_plata_assessor`)  
```python
collection.add(
    documents=[property_description],
    metadatas=[{
        'text': property_description,
        'account_number': account_id,
        'text_length': len(property_description),
        'collection': 'la_plata_assessor'
    }],
    ids=[account_id],
    embeddings=[embedding_vector]  # 1024D float32
)
```

### Database Performance

**Storage Requirements**:
- **Legal Code**: 1,298 documents × 4KB = ~5MB embeddings
- **Property Data**: 46,230 documents × 4KB = ~185MB embeddings  
- **Index Overhead**: ~30% additional for HNSW index
- **Total**: ~250MB for full database

**Query Performance**:
- **Cold start**: 100-200ms (first query after restart)
- **Warm queries**: 20-50ms typical
- **Concurrent queries**: Well-supported up to 20+ simultaneous
- **Memory usage**: ~500MB loaded index

## Quality and Optimization

### Embedding Quality Metrics

#### Semantic Coherence Test
```python
def test_embedding_quality():
    # Test similar concepts cluster together
    queries = [
        "building permit requirements",
        "construction permit needed", 
        "permit for building structure"
    ]
    
    results = []
    for query in queries:
        embedding = model.encode([query])[0]
        results.append(embedding)
    
    # Calculate pairwise similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(results)
    print(f"Average similarity: {similarities.mean():.3f}")
    # Should be >0.8 for good embeddings
```

#### Domain Coverage Analysis
```python
def analyze_coverage():
    # Sample queries across legal domains
    test_queries = [
        "building permits",      # Construction
        "zoning residential",    # Land use  
        "subdivision minor",     # Development
        "property assessment",   # Taxation
        "variance application"   # Exceptions
    ]
    
    for query in test_queries:
        results = search_api.search_simple(query, num_results=5)
        relevance_scores = [float(r['relevance']) for r in results]
        print(f"{query}: avg={np.mean(relevance_scores):.3f}, min={min(relevance_scores):.3f}")
```

### Performance Optimization

#### Model Optimization
```python
# For faster inference (trade quality for speed)
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384D, much faster

# For better quality (slower inference)  
model = SentenceTransformer('intfloat/e5-large-v2')  # 1024D, current choice

# Memory optimization during creation
torch.cuda.empty_cache()  # If using CUDA
import gc; gc.collect()   # Aggressive cleanup
```

#### Database Optimization
```python
# ChromaDB performance tuning
collection = client.create_collection(
    name="collection_name",
    metadata={
        "hnsw:space": "cosine",           # Distance metric
        "hnsw:M": 16,                     # Index connectivity (default: 16)
        "hnsw:ef_construction": 200,      # Build quality (default: 200)
        "hnsw:ef": 10,                    # Search quality (default: 10)
    }
)
```

## Maintenance and Updates

### Data Refresh Procedures

#### Adding New Legal Sections
```bash
# 1. Update source data
# Edit la_plata_code/full_code.json with new sections

# 2. Backup existing database
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d)

# 3. Recreate embeddings (incremental update not currently supported)
python apis/search/embeddings/create_legal_embeddings.py

# 4. Restart search API
./scripts/api.sh restart

# 5. Verify new content
curl "http://localhost:8000/search/simple?query=new%20section%20topic"
```

#### Property Data Updates
```bash
# 1. Replace assessor database
# Update LPC-Assessor-Data-Files/AssessorData.mdb

# 2. Clear old collection
python apis/search/delete_assessor_collection.py

# 3. Recreate embeddings
python apis/search/embeddings/create_assessor_embeddings.py

# 4. Verify update
curl http://localhost:8000/collections | grep assessor
```

### Model Updates

#### Upgrading Embedding Model
```python
# 1. Update model name in embedding scripts
OLD_MODEL = 'intfloat/e5-large-v2'  
NEW_MODEL = 'intfloat/e5-large-v2'  # Or newer version

# 2. Update search API configuration
AVAILABLE_COLLECTIONS = {
    'la_plata_county_code': {
        'model': NEW_MODEL,  # Update model reference
        'dimensions': 1024,  # Update if dimensions change
    }
}

# 3. Recreate all embeddings (required for model changes)
rm -rf chroma_db/
python apis/search/embeddings/create_legal_embeddings.py
python apis/search/embeddings/create_assessor_embeddings.py

# 4. Test compatibility
./scripts/api.sh restart
curl "http://localhost:8000/search/simple?query=test"
```

### Quality Monitoring

#### Automated Quality Checks
```python
#!/usr/bin/env python3
# quality_monitor.py - Run weekly to check embedding quality

import requests
import numpy as np

def quality_check():
    """Check search quality across key legal domains"""
    
    test_cases = [
        ("building permit", "18-35"),           # Should find building regulations
        ("minor subdivision", "67-4"),          # Should find subdivision rules  
        ("zoning commercial", "commercial"),    # Should find zoning info
        ("property assessment", "assessment"),  # Should find assessor data
    ]
    
    issues = []
    for query, expected_content in test_cases:
        try:
            response = requests.get(f"http://localhost:8000/search/simple?query={query}&num_results=5")
            results = response.json()['results']
            
            # Check if any result contains expected content
            found = any(expected_content.lower() in r['text'].lower() for r in results)
            if not found:
                issues.append(f"Query '{query}' did not find expected content '{expected_content}'")
                
            # Check relevance scores
            scores = [float(r['relevance']) for r in results]
            if scores and max(scores) < 0.7:
                issues.append(f"Query '{query}' has low max relevance: {max(scores):.3f}")
                
        except Exception as e:
            issues.append(f"Query '{query}' failed: {e}")
    
    if issues:
        print("❌ Quality issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All quality checks passed")
        return True

if __name__ == "__main__":
    quality_check()
```

#### Performance Monitoring
```bash
#!/bin/bash
# performance_monitor.sh - Run daily to check response times

echo "Search API Performance Check - $(date)"

# Test response times for common queries
queries=("building" "permit" "subdivision" "zoning" "property")

total_time=0
query_count=0

for query in "${queries[@]}"; do
    echo -n "Testing '$query': "
    
    # Measure response time
    response_time=$(curl -w "%{time_total}" -s -o /dev/null \
        "http://localhost:8000/search/simple?query=$query&num_results=5")
    
    echo "${response_time}s"
    
    # Add to average calculation  
    total_time=$(echo "$total_time + $response_time" | bc -l)
    query_count=$((query_count + 1))
done

# Calculate average
avg_time=$(echo "scale=3; $total_time / $query_count" | bc -l)
echo "Average response time: ${avg_time}s"

# Alert if too slow
if (( $(echo "$avg_time > 1.0" | bc -l) )); then
    echo "⚠️  WARNING: Average response time above 1.0s"
    echo "Consider restarting service or checking system resources"
fi
```

## Troubleshooting Embedding Issues

### Common Problems

#### Out of Memory During Creation
**Error**: `RuntimeError: [enforce fail at alloc_cpu.cpp:64] posix_memalign. DefaultCPUAllocator`

**Solutions**:
```bash
# 1. Use smaller batch size (already set to 1 in scripts)
MICRO_BATCH_SIZE = 1

# 2. Close other applications
# 3. Use smaller model temporarily
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384D instead of 1024D

# 4. Process in smaller chunks
# Split data into multiple runs if necessary
```

#### Corrupted Embeddings
**Symptoms**: Search returns random results, poor relevance scores

**Diagnosis**:
```python
# Check embedding dimensions
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("la_plata_county_code")

# Get sample embedding
sample = collection.get(ids=["67-4"], include=["embeddings"])
if sample['embeddings']:
    embedding = sample['embeddings'][0]
    print(f"Embedding dimensions: {len(embedding)}")
    print(f"Embedding range: {min(embedding):.3f} to {max(embedding):.3f}")
    print(f"Embedding norm: {np.linalg.norm(embedding):.3f}")
```

**Recovery**:
```bash
# Delete corrupted collection
rm -rf chroma_db/

# Recreate from scratch  
python apis/search/embeddings/create_legal_embeddings.py

# Verify quality
curl "http://localhost:8000/search/simple?query=building&num_results=1"
```

This comprehensive guide provides everything needed to understand, create, and maintain high-quality embeddings for the La Plata County Search API.
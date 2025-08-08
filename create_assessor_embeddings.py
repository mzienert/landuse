#!/usr/bin/env python3
"""
Create embeddings from La Plata County Assessor database
Combines multiple tables to create comprehensive property descriptions
"""

import subprocess
import os
import json
import csv
import gc
from pathlib import Path
from tqdm import tqdm
import chromadb
from sentence_transformers import SentenceTransformer

def run_mdb_export(mdb_path, table_name, output_dir="assessor_csv"):
    """Export a table from MDB to CSV"""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = f"{output_dir}/{table_name}.csv"
    
    cmd = f"mdb-export '{mdb_path}' '{table_name}' > '{csv_path}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        print(f"✅ Exported {table_name} to {csv_path}")
        return csv_path
    else:
        print(f"❌ Failed to export {table_name}: {result.stderr}")
        return None

def load_csv_data(csv_path):
    """Load CSV data into a dictionary keyed by account number"""
    if not os.path.exists(csv_path):
        return {}
    
    data = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use various possible account number field names
                account_key = None
                for key in ['Account_No', 'ACCOUNT_NO', 'ACCOUNTNUMBER']:
                    if key in row and row[key]:
                        account_key = row[key]
                        break
                
                if account_key:
                    # Store multiple records per account if needed
                    if account_key not in data:
                        data[account_key] = []
                    data[account_key].append(row)
        
        print(f"Loaded {len(data)} unique accounts from {csv_path}")
        return data
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        return {}

def create_property_description(account_no, mailaddr_data, legal_data, livalue_data, archyear_data, classuse_data):
    """Create a comprehensive text description for a property"""
    description_parts = []
    
    # Start with account number
    description_parts.append(f"Property Account: {account_no}")
    
    # Owner and address information from MAILADDR
    if account_no in mailaddr_data:
        mail_info = mailaddr_data[account_no][0]  # Take first record
        
        owner_name = mail_info.get('Name', '').strip()
        if owner_name:
            description_parts.append(f"Owner: {owner_name}")
        
        # Property address
        addr_parts = []
        for addr_field in ['Addr_1', 'Addr_2']:
            addr = mail_info.get(addr_field, '').strip()
            if addr:
                addr_parts.append(addr)
        
        city = mail_info.get('City', '').strip()
        state = mail_info.get('State', '').strip()
        zip_code = mail_info.get('Zip', '').strip()
        
        if addr_parts or city:
            full_address = ', '.join(addr_parts)
            if city:
                full_address += f", {city}"
            if state:
                full_address += f", {state}"
            if zip_code:
                full_address += f" {zip_code}"
            description_parts.append(f"Property Address: {full_address}")
        
        # Parcel and tax information
        parcel_no = mail_info.get('Parcel_No', '').strip()
        if parcel_no:
            description_parts.append(f"Parcel Number: {parcel_no}")
        
        tax_dist = mail_info.get('Tax_Dist', '').strip()
        if tax_dist:
            description_parts.append(f"Tax District: {tax_dist}")
        
        acct_type = mail_info.get('AcctType', '').strip()
        if acct_type:
            description_parts.append(f"Account Type: {acct_type}")
    
    # Legal description from LEGAL
    if account_no in legal_data:
        legal_info = legal_data[account_no][0]
        legal_desc = legal_info.get('LEGAL_DESC', '').strip()
        if legal_desc:
            description_parts.append(f"Legal Description: {legal_desc}")
    
    # Property values from LIVALUE
    if account_no in livalue_data:
        value_info = livalue_data[account_no][0]
        
        land_act = value_info.get('LAND_ACT', '0').replace('$', '').replace(',', '')
        impv_act = value_info.get('IMPV_ACT', '0').replace('$', '').replace(',', '')
        
        try:
            land_actual = float(land_act) if land_act else 0
            impv_actual = float(impv_act) if impv_act else 0
            total_actual = land_actual + impv_actual
            
            if total_actual > 0:
                description_parts.append(f"Actual Value: ${total_actual:,.0f}")
        except:
            pass
    
    # Building details from ARCHYEAR
    if account_no in archyear_data:
        arch_info = archyear_data[account_no][0]  # Take first building
        
        building_parts = []
        
        year_built = arch_info.get('ACTUAL_YEAR_BLT', '').strip()
        if year_built and year_built != '0':
            building_parts.append(f"Built: {year_built}")
        
        building_desc = arch_info.get('BUILDING_DESC', '').strip()
        if building_desc:
            building_parts.append(f"Type: {building_desc}")
        
        bedrooms = arch_info.get('BEDROOMS', '').strip()
        bathrooms = arch_info.get('BATHROOMS', '').strip()
        if bedrooms and bedrooms != '0':
            building_parts.append(f"{bedrooms} bed")
        if bathrooms and bathrooms != '0':
            building_parts.append(f"{bathrooms} bath")
        
        sqft = arch_info.get('IMPSQFT', '').strip()
        if sqft and sqft != '0':
            building_parts.append(f"{sqft} sq ft")
        
        if building_parts:
            description_parts.append(f"Building: {', '.join(building_parts)}")
    
    # Join all parts with proper formatting
    full_description = '\n'.join(description_parts)
    
    return full_description

def setup_model():
    """Load the sentence transformer model - using medium dimension model"""
    print("Loading sentence transformer model...")
    try:
        model = SentenceTransformer('intfloat/e5-large-v2')  # 1024 dimensions - better for structured data
        print("Model loaded successfully: e5-large-v2 (1024 dimensions)")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise

def create_embeddings(property_descriptions, model, batch_size=50):
    """Generate embeddings for property descriptions with memory management"""
    print(f"Creating embeddings for {len(property_descriptions)} properties with batch size: {batch_size}")
    
    accounts = list(property_descriptions.keys())
    descriptions = [property_descriptions[account] for account in accounts]
    all_embeddings = []
    
    # Process in batches with memory management
    for i in tqdm(range(0, len(descriptions), batch_size), desc="Processing batches"):
        batch_descriptions = descriptions[i:i + batch_size]
        
        try:
            batch_embeddings = model.encode(
                batch_descriptions,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
                device=None,  # Auto-detect MPS
                convert_to_tensor=False
            )
            
            all_embeddings.extend(batch_embeddings.tolist())
            
            # Memory cleanup every 20 batches
            if (i // batch_size) % 20 == 0:
                gc.collect()
                
        except Exception as e:
            print(f"❌ Error processing batch {i//batch_size}: {e}")
            continue
    
    gc.collect()
    print(f"Generated {len(all_embeddings)} embeddings")
    return accounts, all_embeddings

def setup_chroma_db(db_path="./chroma_db"):
    """Initialize ChromaDB for vector storage"""
    print(f"Setting up ChromaDB at {db_path}...")
    
    Path(db_path).mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or get collection for assessor data
    collection = client.get_or_create_collection(
        name="la_plata_assessor",
        metadata={"description": "La Plata County Assessor property data embeddings"}
    )
    
    print(f"ChromaDB collection ready: {collection.count()} existing documents")
    return collection

def store_embeddings(collection, accounts, embeddings, property_descriptions):
    """Store embeddings and metadata in ChromaDB"""
    print("Storing embeddings in ChromaDB...")
    
    # Prepare data for ChromaDB
    metadatas = []
    for account in accounts:
        description = property_descriptions[account]
        metadatas.append({
            'text': description,
            'account_number': account,
            'text_length': len(description),
            'data_source': 'la_plata_assessor'
        })
    
    # Store in batches
    batch_size = 100
    for i in tqdm(range(0, len(accounts), batch_size), desc="Storing batches"):
        batch_accounts = accounts[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        
        collection.upsert(
            ids=batch_accounts,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas
        )
    
    print(f"Stored {collection.count()} documents in ChromaDB")

def main():
    mdb_path = "./LPC-Assessor-Data-Files/AssessorData.mdb"
    
    if not os.path.exists(mdb_path):
        print(f"❌ MDB file not found: {mdb_path}")
        return
    
    print("🏠 La Plata County Assessor Data → Embeddings")
    print("=" * 50)
    
    # Key tables to export
    key_tables = ['MAILADDR', 'LEGAL', 'LIVALUE', 'ARCHYEAR', 'CLASSUSE']
    
    # Export tables to CSV
    csv_files = {}
    for table in key_tables:
        csv_path = run_mdb_export(mdb_path, table)
        if csv_path:
            csv_files[table] = csv_path
    
    # Load all CSV data
    print("\n📊 Loading CSV data...")
    mailaddr_data = load_csv_data(csv_files.get('MAILADDR'))
    legal_data = load_csv_data(csv_files.get('LEGAL'))
    livalue_data = load_csv_data(csv_files.get('LIVALUE'))
    archyear_data = load_csv_data(csv_files.get('ARCHYEAR'))
    classuse_data = load_csv_data(csv_files.get('CLASSUSE'))
    
    # Get all unique account numbers
    all_accounts = set()
    for data in [mailaddr_data, legal_data, livalue_data, archyear_data, classuse_data]:
        all_accounts.update(data.keys())
    
    print(f"Found {len(all_accounts)} unique property accounts")
    
    # Create property descriptions
    print("\n📝 Creating property descriptions...")
    property_descriptions = {}
    
    for account_no in tqdm(all_accounts, desc="Creating descriptions"):
        description = create_property_description(
            account_no, mailaddr_data, legal_data, livalue_data, archyear_data, classuse_data
        )
        if description.strip():
            property_descriptions[account_no] = description
    
    print(f"Created {len(property_descriptions)} property descriptions")
    
    # Save descriptions for review
    os.makedirs("assessor_data", exist_ok=True)
    with open("assessor_data/property_descriptions.json", "w", encoding="utf-8") as f:
        json.dump(property_descriptions, f, indent=2)
    print("Property descriptions saved to assessor_data/property_descriptions.json")
    
    # Setup model and create embeddings
    model = setup_model()
    accounts, embeddings = create_embeddings(property_descriptions, model)
    
    # Setup vector database and store embeddings
    collection = setup_chroma_db()
    store_embeddings(collection, accounts, embeddings, property_descriptions)
    
    print("\n✅ Assessor embeddings created successfully!")
    print(f"📊 Total properties processed: {len(property_descriptions)}")
    print(f"🔢 Vector dimensions: 768D (all-mpnet-base-v2)")
    print(f"🗂️  Database location: ./chroma_db")
    print(f"🔍 Collection: la_plata_assessor")
    print("Ready for semantic search queries on property data!")

if __name__ == "__main__":
    main()
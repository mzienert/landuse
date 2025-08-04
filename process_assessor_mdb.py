#!/usr/bin/env python3
"""
Process La Plata County Assessor .mdb database file
Extract data and prepare for embedding generation
"""

import sys
import os
import json
from pathlib import Path

# Check if we have the required library for .mdb files
try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    import pypyodbc
    HAS_PYPYODBC = True
except ImportError:
    HAS_PYPYODBC = False

def list_mdb_tables(mdb_path):
    """List all tables in the .mdb file"""
    print(f"Examining MDB file: {mdb_path}")
    
    if not HAS_PYODBC and not HAS_PYPYODBC:
        print("❌ Neither pyodbc nor pypyodbc is available")
        print("Install with: pip install pyodbc")
        print("Note: On macOS, you may need: brew install unixodbc")
        return []
    
    # Try different connection methods
    conn_strings = [
        f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};',
        f'DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={mdb_path};',
        f'Driver={{MDBTools}};DBQ={mdb_path};'
    ]
    
    connection = None
    for conn_str in conn_strings:
        try:
            if HAS_PYODBC:
                connection = pyodbc.connect(conn_str)
            elif HAS_PYPYODBC:
                connection = pypyodbc.connect(conn_str)
            print(f"✅ Connected using: {conn_str[:50]}...")
            break
        except Exception as e:
            print(f"❌ Failed connection attempt: {str(e)[:100]}...")
            continue
    
    if not connection:
        print("❌ Could not connect to MDB file with any method")
        return []
    
    try:
        cursor = connection.cursor()
        
        # Get list of tables
        tables = []
        for table_info in cursor.tables(tableType='TABLE'):
            table_name = table_info.table_name
            if not table_name.startswith('MSys'):  # Skip system tables
                tables.append(table_name)
        
        print(f"\n📊 Found {len(tables)} data tables:")
        for table in tables:
            # Get row count for each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count:,} records")
            except Exception as e:
                print(f"  - {table}: Error counting records ({str(e)[:50]})")
        
        return tables
        
    except Exception as e:
        print(f"❌ Error examining tables: {e}")
        return []
    finally:
        connection.close()

def examine_table_structure(mdb_path, table_name, sample_rows=5):
    """Examine the structure and sample data of a specific table"""
    print(f"\n🔍 Examining table: {table_name}")
    
    if not HAS_PYODBC and not HAS_PYPYODBC:
        return None
    
    conn_strings = [
        f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};',
        f'DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={mdb_path};',
        f'Driver={{MDBTools}};DBQ={mdb_path};'
    ]
    
    connection = None
    for conn_str in conn_strings:
        try:
            if HAS_PYODBC:
                connection = pyodbc.connect(conn_str)
            elif HAS_PYPYODBC:
                connection = pypyodbc.connect(conn_str)
            break
        except:
            continue
    
    if not connection:
        return None
    
    try:
        # Get column information
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM [{table_name}] LIMIT {sample_rows}")
        
        # Get column names and types
        columns = [desc[0] for desc in cursor.description]
        print(f"📋 Columns ({len(columns)}): {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}")
        
        # Get sample rows
        rows = cursor.fetchall()
        print(f"📝 Sample data ({len(rows)} rows):")
        
        for i, row in enumerate(rows):
            print(f"  Row {i+1}:")
            for j, (col, val) in enumerate(zip(columns, row)):
                if j < 5:  # Show first 5 columns
                    val_str = str(val)[:50] if val else 'NULL'
                    print(f"    {col}: {val_str}")
                elif j == 5:
                    print(f"    ... ({len(columns) - 5} more columns)")
                    break
        
        return {'columns': columns, 'sample_rows': rows}
        
    except Exception as e:
        print(f"❌ Error examining table {table_name}: {e}")
        return None
    finally:
        connection.close()

def suggest_embedding_strategy(tables_info):
    """Suggest how to create embeddings from the assessor data"""
    print("\n💡 EMBEDDING STRATEGY SUGGESTIONS:")
    print("=" * 50)
    
    # Common assessor database table patterns
    likely_main_tables = []
    property_tables = []
    lookup_tables = []
    
    for table in tables_info:
        table_lower = table.lower()
        if any(keyword in table_lower for keyword in ['parcel', 'property', 'account', 'real']):
            property_tables.append(table)
        elif any(keyword in table_lower for keyword in ['master', 'main', 'owner']):
            likely_main_tables.append(table)
        elif any(keyword in table_lower for keyword in ['code', 'type', 'class', 'district']):
            lookup_tables.append(table)
    
    print(f"🏠 Likely Property Tables: {property_tables}")
    print(f"📋 Likely Main/Master Tables: {likely_main_tables}")
    print(f"🔍 Likely Lookup Tables: {lookup_tables}")
    
    print("\n📝 RECOMMENDED APPROACH:")
    print("1. Focus on main property/parcel tables for embeddings")
    print("2. Join with lookup tables for meaningful descriptions")
    print("3. Create text descriptions combining:")
    print("   - Property address/location")
    print("   - Owner information")
    print("   - Property characteristics (type, class, size)")
    print("   - Assessment values")
    print("   - Legal descriptions")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Examine key tables in detail")
    print("2. Create JOIN queries to combine related data")
    print("3. Generate text descriptions for each property")
    print("4. Create embeddings similar to land use code process")

def main():
    mdb_path = "./LPC-Assessor-Data-Files/AssessorData.mdb"
    
    if not os.path.exists(mdb_path):
        print(f"❌ MDB file not found: {mdb_path}")
        return
    
    # List all tables
    tables = list_mdb_tables(mdb_path)
    
    if not tables:
        print("❌ No tables found or could not access database")
        return
    
    # Examine structure of key tables
    key_tables = tables[:5]  # Examine first 5 tables
    tables_info = {}
    
    for table in key_tables:
        table_info = examine_table_structure(mdb_path, table)
        if table_info:
            tables_info[table] = table_info
    
    # Suggest embedding strategy
    suggest_embedding_strategy(tables)
    
    print(f"\n✅ Analysis complete. Found {len(tables)} tables in assessor database.")
    print("Review the output above to determine the best approach for creating embeddings.")

if __name__ == "__main__":
    main()
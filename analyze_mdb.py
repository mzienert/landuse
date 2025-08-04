#!/usr/bin/env python3
"""
Analyze La Plata County Assessor .mdb database using mdb-tools
"""

import subprocess
import os
import json

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return None

def check_mdb_tools():
    """Check if mdb-tools is available"""
    result = run_command("which mdb-tables")
    if result:
        print("✅ mdb-tools is available")
        return True
    else:
        print("❌ mdb-tools not found")
        print("Install with: brew install mdb-tools")
        return False

def list_tables(mdb_path):
    """List all tables in the MDB file"""
    print(f"📊 Listing tables in: {mdb_path}")
    
    cmd = f"mdb-tables '{mdb_path}'"
    output = run_command(cmd)
    
    if output:
        tables = [t.strip() for t in output.split() if t.strip()]
        print(f"Found {len(tables)} tables:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")
        return tables
    else:
        print("❌ Could not list tables")
        return []

def examine_table_structure(mdb_path, table_name):
    """Get structure and sample data from a table"""
    print(f"\n🔍 Examining table: {table_name}")
    
    # Get table schema
    schema_cmd = f"mdb-schema '{mdb_path}' -T '{table_name}'"
    schema = run_command(schema_cmd)
    
    if schema:
        print("📋 Table Schema:")
        print(schema)
    
    # Get row count
    count_cmd = f"mdb-count '{mdb_path}' '{table_name}'"
    count = run_command(count_cmd)
    
    if count:
        print(f"📊 Row count: {count}")
    
    # Get sample data (first 5 rows)
    sample_cmd = f"mdb-export '{mdb_path}' '{table_name}' | head -6"  # Header + 5 rows
    sample = run_command(sample_cmd)
    
    if sample:
        print("📝 Sample data:")
        lines = sample.split('\n')
        for i, line in enumerate(lines[:6]):
            if i == 0:
                print(f"  Header: {line}")
            else:
                print(f"  Row {i}: {line[:100]}{'...' if len(line) > 100 else ''}")
    
    return {
        'table_name': table_name,
        'schema': schema,
        'row_count': count,
        'sample_data': sample
    }

def export_table_to_csv(mdb_path, table_name, output_dir="assessor_data"):
    """Export a table to CSV format"""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = f"{output_dir}/{table_name}.csv"
    
    cmd = f"mdb-export '{mdb_path}' '{table_name}' > '{csv_path}'"
    result = run_command(cmd)
    
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        print(f"✅ Exported {table_name} to {csv_path}")
        return csv_path
    else:
        print(f"❌ Failed to export {table_name}")
        return None

def analyze_for_embeddings(tables_info):
    """Analyze tables and suggest embedding strategy"""
    print("\n💡 EMBEDDING STRATEGY ANALYSIS")
    print("=" * 50)
    
    # Categorize tables
    property_tables = []
    lookup_tables = []
    transaction_tables = []
    other_tables = []
    
    for table in tables_info:
        table_lower = table.lower()
        if any(keyword in table_lower for keyword in ['parcel', 'property', 'real', 'account', 'owner']):
            property_tables.append(table)
        elif any(keyword in table_lower for keyword in ['code', 'type', 'class', 'district', 'zone']):
            lookup_tables.append(table)
        elif any(keyword in table_lower for keyword in ['sale', 'transfer', 'history', 'change']):
            transaction_tables.append(table)
        else:
            other_tables.append(table)
    
    print(f"🏠 Property Tables ({len(property_tables)}): {property_tables}")
    print(f"🔍 Lookup Tables ({len(lookup_tables)}): {lookup_tables}")
    print(f"📈 Transaction Tables ({len(transaction_tables)}): {transaction_tables}")
    print(f"📋 Other Tables ({len(other_tables)}): {other_tables}")
    
    print("\n📝 RECOMMENDED EMBEDDING APPROACH:")
    print("1. Export key property tables to CSV")
    print("2. Create comprehensive property descriptions by joining:")
    print("   - Main property/parcel data")
    print("   - Owner information")
    print("   - Property classifications")
    print("   - Assessment values")
    print("   - Legal descriptions")
    print("3. Generate embeddings similar to land use code")
    
    return {
        'property_tables': property_tables,
        'lookup_tables': lookup_tables,
        'transaction_tables': transaction_tables,
        'other_tables': other_tables
    }

def main():
    mdb_path = "./LPC-Assessor-Data-Files/AssessorData.mdb"
    
    if not os.path.exists(mdb_path):
        print(f"❌ MDB file not found: {mdb_path}")
        return
    
    if not check_mdb_tools():
        return
    
    # List all tables
    tables = list_tables(mdb_path)
    
    if not tables:
        return
    
    # Examine first few tables in detail
    tables_info = {}
    key_tables = tables[:5]  # First 5 tables
    
    for table in key_tables:
        info = examine_table_structure(mdb_path, table)
        tables_info[table] = info
    
    # Analyze for embedding strategy
    analysis = analyze_for_embeddings(tables)
    
    # Save analysis results
    output = {
        'all_tables': tables,
        'table_analysis': analysis,
        'detailed_info': tables_info
    }
    
    with open('assessor_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Full results saved to: assessor_analysis.json")
    print(f"📊 Found {len(tables)} tables total")
    
    # Suggest next steps
    print("\n🚀 NEXT STEPS:")
    if analysis['property_tables']:
        print(f"1. Examine these property tables in detail: {analysis['property_tables'][:3]}")
        print("2. Export key tables to CSV for easier processing")
        print("3. Create property descriptions combining multiple tables")
        print("4. Generate embeddings using create_embeddings.py approach")

if __name__ == "__main__":
    main()
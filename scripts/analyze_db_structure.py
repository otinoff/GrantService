#!/usr/bin/env python3
"""
Script to analyze GrantService database structure
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def analyze_database():
    """Analyze database structure and content"""
    
    db_path = Path(__file__).parent.parent / 'data' / 'grantservice.db'
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    db_structure = {
        "database": str(db_path),
        "analyzed_at": datetime.now().isoformat(),
        "tables": {}
    }
    
    for table_name in [t[0] for t in tables]:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        db_structure["tables"][table_name] = {
            "row_count": row_count,
            "columns": [
                {
                    "id": col[0],
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default": col[4],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ],
            "indexes": [
                {
                    "name": idx[1],
                    "unique": bool(idx[2])
                }
                for idx in indexes
            ],
            "foreign_keys": [
                {
                    "id": fk[0],
                    "table": fk[2],
                    "from": fk[3],
                    "to": fk[4]
                }
                for fk in foreign_keys
            ]
        }
        
        # For grant_applications table, get sample data
        if table_name == 'grant_applications' and row_count > 0:
            cursor.execute(f"""
                SELECT id, user_id, created_at, status 
                FROM {table_name} 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            sample_data = cursor.fetchall()
            db_structure["tables"][table_name]["sample_data"] = [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "created_at": row[2],
                    "status": row[3]
                }
                for row in sample_data
            ]
    
    conn.close()
    
    # Save as JSON
    json_path = Path(__file__).parent.parent / 'data' / 'db_structure.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(db_structure, f, ensure_ascii=False, indent=2)
    
    # Create markdown report
    create_markdown_report(db_structure)
    
    print(f"Database analysis complete!")
    print(f"JSON saved to: {json_path}")
    print(f"Markdown report saved to: GrantService/CLAUDE.md")
    
    return db_structure

def create_markdown_report(db_structure):
    """Create markdown report of database structure"""
    
    md_lines = []
    md_lines.append("# GrantService Database Structure")
    md_lines.append("")
    md_lines.append(f"**Database Path:** `{db_structure['database']}`")
    md_lines.append(f"**Analysis Date:** {db_structure['analyzed_at']}")
    md_lines.append(f"**Total Tables:** {len(db_structure['tables'])}")
    md_lines.append("")
    
    # Summary table
    md_lines.append("## Tables Summary")
    md_lines.append("")
    md_lines.append("| Table Name | Row Count | Columns | Indexes | Foreign Keys |")
    md_lines.append("|------------|-----------|---------|---------|--------------|")
    
    for table_name, table_info in db_structure['tables'].items():
        md_lines.append(f"| {table_name} | {table_info['row_count']:,} | {len(table_info['columns'])} | {len(table_info['indexes'])} | {len(table_info['foreign_keys'])} |")
    
    md_lines.append("")
    md_lines.append("## Detailed Table Structures")
    md_lines.append("")
    
    # Detailed structure for each table
    for table_name, table_info in db_structure['tables'].items():
        md_lines.append(f"### 📊 {table_name}")
        md_lines.append("")
        md_lines.append(f"**Rows:** {table_info['row_count']:,}")
        md_lines.append("")
        
        # Columns
        md_lines.append("#### Columns:")
        md_lines.append("")
        md_lines.append("| Column | Type | Not Null | Default | Primary Key |")
        md_lines.append("|--------|------|----------|---------|-------------|")
        
        for col in table_info['columns']:
            pk = "✓" if col['primary_key'] else ""
            nn = "✓" if col['not_null'] else ""
            default = col['default'] if col['default'] else ""
            md_lines.append(f"| {col['name']} | {col['type']} | {nn} | {default} | {pk} |")
        
        md_lines.append("")
        
        # Indexes
        if table_info['indexes']:
            md_lines.append("#### Indexes:")
            for idx in table_info['indexes']:
                unique = "UNIQUE" if idx['unique'] else ""
                md_lines.append(f"- {idx['name']} {unique}")
            md_lines.append("")
        
        # Foreign Keys
        if table_info['foreign_keys']:
            md_lines.append("#### Foreign Keys:")
            for fk in table_info['foreign_keys']:
                md_lines.append(f"- {fk['from']} → {fk['table']}.{fk['to']}")
            md_lines.append("")
        
        # Sample data for grant_applications
        if table_name == 'grant_applications' and 'sample_data' in table_info:
            md_lines.append("#### Sample Data (Latest 5 records):")
            md_lines.append("")
            md_lines.append("| ID | User ID | Created At | Status |")
            md_lines.append("|----|---------|------------|--------|")
            for row in table_info['sample_data']:
                md_lines.append(f"| {row['id']} | {row['user_id']} | {row['created_at']} | {row['status']} |")
            md_lines.append("")
        
        md_lines.append("---")
        md_lines.append("")
    
    # Grant Applications Analysis
    md_lines.append("## 📋 Grant Applications Analysis")
    md_lines.append("")
    
    if 'grant_applications' in db_structure['tables']:
        apps_info = db_structure['tables']['grant_applications']
        md_lines.append(f"**Total Applications:** {apps_info['row_count']}")
        md_lines.append("")
        
        if apps_info['row_count'] > 0:
            md_lines.append("The grant_applications table contains filled grant applications.")
            md_lines.append("Each application is linked to a user and contains:")
            md_lines.append("- Application data in JSON format")
            md_lines.append("- User responses to interview questions")
            md_lines.append("- Status tracking")
            md_lines.append("- Timestamps for creation and updates")
        else:
            md_lines.append("❗ No grant applications found in the database yet.")
    
    md_lines.append("")
    md_lines.append("## 🔍 Key Relationships")
    md_lines.append("")
    md_lines.append("1. **Users ↔ Grant Applications**: One-to-many relationship")
    md_lines.append("2. **Users ↔ User Answers**: Track interview responses")
    md_lines.append("3. **Sessions ↔ Users**: Authentication and session management")
    md_lines.append("4. **Interview Questions ↔ User Answers**: Q&A tracking")
    md_lines.append("5. **Grants ↔ Grant Applications**: Grant program tracking")
    
    # Save markdown
    md_path = Path(__file__).parent.parent / 'CLAUDE.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    return md_path

if __name__ == '__main__':
    analyze_database()
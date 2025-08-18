import os
import sys
import django
from django.conf import settings
from django.db import connections, OperationalError

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ems.settings')
django.setup()

def get_database_info():
    """Get database information from settings"""
    db_info = settings.DATABASES['default']
    return {
        'engine': db_info['ENGINE'],
        'name': db_info['NAME'],
        'host': db_info.get('HOST', 'localhost'),
        'port': db_info.get('PORT', ''),
        'user': db_info.get('USER', '')
    }

def test_database_connection():
    """Test database connection"""
    results = []
    
    for name, connection in connections.databases.items():
        try:
            conn = connections[name]
            conn.ensure_connection()
            
            with conn.cursor() as cursor:
                if 'sqlite' in conn.vendor:
                    cursor.execute("SELECT sqlite_version()")
                    version = cursor.fetchone()[0]
                    db_type = "SQLite"
                elif 'postgresql' in conn.vendor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    db_type = "PostgreSQL"
                elif 'mysql' in conn.vendor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    db_type = "MySQL/MariaDB"
                elif 'mssql' in conn.vendor:
                    cursor.execute("SELECT @@VERSION")
                    version = cursor.fetchone()[0]
                    db_type = "SQL Server" 
                elif any(x in conn.vendor.lower() for x in ['mssql', 'microsoft', 'sql server']):
                    try:
                        cursor.execute("SELECT @@VERSION")
                        version = cursor.fetchone()[0]
                        db_type = "SQL Server"
                    except Exception as e:
                        try:
                            cursor.execute("SELECT SERVERPROPERTY('ProductVersion')")
                            version = cursor.fetchone()[0]
                            db_type = "SQL Server"
                        except:
                            version = f"Could not retrieve version: {str(e)}"
                            db_type = "SQL Server (Microsoft)"
                else:
                    version = "Unknown"
                    db_type = conn.vendor
            results.append({
                'name': name,
                'type': db_type,
                'status': '✅ Connected',
                'version': version,
                'details': get_database_info(),
                'is_usable': conn.is_usable(),
                'error': None
            })
            
        except OperationalError as e:
            results.append({
                'name': name,
                'type': 'Unknown',
                'status': '❌ Connection failed',
                'version': 'N/A',
                'details': get_database_info(),
                'is_usable': False,
                'error': str(e)
            })
    
    return results

def print_results(results):
    """Print formatted results"""
    print("\n" + "="*50)
    print("DATABASE CONNECTION TEST RESULTS".center(50))
    print("="*50)
    
    for db in results:
        print(f"\n🔹 Database: {db['name']}")
        print(f"Type: {db['type']}")
        print(f"Status: {db['status']}")
        print(f"Version: {db['version']}")
        print(f"Is usable: {'Yes' if db['is_usable'] else 'No'}")
        
        if db['error']:
            print(f"Error: {db['error']}")
        
        print("\nConnection details:")
        print(f"Engine: {db['details']['engine']}")
        print(f"Name: {db['details']['name']}")
        print(f"Host: {db['details']['host']}")
        print(f"Port: {db['details']['port'] or 'Default'}")
        print(f"User: {db['details']['user'] or 'Not specified'}")
        
        print("-"*50)

if __name__ == "__main__":
    try:
        db_results = test_database_connection()
        print_results(db_results)
        
        if all(db['is_usable'] for db in db_results):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except Exception as e:
        print(f"Unexpected error occurred: {str(e)}")
        sys.exit(2)  # Unexpected error
#!/usr/bin/env python3
"""
Script to verify the FastAPI setup is correct.
"""

import sys


def check_imports():
    """Check if all required packages can be imported."""
    import importlib
    
    print("Checking required packages...")
    packages = {
        'fastapi': 'FastAPI',
        'pydantic': 'Pydantic',
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'Alembic',
        'elasticsearch': 'Elasticsearch',
        'psycopg2': 'Psycopg2',
        'uvicorn': 'Uvicorn',
    }
    
    failed = []
    for package, name in packages.items():
        try:
            importlib.import_module(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT FOUND")
            failed.append(name)
    
    return len(failed) == 0


def check_app_structure():
    """Check if the application structure is correct."""
    print("\nChecking application structure...")
    from pathlib import Path
    
    required_dirs = [
        'app',
        'app/api',
        'app/api/v1',
        'app/core',
        'app/db',
        'app/models',
        'app/schemas',
        'app/services',
        'alembic',
        'alembic/versions',
    ]
    
    required_files = [
        'app/main.py',
        'app/core/config.py',
        'app/db/base.py',
        'app/db/elasticsearch.py',
        'requirements.txt',
        'docker-compose.yml',
        '.env.example',
        'alembic.ini',
    ]
    
    base_path = Path(__file__).parent
    
    failed = []
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}/")
        else:
            print(f"  ✗ {dir_path}/ - NOT FOUND")
            failed.append(dir_path)
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - NOT FOUND")
            failed.append(file_path)
    
    return len(failed) == 0


def check_app_startup():
    """Check if the FastAPI app can be loaded."""
    print("\nChecking FastAPI application...")
    try:
        from app.main import app
        print(f"  ✓ Application loaded successfully")
        print(f"  ✓ App name: {app.title}")
        print(f"  ✓ App version: {app.version}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to load application: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("FastAPI Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        check_imports(),
        check_app_structure(),
        check_app_startup(),
    ]
    
    print()
    print("=" * 60)
    if all(checks):
        print("✅ All checks passed! Setup is correct.")
        print("=" * 60)
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())

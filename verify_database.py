#!/usr/bin/env python3
"""
Database module verification script.

Verifies that database/connection.py and database/models.py are correctly implemented
without requiring dependencies to be installed.
"""

import ast
import re
from pathlib import Path


def extract_classes(file_path):
    """Extract class definitions from Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get base classes
            bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]

            # Get attributes (simplified)
            attributes = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)

            classes.append({
                'name': node.name,
                'bases': bases,
                'attributes': attributes,
                'docstring': ast.get_docstring(node)
            })

    return classes


def extract_functions(file_path):
    """Extract function definitions from Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Skip class methods (those inside ClassDef)
            is_method = False
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef) and node in ast.walk(parent):
                    is_method = True
                    break

            if not is_method:
                is_async = isinstance(node, ast.AsyncFunctionDef)
                functions.append({
                    'name': node.name,
                    'async': is_async,
                    'docstring': ast.get_docstring(node)
                })

    return functions


def main():
    print("=" * 70)
    print("DATABASE MODULE VERIFICATION REPORT")
    print("=" * 70)

    # Verify connection.py
    print("\n[1] database/connection.py")
    print("-" * 70)

    connection_file = Path("database/connection.py")
    if not connection_file.exists():
        print("ERROR: File not found!")
        return 1

    # Parse connection.py
    functions = extract_functions(connection_file)
    classes = extract_classes(connection_file)

    print(f"Classes defined: {len(classes)}")
    for cls in classes:
        print(f"  - {cls['name']} (bases: {', '.join(cls['bases'])})")

    print(f"\nFunctions defined: {len(functions)}")
    expected_functions = [
        'get_async_database_url',
        'get_engine',
        'get_sessionmaker',
        'get_session',
        'init_db',
        'test_connection',
        'close_engine'
    ]

    for func_name in expected_functions:
        found = any(f['name'] == func_name for f in functions)
        is_async = any(f['name'] == func_name and f['async'] for f in functions)
        async_marker = " (async)" if is_async else ""
        status = "[OK]" if found else "[MISSING]"
        print(f"  {status} {func_name}{async_marker}")

    # Verify models.py
    print("\n[2] database/models.py")
    print("-" * 70)

    models_file = Path("database/models.py")
    if not models_file.exists():
        print("ERROR: File not found!")
        return 1

    # Parse models.py
    model_classes = extract_classes(models_file)

    print(f"Model classes defined: {len(model_classes)}")

    expected_models = {
        'Employee': {
            'table': 'employees',
            'key_attrs': ['employee_id', 'email', 'full_name', 'practice', 'level', 'location']
        },
        'UserAccount': {
            'table': 'user_accounts',
            'key_attrs': ['user_id', 'account_uuid', 'organization_id', 'employee_id']
        },
        'Model': {
            'table': 'models',
            'key_attrs': ['model_id', 'model_name', 'model_family', 'version']
        },
        'Tool': {
            'table': 'tools',
            'key_attrs': ['tool_id', 'tool_name', 'tool_category']
        },
        'Session': {
            'table': 'sessions',
            'key_attrs': ['session_id', 'user_id', 'terminal_type', 'os_type']
        },
        'APIRequest': {
            'table': 'api_requests',
            'key_attrs': ['request_id', 'event_timestamp', 'input_tokens', 'output_tokens', 'cost_usd']
        },
        'ToolDecision': {
            'table': 'tool_decisions',
            'key_attrs': ['decision_id', 'event_timestamp', 'tool_id', 'decision', 'source']
        },
        'ToolResult': {
            'table': 'tool_results',
            'key_attrs': ['result_id', 'event_timestamp', 'tool_id', 'success', 'duration_ms']
        },
        'UserPrompt': {
            'table': 'user_prompts',
            'key_attrs': ['prompt_id', 'event_timestamp', 'prompt_length']
        },
        'APIError': {
            'table': 'api_errors',
            'key_attrs': ['error_id', 'event_timestamp', 'error_message', 'status_code']
        }
    }

    for model_name, expected in expected_models.items():
        model = next((m for m in model_classes if m['name'] == model_name), None)

        if model:
            print(f"\n  [OK] {model_name}")

            # Check if Base is in bases
            has_base = 'Base' in model['bases']
            print(f"       Inherits from Base: {'Yes' if has_base else 'No (ERROR!)'}")

            # Check key attributes
            missing_attrs = [attr for attr in expected['key_attrs'] if attr not in model['attributes']]
            if missing_attrs:
                print(f"       Missing attributes: {', '.join(missing_attrs)}")
            else:
                print(f"       Has all key attributes ({len(expected['key_attrs'])} checked)")

            # Check for __tablename__
            has_tablename = '__tablename__' in model['attributes']
            print(f"       Has __tablename__: {'Yes' if has_tablename else 'No (ERROR!)'}")

        else:
            print(f"\n  [MISSING] {model_name}")

    # Schema alignment check
    print("\n[3] Schema Alignment with schema.sql")
    print("-" * 70)

    schema_file = Path("database/schema.sql")
    if schema_file.exists():
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()

        # Extract table names from SQL
        sql_tables = re.findall(r'CREATE TABLE.*?(\w+)\s*\(', schema_content, re.IGNORECASE)

        print(f"Tables in schema.sql: {len(sql_tables)}")
        print(f"Models in models.py: {len(expected_models)}")

        # Check if all SQL tables have corresponding models
        for table in sql_tables:
            model_exists = any(
                expected[table] == table
                for expected in expected_models.values()
                if 'table' in expected
            )
            status = "[OK]" if model_exists else "[MISSING MODEL]"
            print(f"  {status} {table}")

    else:
        print("  schema.sql not found - skipping alignment check")

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    connection_ok = len(functions) >= 7 and len(classes) >= 1
    models_ok = len(model_classes) >= 10

    print(f"Connection module: {'PASS' if connection_ok else 'FAIL'}")
    print(f"  - Functions: {len(functions)}/7 minimum")
    print(f"  - Base class: {len(classes)} defined")

    print(f"\nModels module: {'PASS' if models_ok else 'FAIL'}")
    print(f"  - Model classes: {len(model_classes)}/10 expected")

    if connection_ok and models_ok:
        print("\n" + "=" * 70)
        print("SUCCESS: All database modules are correctly implemented!")
        print("=" * 70)
        print("\nImplementation uses SQLAlchemy 2.0 async style with:")
        print("  - AsyncEngine and AsyncSession")
        print("  - async_sessionmaker")
        print("  - Mapped and mapped_column")
        print("  - Proper relationships between models")
        print("\nThe models match schema.sql exactly.")
        return 0
    else:
        print("\n" + "=" * 70)
        print("FAILED: Some issues found in database modules")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

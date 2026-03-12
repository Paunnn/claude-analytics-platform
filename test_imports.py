#!/usr/bin/env python3
"""
Test script to verify database module imports work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing database module imports...")
print("=" * 60)

try:
    print("\n1. Testing config import...")
    from config import settings
    print(f"   ✓ Config loaded: {settings.environment}")

    print("\n2. Testing database.connection import...")
    from database.connection import (
        Base,
        get_engine,
        get_sessionmaker,
        get_session,
        init_db,
        test_connection,
        close_engine,
    )
    print("   ✓ Connection module imported successfully")

    print("\n3. Testing database.models import...")
    from database.models import (
        Employee,
        UserAccount,
        Model,
        Tool,
        Session,
        APIRequest,
        ToolDecision,
        ToolResult,
        UserPrompt,
        APIError,
    )
    print("   ✓ Models imported successfully")

    print("\n4. Testing database package import...")
    import database
    print(f"   ✓ Database package imported successfully")
    print(f"   ✓ Available exports: {len(database.__all__)} items")

    print("\n5. Checking model attributes...")
    models_info = [
        ("Employee", Employee, ["employee_id", "email", "full_name", "practice", "level"]),
        ("UserAccount", UserAccount, ["user_id", "account_uuid", "organization_id"]),
        ("Model", Model, ["model_id", "model_name", "model_family"]),
        ("Tool", Tool, ["tool_id", "tool_name", "tool_category"]),
        ("Session", Session, ["session_id", "user_id", "terminal_type"]),
        ("APIRequest", APIRequest, ["request_id", "event_timestamp", "input_tokens", "output_tokens"]),
        ("ToolDecision", ToolDecision, ["decision_id", "tool_id", "decision"]),
        ("ToolResult", ToolResult, ["result_id", "tool_id", "success"]),
        ("UserPrompt", UserPrompt, ["prompt_id", "prompt_length"]),
        ("APIError", APIError, ["error_id", "error_message"]),
    ]

    for model_name, model_class, expected_attrs in models_info:
        # Check tablename
        assert hasattr(model_class, "__tablename__"), f"{model_name} missing __tablename__"

        # Check expected attributes exist
        for attr in expected_attrs:
            assert hasattr(model_class, attr), f"{model_name} missing attribute: {attr}"

        print(f"   ✓ {model_name} - table: {model_class.__tablename__}")

    print("\n6. Checking Base metadata...")
    print(f"   ✓ Base class: {Base.__name__}")
    print(f"   ✓ Registered tables: {len(Base.metadata.tables)}")

    for table_name in sorted(Base.metadata.tables.keys()):
        table = Base.metadata.tables[table_name]
        print(f"     - {table_name} ({len(table.columns)} columns)")

    print("\n" + "=" * 60)
    print("✅ All imports successful! No errors found.")
    print("=" * 60)
    print("\nDatabase module is ready to use.")

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except AttributeError as e:
    print(f"\n❌ Attribute Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

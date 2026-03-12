#!/usr/bin/env python3
"""
Test script for ETL pipeline.

This script runs the complete ETL pipeline and shows statistics.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from etl.pipeline import ETLPipeline


def main():
    """Run the ETL pipeline test."""
    print("="*70)
    print("ETL PIPELINE TEST")
    print("="*70)
    print()

    # Initialize pipeline
    pipeline = ETLPipeline(data_dir="data/raw")

    # Run full pipeline
    try:
        stats = pipeline.run_full_pipeline()

        # Print detailed statistics
        print("\n" + "="*70)
        print("DETAILED STATISTICS")
        print("="*70)

        duration = (stats['end_time'] - stats['start_time']).total_seconds()

        print(f"\nDuration: {duration:.2f} seconds")
        print(f"Total events: {stats['total_events']:,}")
        print(f"\nRecords loaded:")
        print(f"  Employees:      {stats['employees_loaded']:,}")
        print(f"  User accounts:  {stats['user_accounts_loaded']:,}")
        print(f"  Sessions:       {stats['sessions_loaded']:,}")
        print(f"  API requests:   {stats['api_requests_loaded']:,}")
        print(f"  Tool decisions: {stats['tool_decisions_loaded']:,}")
        print(f"  Tool results:   {stats['tool_results_loaded']:,}")
        print(f"  User prompts:   {stats['user_prompts_loaded']:,}")
        print(f"  API errors:     {stats['api_errors_loaded']:,}")

        if stats.get('errors'):
            print(f"\nErrors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")

        print("\n" + "="*70)
        print("ETL PIPELINE TEST COMPLETE")
        print("="*70)

        return 0

    except Exception as e:
        print(f"\nETL Pipeline failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

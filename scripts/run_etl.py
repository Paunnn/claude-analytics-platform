#!/usr/bin/env python3
"""
Run ETL pipeline to load data into database.

This script orchestrates the complete ETL process.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.pipeline import ETLPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the ETL pipeline."""
    logger.info("="*70)
    logger.info(" STARTING ETL PIPELINE")
    logger.info("="*70)

    try:
        # Initialize pipeline
        pipeline = ETLPipeline(data_dir="data/raw")

        # Run full pipeline
        stats = pipeline.run_full_pipeline()

        # Print results
        logger.info("="*70)
        logger.info(" ETL PIPELINE COMPLETE")
        logger.info("="*70)

        logger.info("\n📊 Summary Statistics:")
        logger.info(f"  Total events processed:    {stats.get('total_events', 0):,}")
        logger.info(f"  Employees loaded:          {stats.get('employees_loaded', 0):,}")
        logger.info(f"  Sessions extracted:        {stats.get('sessions_loaded', 0):,}")
        logger.info(f"  API requests loaded:       {stats.get('api_requests_loaded', 0):,}")
        logger.info(f"  Tool decisions loaded:     {stats.get('tool_decisions_loaded', 0):,}")
        logger.info(f"  Tool results loaded:       {stats.get('tool_results_loaded', 0):,}")
        logger.info(f"  User prompts loaded:       {stats.get('user_prompts_loaded', 0):,}")
        logger.info(f"  API errors loaded:         {stats.get('api_errors_loaded', 0):,}")

        logger.info("\n✅ ETL pipeline completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  - Query data: psql -U claude -d claude_analytics")
        logger.info("  - Test API: curl http://localhost:8000/analytics/summary/overview")
        logger.info("  - Open dashboard: http://localhost:8501")

        return 0

    except Exception as e:
        logger.error(f"\n❌ ETL pipeline failed with error:")
        logger.error(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script for analytics modules.

This script tests all analytics functions with real loaded data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analytics.metrics import MetricsEngine
from analytics.aggregations import AggregationEngine


def print_section(title):
    """Print section header."""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def print_df_summary(name, df):
    """Print DataFrame summary."""
    print(f"\n{name}:")
    print(f"  Shape: {df.shape} (rows × columns)")
    print(f"  Columns: {list(df.columns)}")
    if not df.empty:
        print(f"\n  First 3 rows:")
        print(df.head(3).to_string(index=False))
    else:
        print("  (No data)")


def test_metrics():
    """Test MetricsEngine functions."""
    print_section("TESTING METRICS ENGINE")

    metrics = MetricsEngine()

    # Test 1: Token trends by practice
    print("\n[1] token_trends_by_practice()")
    df = metrics.token_trends_by_practice()
    print_df_summary("Token Trends", df)

    # Test 2: Cost by practice and level
    print("\n[2] cost_by_practice_and_level()")
    df = metrics.cost_by_practice_and_level()
    print_df_summary("Cost by Practice & Level", df)

    # Test 3: Peak usage heatmap
    print("\n[3] peak_usage_heatmap()")
    df = metrics.peak_usage_heatmap()
    print_df_summary("Peak Usage Heatmap", df)

    # Test 4: Session duration stats
    print("\n[4] session_duration_stats()")
    df = metrics.session_duration_stats()
    print_df_summary("Session Duration Stats", df)

    # Test 5: Tool success rates
    print("\n[5] tool_success_rates()")
    df = metrics.tool_success_rates()
    print_df_summary("Tool Success Rates", df)

    # Test 6: Cache efficiency by user
    print("\n[6] cache_efficiency_by_user()")
    df = metrics.cache_efficiency_by_user()
    print_df_summary("Cache Efficiency", df)

    # Test 7: Model usage distribution
    print("\n[7] model_usage_distribution()")
    df = metrics.model_usage_distribution()
    print_df_summary("Model Usage Distribution", df)

    # Test 8: Top users by cost
    print("\n[8] top_users_by_cost(n=10)")
    df = metrics.top_users_by_cost(n=10)
    print_df_summary("Top 10 Users by Cost", df)


def test_aggregations():
    """Test AggregationEngine functions."""
    print_section("TESTING AGGREGATION ENGINE")

    agg = AggregationEngine()

    # Test 1: Aggregate by time (daily costs)
    print("\n[1] aggregate_by_time(metric='cost', time_grain='day')")
    df = agg.aggregate_by_time(metric='cost', time_grain='day')
    print_df_summary("Daily Cost Aggregation", df)

    # Test 2: Aggregate by user cohort (level)
    print("\n[2] aggregate_by_user_cohort(cohort_field='level')")
    df = agg.aggregate_by_user_cohort(cohort_field='level')
    print_df_summary("Cohort Analysis by Level", df)

    # Test 3: Aggregate by user cohort (practice)
    print("\n[3] aggregate_by_user_cohort(cohort_field='practice')")
    df = agg.aggregate_by_user_cohort(cohort_field='practice')
    print_df_summary("Cohort Analysis by Practice", df)

    # Test 4: Rolling averages
    print("\n[4] calculate_rolling_averages(metric='cost', window_days=7)")
    df = agg.calculate_rolling_averages(metric='cost', window_days=7)
    print_df_summary("7-Day Rolling Average (Cost)", df)

    # Test 5: Percentiles
    print("\n[5] calculate_percentiles(metric='cost_usd')")
    percentiles = agg.calculate_percentiles(metric='cost_usd', percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    print("\n  Percentiles:")
    for p, value in sorted(percentiles.items()):
        if isinstance(p, float):
            print(f"    p{int(p*100):02d}: ${value:.4f}")
        else:
            print(f"    {p}: ${value:.4f}")

    # Test 6: Tool usage patterns
    print("\n[6] aggregate_tool_usage_patterns()")
    df = agg.aggregate_tool_usage_patterns()
    print_df_summary("Tool Usage Patterns", df)

    # Test 7: Model usage trends
    print("\n[7] aggregate_model_usage_trends()")
    df = agg.aggregate_model_usage_trends()
    print_df_summary("Model Usage Trends", df)

    # Test 8: Hourly patterns
    print("\n[8] aggregate_hourly_patterns()")
    df = agg.aggregate_hourly_patterns()
    print_df_summary("Hourly Patterns", df)

    # Test 9: Practice trends over time
    print("\n[9] aggregate_by_practice_over_time(time_grain='day')")
    df = agg.aggregate_by_practice_over_time(time_grain='day')
    print_df_summary("Practice Trends Over Time", df)


def print_summary_stats():
    """Print overall summary statistics."""
    print_section("SUMMARY STATISTICS")

    metrics = MetricsEngine()

    # Overall totals
    df = metrics.calculate_total_cost()
    if not df.empty:
        row = df.iloc[0]
        print(f"\nOverall Statistics:")
        print(f"  Total Cost:           ${row['total_cost']:,.2f}")
        print(f"  Total Requests:       {row['request_count']:,}")
        print(f"  Avg Cost/Request:     ${row['avg_cost_per_request']:.4f}")
        print(f"  Total Tokens:         {row['total_tokens']:,}")
        print(f"  Unique Users:         {row['unique_users']}")
        print(f"  Unique Sessions:      {row['unique_sessions']}")

    # By practice
    print("\n  Cost by Practice:")
    df = metrics.calculate_total_cost(group_by=['practice'])
    for _, row in df.iterrows():
        print(f"    {row['practice']:20s}: ${row['total_cost']:>10,.2f} ({row['request_count']:>6,} requests)")


def main():
    """Run all analytics tests."""
    print("="*70)
    print(" ANALYTICS MODULE TEST")
    print(" Testing with REAL loaded data")
    print("="*70)

    try:
        # Print summary first
        print_summary_stats()

        # Test metrics
        test_metrics()

        # Test aggregations
        test_aggregations()

        # Final summary
        print_section("TEST COMPLETE")
        print("\n✓ All analytics functions executed successfully!")
        print("\nNext steps:")
        print("  - Review the output above")
        print("  - Use these functions in API endpoints")
        print("  - Create visualizations in Streamlit dashboard")

        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

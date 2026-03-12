#!/usr/bin/env python3
"""
Test script for ML models.

This script tests all 3 ML classes with real loaded data:
1. AnomalyDetector - IsolationForest on daily token usage
2. ForecastModel - Holt-Winters forecasting
3. UserClusterer - KMeans user segmentation
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analytics.ml_models import AnomalyDetector, ForecastModel, UserClusterer


def print_section(title):
    """Print section header."""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def print_df_summary(name, df):
    """Print DataFrame summary."""
    print(f"\n{name}:")
    print(f"  Shape: {df.shape} (rows x columns)")
    print(f"  Columns: {list(df.columns)}")
    if not df.empty:
        print(f"\n  First 5 rows:")
        print(df.head(5).to_string(index=False))
    else:
        print("  (No data)")


def test_anomaly_detector():
    """Test AnomalyDetector class."""
    print_section("TESTING ANOMALY DETECTOR")

    print("\nInitializing AnomalyDetector with contamination=0.05...")
    detector = AnomalyDetector(contamination=0.05)

    print("\nFitting model on daily user token usage...")
    detector.fit()

    print("\nDetecting anomalies...")
    anomalies_df = detector.predict()

    print_df_summary("All Predictions", anomalies_df)

    # Show only anomalies
    anomalies_only = anomalies_df[anomalies_df['is_anomaly']].sort_values('anomaly_score')
    print(f"\n\nAnomalies Detected: {len(anomalies_only)}")
    if not anomalies_only.empty:
        print("\n  Top 5 most anomalous (lowest scores):")
        print(anomalies_only.head(5).to_string(index=False))

        # Statistics
        print(f"\n  Anomaly Statistics:")
        print(f"    Total records: {len(anomalies_df)}")
        print(f"    Anomalies: {len(anomalies_only)} ({len(anomalies_only)/len(anomalies_df)*100:.1f}%)")
        print(f"    Normal: {len(anomalies_df) - len(anomalies_only)} ({(len(anomalies_df)-len(anomalies_only))/len(anomalies_df)*100:.1f}%)")
        print(f"    Min anomaly score: {anomalies_only['anomaly_score'].min():.4f}")
        print(f"    Max anomaly score: {anomalies_only['anomaly_score'].max():.4f}")
        print(f"    Avg token usage (anomalies): {anomalies_only['total_tokens'].mean():,.0f}")
        print(f"    Avg token usage (normal): {anomalies_df[~anomalies_df['is_anomaly']]['total_tokens'].mean():,.0f}")


def test_forecast_model():
    """Test ForecastModel class."""
    print_section("TESTING FORECAST MODEL (HOLT-WINTERS)")

    print("\nInitializing ForecastModel...")
    model = ForecastModel()

    print("\nFitting Holt-Winters Exponential Smoothing on daily totals...")
    model.fit()

    print("\nGenerating 7-day forecast...")
    forecast_df = model.forecast(days=7)

    print_df_summary("7-Day Forecast", forecast_df)

    # Show forecast summary
    if not forecast_df.empty:
        print(f"\n\n  Forecast Summary:")
        print(f"    Total predicted tokens (7 days): {forecast_df['predicted_tokens'].sum():,.0f}")
        print(f"    Avg daily predicted tokens: {forecast_df['predicted_tokens'].mean():,.0f}")
        print(f"    Min daily prediction: {forecast_df['predicted_tokens'].min():,.0f}")
        print(f"    Max daily prediction: {forecast_df['predicted_tokens'].max():,.0f}")

        # Show trend
        first_day = forecast_df['predicted_tokens'].iloc[0]
        last_day = forecast_df['predicted_tokens'].iloc[-1]
        trend = ((last_day - first_day) / first_day) * 100
        print(f"    Trend (day 1 to day 7): {trend:+.1f}%")


def test_user_clusterer():
    """Test UserClusterer class."""
    print_section("TESTING USER CLUSTERER (KMEANS)")

    print("\nInitializing UserClusterer with 4 clusters...")
    clusterer = UserClusterer(n_clusters=4)

    print("\nClustering users based on:")
    print("  - avg_tokens_per_session")
    print("  - sessions_per_day")
    print("  - tool_usage_rate")
    print("  - cache_hit_rate")

    clusters_df = clusterer.fit_predict()

    print_df_summary("User Clusters", clusters_df)

    # Cluster distribution
    print("\n\n  Cluster Distribution:")
    cluster_counts = clusters_df['cluster_label'].value_counts()
    for label, count in cluster_counts.items():
        pct = (count / len(clusters_df)) * 100
        print(f"    {label:15s}: {count:3d} users ({pct:5.1f}%)")

    # Show representative users from each cluster
    print("\n\n  Representative Users from Each Cluster:")
    for label in ['Power User', 'Balanced', 'Tool-Heavy', 'Light User']:
        cluster_users = clusters_df[clusters_df['cluster_label'] == label]
        if not cluster_users.empty:
            print(f"\n  {label} (sample):")
            sample = cluster_users.head(2)
            for _, row in sample.iterrows():
                print(f"    - {row['full_name']:20s} ({row['practice']:25s})")
                print(f"      Tokens/session: {row['avg_tokens_per_session']:8,.0f}  "
                      f"Sessions/day: {row['sessions_per_day']:5.2f}  "
                      f"Tool rate: {row['tool_usage_rate']:5.2f}  "
                      f"Cache hit: {row['cache_hit_rate']:5.2f}")

    # Cluster statistics
    print("\n\n  Cluster Statistics (Averages):")
    cluster_stats = clusters_df.groupby('cluster_label')[
        ['avg_tokens_per_session', 'sessions_per_day', 'tool_usage_rate', 'cache_hit_rate']
    ].mean()
    print(cluster_stats.to_string())


def main():
    """Run all ML model tests."""
    print("="*70)
    print(" ML MODELS TEST")
    print(" Testing with REAL loaded data")
    print("="*70)

    try:
        # Test 1: Anomaly Detector
        test_anomaly_detector()

        # Test 2: Forecast Model
        test_forecast_model()

        # Test 3: User Clusterer
        test_user_clusterer()

        # Final summary
        print_section("TEST COMPLETE")
        print("\nAll ML models executed successfully!")
        print("\nNext steps:")
        print("  - Review the output above")
        print("  - Use these models in API endpoints")
        print("  - Visualize results in Streamlit dashboard")

        return 0

    except Exception as e:
        print(f"\nTest failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Data ingestion module.

This module handles reading raw telemetry data from JSONL and CSV files.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class DataIngester:
    """
    Data ingestion class for reading raw telemetry files.

    This class handles:
    - Reading JSONL telemetry log files
    - Reading CSV employee files
    - Validating file formats
    - Extracting events from log batches
    """

    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize DataIngester.

        Args:
            data_dir: Directory containing raw data files
        """
        self.data_dir = Path(data_dir)
        logger.info(f"DataIngester initialized with data_dir: {self.data_dir}")

    def ingest_telemetry_logs(
        self,
        file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ingest telemetry logs from JSONL file.

        Reads the JSONL file where each line is a log batch containing
        multiple events. Extracts and flattens all events.

        Args:
            file_path: Path to telemetry_logs.jsonl file

        Returns:
            List of event dictionaries

        Example:
            >>> ingester = DataIngester()
            >>> events = ingester.ingest_telemetry_logs()
            >>> print(f"Loaded {len(events)} events")
        """
        if file_path is None:
            file_path = self.data_dir / "telemetry_logs.jsonl"
        else:
            file_path = Path(file_path)

        if not self.validate_file(str(file_path)):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Reading telemetry logs from: {file_path}")

        all_events = []
        batch_count = 0
        error_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse log batch
                    batch = json.loads(line)
                    batch_count += 1

                    # Extract events from logEvents array
                    log_events = batch.get('logEvents', [])

                    for log_event in log_events:
                        try:
                            # Parse the nested message JSON
                            event = self.parse_event(log_event['message'])

                            # Add batch metadata
                            event['_batch_timestamp'] = log_event.get('timestamp')
                            event['_batch_year'] = batch.get('year')
                            event['_batch_month'] = batch.get('month')
                            event['_batch_day'] = batch.get('day')

                            all_events.append(event)

                        except (json.JSONDecodeError, KeyError) as e:
                            error_count += 1
                            logger.warning(
                                f"Failed to parse event in batch {batch_count}, "
                                f"line {line_num}: {e}"
                            )

                except json.JSONDecodeError as e:
                    error_count += 1
                    logger.error(f"Failed to parse batch on line {line_num}: {e}")

                # Log progress every 1000 batches
                if batch_count % 1000 == 0:
                    logger.info(
                        f"Processed {batch_count} batches, "
                        f"extracted {len(all_events)} events"
                    )

        logger.info(
            f"Ingestion complete: {batch_count} batches, "
            f"{len(all_events)} events, {error_count} errors"
        )

        return all_events

    def ingest_employees(
        self,
        file_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Ingest employee data from CSV file.

        Args:
            file_path: Path to employees.csv file

        Returns:
            DataFrame with employee data

        Example:
            >>> ingester = DataIngester()
            >>> employees_df = ingester.ingest_employees()
            >>> print(employees_df.head())
        """
        if file_path is None:
            file_path = self.data_dir / "employees.csv"
        else:
            file_path = Path(file_path)

        if not self.validate_file(str(file_path)):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Reading employees from: {file_path}")

        df = pd.read_csv(file_path)

        logger.info(f"Loaded {len(df)} employee records")

        return df

    def parse_event(self, event_message: str) -> Dict[str, Any]:
        """
        Parse a single event message JSON string.

        Args:
            event_message: JSON string from logEvents[].message

        Returns:
            Parsed event dictionary with body, attributes, scope, resource

        Example:
            >>> event = ingester.parse_event('{"body": "claude_code.api_request", ...}')
            >>> print(event['body'])
        """
        # Parse the JSON message
        event_data = json.loads(event_message)

        # Flatten the structure for easier access
        flattened = {
            'body': event_data.get('body'),
            'attributes': event_data.get('attributes', {}),
            'scope': event_data.get('scope', {}),
            'resource': event_data.get('resource', {})
        }

        return flattened

    def validate_file(self, file_path: str) -> bool:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            True if file is valid, False otherwise

        Example:
            >>> if ingester.validate_file("data/raw/telemetry_logs.jsonl"):
            ...     print("File is valid")
        """
        path = Path(file_path)
        return path.exists() and path.is_file()

    def get_event_count_by_type(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Count events by type.

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary mapping event type to count

        Example:
            >>> events = ingester.ingest_telemetry_logs()
            >>> counts = ingester.get_event_count_by_type(events)
            >>> print(counts)
            {'claude_code.api_request': 1234, 'claude_code.tool_result': 567, ...}
        """
        counts = {}

        for event in events:
            event_type = event.get('body', 'unknown')
            counts[event_type] = counts.get(event_type, 0) + 1

        return counts

"""
Data transformation module.

This module handles cleaning, validation, and transformation
of raw telemetry data into structured formats for database loading.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import logging
import hashlib

logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Data transformation class for cleaning and structuring telemetry data.

    This class handles:
    - Cleaning and validating event data
    - Extracting structured records from nested JSON
    - Type conversions and normalization
    - Data quality checks
    """

    def __init__(self):
        """Initialize DataTransformer."""
        logger.info("DataTransformer initialized")

    def transform_employees(self, employees_df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform employee data.

        Cleans and validates employee records.

        Args:
            employees_df: Raw employee DataFrame

        Returns:
            Cleaned and validated employee DataFrame

        Example:
            >>> transformer = DataTransformer()
            >>> clean_df = transformer.transform_employees(raw_df)
        """
        logger.info(f"Transforming {len(employees_df)} employee records")

        df = employees_df.copy()

        # Ensure required columns exist
        required_cols = ['email', 'full_name', 'practice', 'level', 'location']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Remove duplicates based on email
        initial_count = len(df)
        df = df.drop_duplicates(subset=['email'], keep='first')
        if len(df) < initial_count:
            logger.warning(f"Removed {initial_count - len(df)} duplicate employee records")

        # Clean email addresses
        df['email'] = df['email'].str.strip().str.lower()

        # Validate email format (basic check)
        valid_email_mask = df['email'].str.contains('@', na=False)
        invalid_count = (~valid_email_mask).sum()
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid email addresses, removing them")
            df = df[valid_email_mask]

        logger.info(f"Transformed employees: {len(df)} valid records")

        return df

    def transform_api_requests(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform API request events into structured DataFrame.

        Extracts claude_code.api_request events and creates a DataFrame
        with columns for database insertion.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with API request data

        Example:
            >>> api_df = transformer.transform_api_requests(events)
            >>> print(api_df.columns)
        """
        logger.info("Transforming API request events")

        # Filter API request events
        api_events = [e for e in events if e.get('body') == 'claude_code.api_request']

        if not api_events:
            logger.warning("No API request events found")
            return pd.DataFrame()

        records = []
        for event in api_events:
            attrs = event.get('attributes', {})

            try:
                record = {
                    'event_timestamp': self.parse_timestamp(attrs.get('event.timestamp')),
                    'session_id': attrs.get('session.id'),
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'organization_id': attrs.get('organization.id'),
                    'model_name': attrs.get('model'),
                    'input_tokens': int(attrs.get('input_tokens', 0)),
                    'output_tokens': int(attrs.get('output_tokens', 0)),
                    'cache_read_tokens': int(attrs.get('cache_read_tokens', 0)),
                    'cache_creation_tokens': int(attrs.get('cache_creation_tokens', 0)),
                    'cost_usd': float(attrs.get('cost_usd', 0)),
                    'duration_ms': int(attrs.get('duration_ms', 0)),
                    'terminal_type': attrs.get('terminal.type'),
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to transform API request event: {e}")

        df = pd.DataFrame(records)
        logger.info(f"Transformed {len(df)} API request records")

        return df

    def transform_tool_decisions(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform tool decision events into structured DataFrame.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with tool decision data
        """
        logger.info("Transforming tool decision events")

        tool_events = [e for e in events if e.get('body') == 'claude_code.tool_decision']

        if not tool_events:
            logger.warning("No tool decision events found")
            return pd.DataFrame()

        records = []
        for event in tool_events:
            attrs = event.get('attributes', {})

            try:
                record = {
                    'event_timestamp': self.parse_timestamp(attrs.get('event.timestamp')),
                    'session_id': attrs.get('session.id'),
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'tool_name': attrs.get('tool_name'),
                    'decision': attrs.get('decision'),
                    'source': attrs.get('source'),
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to transform tool decision event: {e}")

        df = pd.DataFrame(records)
        logger.info(f"Transformed {len(df)} tool decision records")

        return df

    def transform_tool_results(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform tool result events into structured DataFrame.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with tool result data
        """
        logger.info("Transforming tool result events")

        tool_events = [e for e in events if e.get('body') == 'claude_code.tool_result']

        if not tool_events:
            logger.warning("No tool result events found")
            return pd.DataFrame()

        records = []
        for event in tool_events:
            attrs = event.get('attributes', {})

            try:
                # Parse success as boolean
                success_str = attrs.get('success', 'false').lower()
                success = success_str in ('true', '1', 'yes')

                record = {
                    'event_timestamp': self.parse_timestamp(attrs.get('event.timestamp')),
                    'session_id': attrs.get('session.id'),
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'tool_name': attrs.get('tool_name'),
                    'decision_type': attrs.get('decision_type'),
                    'decision_source': attrs.get('decision_source'),
                    'success': success,
                    'duration_ms': int(attrs.get('duration_ms', 0)),
                    'result_size_bytes': attrs.get('tool_result_size_bytes'),
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to transform tool result event: {e}")

        df = pd.DataFrame(records)

        # Convert result_size_bytes to int, handle None
        if 'result_size_bytes' in df.columns:
            df['result_size_bytes'] = pd.to_numeric(df['result_size_bytes'], errors='coerce')

        logger.info(f"Transformed {len(df)} tool result records")

        return df

    def transform_user_prompts(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform user prompt events into structured DataFrame.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with user prompt data
        """
        logger.info("Transforming user prompt events")

        prompt_events = [e for e in events if e.get('body') == 'claude_code.user_prompt']

        if not prompt_events:
            logger.warning("No user prompt events found")
            return pd.DataFrame()

        records = []
        for event in prompt_events:
            attrs = event.get('attributes', {})

            try:
                record = {
                    'event_timestamp': self.parse_timestamp(attrs.get('event.timestamp')),
                    'session_id': attrs.get('session.id'),
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'prompt_length': int(attrs.get('prompt_length', 0)),
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to transform user prompt event: {e}")

        df = pd.DataFrame(records)
        logger.info(f"Transformed {len(df)} user prompt records")

        return df

    def transform_api_errors(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Transform API error events into structured DataFrame.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with API error data
        """
        logger.info("Transforming API error events")

        error_events = [e for e in events if e.get('body') == 'claude_code.api_error']

        if not error_events:
            logger.warning("No API error events found")
            return pd.DataFrame()

        records = []
        for event in error_events:
            attrs = event.get('attributes', {})

            try:
                record = {
                    'event_timestamp': self.parse_timestamp(attrs.get('event.timestamp')),
                    'session_id': attrs.get('session.id'),
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'model_name': attrs.get('model'),
                    'error_message': attrs.get('error'),
                    'status_code': attrs.get('status_code'),
                    'attempt': int(attrs.get('attempt', 1)),
                    'duration_ms': int(attrs.get('duration_ms', 0)),
                }
                records.append(record)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to transform API error event: {e}")

        df = pd.DataFrame(records)
        logger.info(f"Transformed {len(df)} API error records")

        return df

    def extract_sessions(
        self,
        events: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Extract unique sessions from events.

        Creates session records with start time, user, and environment info.

        Args:
            events: List of all event dictionaries

        Returns:
            DataFrame with session data
        """
        logger.info("Extracting unique sessions")

        session_data = {}

        for event in events:
            attrs = event.get('attributes', {})
            resource = event.get('resource', {})

            session_id = attrs.get('session.id')
            if not session_id:
                continue

            timestamp = self.parse_timestamp(attrs.get('event.timestamp'))
            if not timestamp:
                continue

            if session_id not in session_data:
                session_data[session_id] = {
                    'session_id': session_id,
                    'user_id': attrs.get('user.id'),
                    'user_email': attrs.get('user.email'),
                    'terminal_type': attrs.get('terminal.type'),
                    'os_type': resource.get('os.type'),
                    'os_version': resource.get('os.version'),
                    'architecture': resource.get('host.arch'),
                    'claude_code_version': resource.get('service.version'),
                    'session_start': timestamp,
                    'session_end': timestamp,
                }
            else:
                # Update session end time to latest event
                if timestamp > session_data[session_id]['session_end']:
                    session_data[session_id]['session_end'] = timestamp

        df = pd.DataFrame(list(session_data.values()))
        logger.info(f"Extracted {len(df)} unique sessions")

        return df

    def extract_user_accounts(
        self,
        events: List[Dict[str, Any]],
        employees_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract user account information from events.

        Links telemetry user IDs to employee records.

        Args:
            events: List of all event dictionaries
            employees_df: Employee DataFrame for linking

        Returns:
            DataFrame with user account data
        """
        logger.info("Extracting user accounts")

        user_data = {}

        for event in events:
            attrs = event.get('attributes', {})
            resource = event.get('resource', {})

            user_id = attrs.get('user.id')
            if not user_id:
                continue

            if user_id not in user_data:
                user_email = attrs.get('user.email', '').strip().lower()

                user_data[user_id] = {
                    'user_id': user_id,
                    'account_uuid': attrs.get('user.account_uuid'),
                    'organization_id': attrs.get('organization.id'),
                    'user_email': user_email,
                    'hostname': resource.get('host.name'),
                    'user_profile': resource.get('user.profile'),
                    'serial_number': resource.get('user.serial'),
                    'practice': resource.get('user.practice'),
                }

        df = pd.DataFrame(list(user_data.values()))

        # Link to employees by email
        if not employees_df.empty and 'email' in employees_df.columns:
            # Ensure lowercase for matching
            employees_df = employees_df.copy()
            employees_df['email'] = employees_df['email'].str.lower()

            # Create a mapping of email to employee_id (assuming we'll have employee_id after DB insert)
            # For now, just keep the email for linking later
            df = df.merge(
                employees_df[['email']],
                left_on='user_email',
                right_on='email',
                how='left'
            )
            df = df.drop(columns=['email'])  # Remove duplicate email column

        logger.info(f"Extracted {len(df)} unique user accounts")

        return df

    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string to datetime object.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Parsed datetime object

        Example:
            >>> dt = transformer.parse_timestamp("2026-02-01T10:30:45.123Z")
        """
        if not timestamp_str:
            return None

        try:
            # Handle ISO format with Z suffix
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'

            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None

    def validate_numeric_field(
        self,
        value: Any,
        field_name: str,
        allow_negative: bool = False
    ) -> Optional[float]:
        """
        Validate and convert numeric fields.

        Args:
            value: Value to validate
            field_name: Name of field for error messages
            allow_negative: Whether negative values are allowed

        Returns:
            Validated numeric value or None if invalid
        """
        if value is None or value == '':
            return None

        try:
            num_value = float(value)
            if not allow_negative and num_value < 0:
                logger.warning(f"Negative value for {field_name}: {num_value}")
                return None
            return num_value
        except (ValueError, TypeError):
            logger.warning(f"Invalid numeric value for {field_name}: {value}")
            return None

    def deduplicate_records(
        self,
        df: pd.DataFrame,
        subset: List[str]
    ) -> pd.DataFrame:
        """
        Remove duplicate records based on subset of columns.

        Args:
            df: DataFrame to deduplicate
            subset: Columns to use for duplicate detection

        Returns:
            Deduplicated DataFrame
        """
        initial_count = len(df)
        df = df.drop_duplicates(subset=subset, keep='first')
        removed = initial_count - len(df)

        if removed > 0:
            logger.info(f"Removed {removed} duplicate records based on {subset}")

        return df

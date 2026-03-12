"""
Data loading module.

This module handles loading transformed data into PostgreSQL database
using sync SQLAlchemy (simpler for batch processing).
"""

from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
import logging

from config import settings


logger = logging.getLogger(__name__)


class DataLoader:
    """
    Data loader class for inserting data into PostgreSQL.

    This class handles:
    - Bulk inserts with pandas to_sql
    - Upsert operations for dimension tables
    - Foreign key resolution
    - Transaction management
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize DataLoader.

        Args:
            db_session: SQLAlchemy database session (sync)
        """
        if db_session is None:
            # Create sync engine
            sync_url = settings.database_url
            # Make sure it's NOT async
            if 'asyncpg' in sync_url:
                sync_url = sync_url.replace('postgresql+asyncpg://', 'postgresql://')

            self.engine = create_engine(
                sync_url,
                echo=settings.log_level == "DEBUG",
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,
            )

            SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
            self.session = SessionLocal()
            self.owns_session = True
        else:
            self.session = db_session
            self.engine = db_session.bind
            self.owns_session = False

        logger.info("DataLoader initialized")

    def __del__(self):
        """Clean up session if we own it."""
        if self.owns_session and hasattr(self, 'session'):
            self.session.close()

    def load_employees(
        self,
        employees_df: pd.DataFrame,
        if_exists: str = "append"
    ) -> int:
        """
        Load employee data into database.

        Uses UPSERT to handle duplicates (ON CONFLICT DO UPDATE).

        Args:
            employees_df: DataFrame with employee data
            if_exists: How to behave if table exists ('fail', 'replace', 'append')

        Returns:
            Number of records loaded

        Example:
            >>> loader = DataLoader()
            >>> count = loader.load_employees(employees_df)
            >>> print(f"Loaded {count} employees")
        """
        if employees_df.empty:
            logger.warning("Empty employees DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(employees_df)} employee records")

        # For employees, we'll do upsert on email
        loaded = 0
        for _, row in employees_df.iterrows():
            try:
                # Use PostgreSQL ON CONFLICT DO UPDATE
                query = text("""
                    INSERT INTO employees (email, full_name, practice, level, location)
                    VALUES (:email, :full_name, :practice, :level, :location)
                    ON CONFLICT (email) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        practice = EXCLUDED.practice,
                        level = EXCLUDED.level,
                        location = EXCLUDED.location,
                        updated_at = CURRENT_TIMESTAMP
                """)

                self.session.execute(query, {
                    'email': row['email'],
                    'full_name': row['full_name'],
                    'practice': row['practice'],
                    'level': row['level'],
                    'location': row['location'],
                })
                loaded += 1

            except Exception as e:
                logger.error(f"Failed to load employee {row.get('email')}: {e}")

        self.session.commit()
        logger.info(f"Successfully loaded {loaded} employees")

        return loaded

    def load_user_accounts(self, user_accounts_df: pd.DataFrame) -> int:
        """
        Load user account data into database.

        Links user accounts to employees by email.

        Args:
            user_accounts_df: DataFrame with user account data

        Returns:
            Number of records loaded
        """
        if user_accounts_df.empty:
            logger.warning("Empty user accounts DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(user_accounts_df)} user account records")

        loaded = 0
        for _, row in user_accounts_df.iterrows():
            try:
                # Get employee_id from email if available
                employee_id = None
                if pd.notna(row.get('user_email')) and row['user_email']:
                    result = self.session.execute(
                        text("SELECT employee_id FROM employees WHERE email = :email"),
                        {'email': row['user_email']}
                    )
                    emp_row = result.fetchone()
                    if emp_row:
                        employee_id = emp_row[0]

                # Upsert user account
                query = text("""
                    INSERT INTO user_accounts
                    (user_id, account_uuid, organization_id, employee_id, hostname, user_profile, serial_number)
                    VALUES (:user_id, :account_uuid, :organization_id, :employee_id, :hostname, :user_profile, :serial_number)
                    ON CONFLICT (user_id) DO UPDATE SET
                        account_uuid = EXCLUDED.account_uuid,
                        organization_id = EXCLUDED.organization_id,
                        employee_id = EXCLUDED.employee_id,
                        hostname = EXCLUDED.hostname,
                        user_profile = EXCLUDED.user_profile,
                        serial_number = EXCLUDED.serial_number
                """)

                self.session.execute(query, {
                    'user_id': row['user_id'],
                    'account_uuid': row.get('account_uuid'),
                    'organization_id': row.get('organization_id'),
                    'employee_id': employee_id,
                    'hostname': row.get('hostname'),
                    'user_profile': row.get('user_profile'),
                    'serial_number': row.get('serial_number'),
                })
                loaded += 1

            except Exception as e:
                logger.error(f"Failed to load user account {row.get('user_id')}: {e}")

        self.session.commit()
        logger.info(f"Successfully loaded {loaded} user accounts")

        return loaded

    def load_sessions(self, sessions_df: pd.DataFrame) -> int:
        """
        Load session data into database.

        Args:
            sessions_df: DataFrame with session data

        Returns:
            Number of records loaded
        """
        if sessions_df.empty:
            logger.warning("Empty sessions DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(sessions_df)} session records")

        # Use pandas to_sql for bulk insert (faster for large datasets)
        try:
            # Prepare DataFrame for insertion
            df = sessions_df.copy()

            # Ensure datetime columns are timezone-aware
            for col in ['session_start', 'session_end']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], utc=True)

            loaded = df.to_sql(
                'sessions',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            logger.info(f"Successfully loaded {loaded if loaded else len(df)} sessions")
            return loaded if loaded else len(df)

        except Exception as e:
            logger.error(f"Failed to bulk load sessions: {e}")
            # Fallback to row-by-row with conflict handling
            return self._load_sessions_with_upsert(sessions_df)

    def _load_sessions_with_upsert(self, sessions_df: pd.DataFrame) -> int:
        """Load sessions with UPSERT for idempotency."""
        loaded = 0
        for _, row in sessions_df.iterrows():
            try:
                query = text("""
                    INSERT INTO sessions
                    (session_id, user_id, terminal_type, os_type, os_version, architecture,
                     claude_code_version, session_start, session_end)
                    VALUES (:session_id, :user_id, :terminal_type, :os_type, :os_version,
                            :architecture, :claude_code_version, :session_start, :session_end)
                    ON CONFLICT (session_id) DO UPDATE SET
                        session_end = EXCLUDED.session_end
                """)

                self.session.execute(query, row.to_dict())
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load session {row.get('session_id')}: {e}")

        self.session.commit()
        return loaded

    def load_api_requests(self, api_requests_df: pd.DataFrame) -> int:
        """
        Load API request events into database.

        Resolves foreign keys for model_id and user_id.

        Args:
            api_requests_df: DataFrame with API request data

        Returns:
            Number of records loaded
        """
        if api_requests_df.empty:
            logger.warning("Empty API requests DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(api_requests_df)} API request records")

        # Resolve model IDs
        df = api_requests_df.copy()
        if 'model_name' in df.columns:
            df['model_id'] = df['model_name'].apply(self._get_model_id)

        # Ensure datetime columns
        if 'event_timestamp' in df.columns:
            df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)

        # Keep only columns that exist in the api_requests table
        valid_columns = [
            'event_timestamp', 'session_id', 'user_id', 'model_id',
            'input_tokens', 'output_tokens', 'cache_read_tokens',
            'cache_creation_tokens', 'cost_usd', 'duration_ms',
        ]
        df = df[[c for c in valid_columns if c in df.columns]]

        # Bulk insert in chunks of 100
        try:
            loaded = 0
            chunk_size = 100
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                chunk.to_sql(
                    'api_requests',
                    con=self.engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                )
                loaded += len(chunk)
                if i % 1000 == 0:
                    logger.info(f"Loaded {i}/{len(df)} api_requests")

            self.session.commit()
            logger.info(f"Successfully loaded {loaded} API requests")
            return loaded

        except Exception as e:
            logger.error(f"Failed to bulk load API requests: {e}")
            self.session.rollback()
            return 0

    def load_tool_decisions(self, tool_decisions_df: pd.DataFrame) -> int:
        """
        Load tool decision events into database.

        Args:
            tool_decisions_df: DataFrame with tool decision data

        Returns:
            Number of records loaded
        """
        if tool_decisions_df.empty:
            logger.warning("Empty tool decisions DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(tool_decisions_df)} tool decision records")

        # Resolve tool IDs
        df = tool_decisions_df.copy()
        if 'tool_name' in df.columns:
            df['tool_id'] = df['tool_name'].apply(self._get_tool_id)

        # Ensure datetime
        if 'event_timestamp' in df.columns:
            df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)

        # Drop temporary columns
        df = df.drop(columns=['tool_name', 'user_email'], errors='ignore')

        # Bulk insert
        try:
            loaded = df.to_sql(
                'tool_decisions',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            self.session.commit()
            logger.info(f"Successfully loaded {loaded if loaded else len(df)} tool decisions")
            return loaded if loaded else len(df)

        except Exception as e:
            logger.error(f"Failed to bulk load tool decisions: {e}")
            self.session.rollback()
            return 0

    def load_tool_results(self, tool_results_df: pd.DataFrame) -> int:
        """
        Load tool result events into database.

        Args:
            tool_results_df: DataFrame with tool result data

        Returns:
            Number of records loaded
        """
        if tool_results_df.empty:
            logger.warning("Empty tool results DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(tool_results_df)} tool result records")

        # Resolve tool IDs
        df = tool_results_df.copy()
        if 'tool_name' in df.columns:
            df['tool_id'] = df['tool_name'].apply(self._get_tool_id)

        # Ensure datetime
        if 'event_timestamp' in df.columns:
            df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)

        # Drop temporary columns
        df = df.drop(columns=['tool_name', 'user_email'], errors='ignore')

        # Bulk insert
        try:
            loaded = df.to_sql(
                'tool_results',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            self.session.commit()
            logger.info(f"Successfully loaded {loaded if loaded else len(df)} tool results")
            return loaded if loaded else len(df)

        except Exception as e:
            logger.error(f"Failed to bulk load tool results: {e}")
            self.session.rollback()
            return 0

    def load_user_prompts(self, user_prompts_df: pd.DataFrame) -> int:
        """
        Load user prompt events into database.

        Args:
            user_prompts_df: DataFrame with user prompt data

        Returns:
            Number of records loaded
        """
        if user_prompts_df.empty:
            logger.warning("Empty user prompts DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(user_prompts_df)} user prompt records")

        df = user_prompts_df.copy()

        # Ensure datetime
        if 'event_timestamp' in df.columns:
            df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)

        # Drop temporary columns
        df = df.drop(columns=['user_email'], errors='ignore')

        # Bulk insert
        try:
            loaded = df.to_sql(
                'user_prompts',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            self.session.commit()
            logger.info(f"Successfully loaded {loaded if loaded else len(df)} user prompts")
            return loaded if loaded else len(df)

        except Exception as e:
            logger.error(f"Failed to bulk load user prompts: {e}")
            self.session.rollback()
            return 0

    def load_api_errors(self, api_errors_df: pd.DataFrame) -> int:
        """
        Load API error events into database.

        Args:
            api_errors_df: DataFrame with API error data

        Returns:
            Number of records loaded
        """
        if api_errors_df.empty:
            logger.warning("Empty API errors DataFrame, skipping")
            return 0

        logger.info(f"Loading {len(api_errors_df)} API error records")

        # Resolve model IDs
        df = api_errors_df.copy()
        if 'model_name' in df.columns:
            df['model_id'] = df['model_name'].apply(self._get_model_id)

        # Ensure datetime
        if 'event_timestamp' in df.columns:
            df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)

        # Drop temporary columns
        df = df.drop(columns=['model_name', 'user_email'], errors='ignore')

        # Bulk insert
        try:
            loaded = df.to_sql(
                'api_errors',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )

            self.session.commit()
            logger.info(f"Successfully loaded {loaded if loaded else len(df)} API errors")
            return loaded if loaded else len(df)

        except Exception as e:
            logger.error(f"Failed to bulk load API errors: {e}")
            self.session.rollback()
            return 0

    def _get_model_id(self, model_name: str) -> Optional[int]:
        """Resolve model name to model ID."""
        if pd.isna(model_name) or not model_name:
            return None

        try:
            result = self.session.execute(
                text("SELECT model_id FROM models WHERE model_name = :name"),
                {'name': model_name}
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"Failed to resolve model ID for '{model_name}': {e}")
            return None

    def _get_tool_id(self, tool_name: str) -> Optional[int]:
        """Resolve tool name to tool ID."""
        if pd.isna(tool_name) or not tool_name:
            return None

        try:
            result = self.session.execute(
                text("SELECT tool_id FROM tools WHERE tool_name = :name"),
                {'name': tool_name}
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"Failed to resolve tool ID for '{tool_name}': {e}")
            return None

    def refresh_materialized_views(self) -> None:
        """
        Refresh all materialized views.

        Should be called after loading data to update aggregated views.

        Example:
            >>> loader.refresh_materialized_views()
            >>> print("Materialized views refreshed")
        """
        logger.info("Refreshing materialized views")

        views = ['daily_user_usage', 'tool_usage_stats']

        for view in views:
            try:
                self.session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                self.session.commit()
                logger.info(f"Refreshed materialized view: {view}")
            except Exception as e:
                logger.error(f"Failed to refresh materialized view {view}: {e}")
                self.session.rollback()

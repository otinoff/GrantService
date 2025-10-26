#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline State Machine - Iteration 52

Manages user pipeline state transitions for interactive grant flow.

States:
- IDLE: User not in pipeline
- ANKETA_IN_PROGRESS: User filling anketa
- ANKETA_COMPLETED: Anketa done, waiting for audit
- AUDIT_COMPLETED: Audit done, waiting for grant generation
- GRANT_COMPLETED: Grant done, waiting for review
- PIPELINE_COMPLETE: All steps done

Author: Claude Code (Iteration 52)
Created: 2025-10-26
Version: 1.0.0
"""

import logging
from enum import Enum
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PipelineState(Enum):
    """Pipeline states for interactive grant flow"""

    IDLE = "idle"
    ANKETA_IN_PROGRESS = "anketa_in_progress"
    ANKETA_COMPLETED = "anketa_completed"
    AUDIT_COMPLETED = "audit_completed"
    GRANT_COMPLETED = "grant_completed"
    PIPELINE_COMPLETE = "pipeline_complete"


class PipelineStateMachine:
    """
    Manages pipeline state transitions

    Responsibilities:
    - Get current state for user
    - Validate state transitions
    - Update state in database
    - Prevent invalid transitions

    Example:
        >>> sm = PipelineStateMachine(db)
        >>> current = sm.get_state(user_id=123)
        >>> if sm.can_transition(123, PipelineState.AUDIT_COMPLETED):
        ...     sm.transition(123, PipelineState.AUDIT_COMPLETED, anketa_id=456)
    """

    # Valid state transitions
    VALID_TRANSITIONS = {
        PipelineState.IDLE: [PipelineState.ANKETA_IN_PROGRESS],
        PipelineState.ANKETA_IN_PROGRESS: [PipelineState.ANKETA_COMPLETED],
        PipelineState.ANKETA_COMPLETED: [PipelineState.AUDIT_COMPLETED],
        PipelineState.AUDIT_COMPLETED: [PipelineState.GRANT_COMPLETED],
        PipelineState.GRANT_COMPLETED: [PipelineState.PIPELINE_COMPLETE],
        PipelineState.PIPELINE_COMPLETE: [PipelineState.IDLE],  # Can restart
    }

    def __init__(self, db):
        """
        Initialize state machine

        Args:
            db: Database instance with state methods
        """
        self.db = db
        logger.info("[STATE_MACHINE] Initialized")

    def get_state(self, user_id: int) -> PipelineState:
        """
        Get current pipeline state for user

        Args:
            user_id: Telegram user ID

        Returns:
            Current PipelineState

        Raises:
            ValueError: If state in DB is invalid
        """
        try:
            # Get from database
            state_str = self.db.get_user_pipeline_state(user_id)

            # Convert to enum
            return PipelineState(state_str)

        except ValueError as e:
            logger.error(f"[ERROR] Invalid pipeline state for user {user_id}: {state_str}")
            # Default to IDLE if invalid
            return PipelineState.IDLE

        except Exception as e:
            logger.error(f"[ERROR] Failed to get pipeline state for user {user_id}: {e}")
            return PipelineState.IDLE

    def can_transition(
        self,
        user_id: int,
        target_state: PipelineState
    ) -> bool:
        """
        Check if transition is valid

        Args:
            user_id: Telegram user ID
            target_state: Target PipelineState

        Returns:
            True if transition is allowed, False otherwise
        """
        current_state = self.get_state(user_id)

        # Check if transition exists in valid transitions
        valid_targets = self.VALID_TRANSITIONS.get(current_state, [])

        return target_state in valid_targets

    def transition(
        self,
        user_id: int,
        target_state: PipelineState,
        anketa_id: Optional[int] = None
    ) -> bool:
        """
        Transition user to new state (with validation)

        Args:
            user_id: Telegram user ID
            target_state: Target PipelineState
            anketa_id: Optional anketa ID (stored in anketa_id_in_progress)

        Returns:
            True if transition successful, False if invalid

        Side effects:
            - Updates pipeline_state in database
            - Updates anketa_id_in_progress
            - Updates pipeline_started_at (if IDLE → ANKETA_IN_PROGRESS)
        """
        current_state = self.get_state(user_id)

        # Validate transition
        if not self.can_transition(user_id, target_state):
            logger.warning(
                f"[INVALID_TRANSITION] User {user_id}: {current_state.value} → {target_state.value}"
            )
            return False

        try:
            # Update database
            self.db.update_user_pipeline_state(
                user_id=user_id,
                new_state=target_state.value,
                anketa_id=anketa_id
            )

            logger.info(
                f"[TRANSITION] User {user_id}: {current_state.value} → {target_state.value}"
            )

            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to transition user {user_id}: {e}")
            return False

    def reset(self, user_id: int):
        """
        Reset pipeline state to IDLE

        Useful for:
        - User wants to start over
        - Error recovery
        - Manual admin intervention

        Args:
            user_id: Telegram user ID
        """
        try:
            self.db.update_user_pipeline_state(
                user_id=user_id,
                new_state=PipelineState.IDLE.value,
                anketa_id=None
            )

            logger.info(f"[RESET] User {user_id} pipeline reset to IDLE")

        except Exception as e:
            logger.error(f"[ERROR] Failed to reset user {user_id}: {e}")

    def get_anketa_in_progress(self, user_id: int) -> Optional[int]:
        """
        Get ID of anketa currently in progress

        Args:
            user_id: Telegram user ID

        Returns:
            Anketa ID or None if no anketa in progress
        """
        try:
            return self.db.get_user_anketa_in_progress(user_id)
        except Exception as e:
            logger.error(f"[ERROR] Failed to get anketa for user {user_id}: {e}")
            return None

    def is_in_pipeline(self, user_id: int) -> bool:
        """
        Check if user is currently in any pipeline stage

        Args:
            user_id: Telegram user ID

        Returns:
            True if user has active pipeline, False if IDLE
        """
        state = self.get_state(user_id)
        return state != PipelineState.IDLE

    def get_next_action(self, user_id: int) -> Optional[str]:
        """
        Get human-readable description of next action

        Useful for displaying to user or in logs.

        Args:
            user_id: Telegram user ID

        Returns:
            Description of next action or None if pipeline complete
        """
        state = self.get_state(user_id)

        action_map = {
            PipelineState.IDLE: "Start new anketa",
            PipelineState.ANKETA_IN_PROGRESS: "Complete anketa",
            PipelineState.ANKETA_COMPLETED: "Click 'Start Audit' button",
            PipelineState.AUDIT_COMPLETED: "Click 'Start Grant' button",
            PipelineState.GRANT_COMPLETED: "Click 'Start Review' button",
            PipelineState.PIPELINE_COMPLETE: "All done! Start new pipeline or exit",
        }

        return action_map.get(state)


# Helper functions for database integration
def ensure_pipeline_state_methods(db):
    """
    Ensure database has required methods for state machine

    Adds methods to db instance if they don't exist.

    Required methods:
    - get_user_pipeline_state(user_id) -> str
    - update_user_pipeline_state(user_id, new_state, anketa_id)
    - get_user_anketa_in_progress(user_id) -> Optional[int]

    Args:
        db: Database instance

    Raises:
        AttributeError: If methods cannot be added
    """
    import psycopg2

    if not hasattr(db, 'get_user_pipeline_state'):
        def get_user_pipeline_state(user_id: int) -> str:
            """Get pipeline_state for user"""
            query = "SELECT pipeline_state FROM users WHERE telegram_id = %s"
            with db.connection.cursor() as cur:
                cur.execute(query, (user_id,))
                result = cur.fetchone()
                return result[0] if result else 'idle'

        db.get_user_pipeline_state = get_user_pipeline_state

    if not hasattr(db, 'update_user_pipeline_state'):
        def update_user_pipeline_state(user_id: int, new_state: str, anketa_id: Optional[int] = None):
            """Update pipeline_state for user"""
            if anketa_id:
                query = """
                    UPDATE users
                    SET pipeline_state = %s,
                        anketa_id_in_progress = %s,
                        pipeline_started_at = CASE
                            WHEN pipeline_state = 'idle' THEN NOW()
                            ELSE pipeline_started_at
                        END
                    WHERE telegram_id = %s
                """
                with db.connection.cursor() as cur:
                    cur.execute(query, (new_state, anketa_id, user_id))
            else:
                query = """
                    UPDATE users
                    SET pipeline_state = %s,
                        anketa_id_in_progress = NULL,
                        pipeline_started_at = NULL
                    WHERE telegram_id = %s
                """
                with db.connection.cursor() as cur:
                    cur.execute(query, (new_state, user_id))

            db.connection.commit()

        db.update_user_pipeline_state = update_user_pipeline_state

    if not hasattr(db, 'get_user_anketa_in_progress'):
        def get_user_anketa_in_progress(user_id: int) -> Optional[int]:
            """Get anketa_id_in_progress for user"""
            query = "SELECT anketa_id_in_progress FROM users WHERE telegram_id = %s"
            with db.connection.cursor() as cur:
                cur.execute(query, (user_id,))
                result = cur.fetchone()
                return result[0] if result and result[0] else None

        db.get_user_anketa_in_progress = get_user_anketa_in_progress

    logger.info("[STATE_MACHINE] Database methods ensured")

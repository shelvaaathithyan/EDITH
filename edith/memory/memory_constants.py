"""
Constants for the Long-Term Memory Subsystem.
"""

from enum import Enum

class MemoryCategory(str, Enum):
    PREFERENCE = "preference"      # Developer choices (e.g. IDE, package manager)
    WORKSPACE = "workspace"        # Known paths and environments
    PROJECT = "project"            # Metadata about specific projects
    RELATIONSHIP = "relationship"  # People, teams, or roles
    COMMAND = "command"            # Frequently or specifically used CLI commands
    HABIT = "habit"                # Repeated workflows or times of day
    FACT = "fact"                  # General explicit knowledge
    ALIAS = "alias"                # Name mappings
    APPLICATION = "application"    # Frequently used desktop applications
    CUSTOM = "custom"              # Catch-all

class MemorySource(str, Enum):
    EXPLICIT = "explicit"          # "Remember that..."
    IMPLICIT = "implicit"          # "I always use Cursor"
    INTERACTION = "interaction"    # Deduced from CLI commands or workflows
    SYSTEM = "system"              # Internal tracking

# Scoring Thresholds
MIN_CONFIDENCE_THRESHOLD = 0.60
AUTO_SAVE_THRESHOLD = 0.85
MAX_CONFIDENCE = 1.0

# Decay Constants
DECAY_RATE_DAYS = 0.05             # 5% decay per day of inactivity

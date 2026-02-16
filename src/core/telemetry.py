"""
Telemetry and Observability for the Long-Form Video Reliability Engine.

This module provides event logging and performance tracking across
the entire pipeline.
"""

import os
import json
from datetime import datetime


class TelemetryService:
    """
    Centralized telemetry service for tracking pipeline events.
    
    Logs all events to a CSV file for analysis and debugging.
    """
    
    def __init__(self):
        """Initialize the telemetry service."""
        self.log_file = "output/telemetry.csv"
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Create the log file with headers if it doesn't exist."""
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("timestamp,scene_id,shot_id,step,status,latency_ms,metadata\n")
    
    def log_event(
        self,
        scene_id: str,
        shot_id: str,
        step: str,
        status: str,
        latency_ms: float = 0,
        metadata: dict = None
    ):
        """
        Log a telemetry event.
        
        Args:
            scene_id: Scene identifier (e.g., "SCENE-001")
            shot_id: Shot identifier (e.g., "SCENE-001-SHOT-001")
            step: Pipeline step name (e.g., "IMAGE_GEN", "VIDEO_GEN", "CRITIC_QA")
            status: Event status (e.g., "SUCCESS", "FAIL", "PASS")
            latency_ms: Operation latency in milliseconds
            metadata: Additional metadata as a dictionary
        """
        # Get current timestamp in ISO format
        timestamp = datetime.now().isoformat()
        
        # Format metadata as JSON string (empty dict if None)
        metadata_str = json.dumps(metadata if metadata is not None else {})
        
        # Escape any commas or quotes in metadata
        metadata_str = metadata_str.replace('"', '""')
        
        # Format the CSV row
        row = f'{timestamp},{scene_id},{shot_id},{step},{status},{latency_ms:.2f},"{metadata_str}"\n'
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(row)


# Global telemetry instance
telemetry = TelemetryService()

"""
Telemetry Service for the Long-Form Video Reliability Engine.

This module handles structured logging of pipeline events, performance metrics,
and reliability statistics to JSON files for post-run analysis.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from threading import Lock


class TelemetryService:
    """
    Handles structured logging of pipeline events and metrics.
    
    Buffers events in memory and writes a comprehensive JSON report
    at the end of the run, including summary statistics.
    """
    
    def __init__(self, output_dir: str = "output/telemetry"):
        """
        Initialize the TelemetryService.
        
        Args:
            output_dir: Directory to store telemetry logs
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate unique run ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"
        self.log_file = os.path.join(self.output_dir, f"{self.run_id}.json")
        
        # Internal buffer
        self.events: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self._lock = Lock()
        
        print(f"[TELEMETRY] Initialized (Run ID: {self.run_id})")
        
    def log_event(
        self,
        event_type: str,
        scene_id: str = "GLOBAL",
        shot_id: str = "GLOBAL",
        step: str = "UNKNOWN",
        status: str = "INFO",
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a structured event to the telemetry buffer.
        
        Args:
            event_type: Category of event (e.g., "GENERATION", "CRITIC", "SYSTEM")
            scene_id: Associated scene identifier
            shot_id: Associated shot identifier
            step: Pipeline step name
            status: Outcome status (SUCCESS, FAILURE, RETRY, INFO)
            latency_ms: Duration of the operation in milliseconds
            metadata: Additional context dictionary
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "scene_id": scene_id,
            "shot_id": shot_id,
            "step": step,
            "status": status,
            "latency_ms": latency_ms,
            "metadata": metadata or {}
        }
        
        with self._lock:
            self.events.append(event)
            
            # Print significant events to console
            if status in ["FAILURE", "RETRY"] or event_type == "CRITIC":
                print(f"[TELEMETRY] {status}: {step} - {metadata.get('reason', '')}")
    
    def save_run(self):
        """
        Calculate summary statistics and write the full run log to JSON.
        """
        with self._lock:
            end_time = time.time()
            total_duration = end_time - self.start_time
            
            # Calculate metrics
            total_events = len(self.events)
            generation_events = [e for e in self.events if e["event_type"] == "GENERATION"]
            critic_events = [e for e in self.events if e["event_type"] == "CRITIC"]
            retry_events = [e for e in self.events if e["status"] == "RETRY"]
            failure_events = [e for e in self.events if e["status"] == "FAILURE"]
            
            # Latency stats
            latencies = [e["latency_ms"] for e in generation_events if e["latency_ms"] > 0]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Success rate calculation
            attempts = len(generation_events)
            failures = len(failure_events)
            success_rate = ((attempts - failures) / attempts * 100) if attempts > 0 else 100.0
            
            summary = {
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(total_duration, 2),
                "total_events": total_events,
                "total_retries": len(retry_events),
                "avg_generation_latency_ms": round(avg_latency, 2),
                "success_rate_percent": round(success_rate, 2),
                "critic_stats": {
                    "total_evaluations": len(critic_events),
                    "pass_count": len([e for e in critic_events if e["status"] == "SUCCESS"]),
                    "fail_count": len([e for e in critic_events if e["status"] == "FAILURE"])
                }
            }
            
            output_data = {
                "summary": summary,
                "events": self.events
            }
            
            try:
                with open(self.log_file, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"\n[TELEMETRY] ✓ Run logs saved to {self.log_file}")
                print(f"[TELEMETRY] Stats: {len(retry_events)} retries, {success_rate:.1f}% success rate")
            except Exception as e:
                print(f"[TELEMETRY] Error saving logs: {e}")


# Global telemetry instance
telemetry = TelemetryService()

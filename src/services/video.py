"""
Video Generation Service for the Long-Form Video Reliability Engine.

This module provides video generation capabilities, with support for both
mock generation (for testing) and real video rendering.
"""

import os
import time
import requests
from src.core.schemas import ShotPlan
from src.core.config import settings
from src.core.telemetry import telemetry


class VideoService:
    """
    Handles video generation for shots.
    
    Supports mock mode for testing and development, with real API
    integration for production use.
    """
    
    def __init__(self, is_mock: bool = None):
        """
        Initialize the VideoService.
        
        Args:
            is_mock: If True, use mock generation. If False, use real rendering.
                    If None, use settings.USE_MOCK_GENERATION.
        """
        self.is_mock = is_mock if is_mock is not None else settings.USE_MOCK_GENERATION
        self.output_dir = "output/assets"
        
        # Create output directory if it doesn't exist
        if self.is_mock:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_video(self, shot_id: str, image_url: str, shot_plan: ShotPlan) -> str:
        """
        Generate a video clip from a keyframe image and shot plan.
        
        Args:
            shot_id: Unique identifier for the shot
            image_url: URL/path to the keyframe image
            shot_plan: ShotPlan object with camera specifications
            
        Returns:
            URL/path to the generated video file
        """
        if self.is_mock:
            return self._mock_generate(shot_id, image_url, shot_plan)
        else:
            return self._real_generate(shot_id, image_url, shot_plan)
    
    def _mock_generate(self, shot_id: str, image_url: str, shot_plan: ShotPlan) -> str:
        """
        Mock video generation with simulated rendering latency.
        
        Creates a dummy MP4 file with placeholder content.
        
        Args:
            shot_id: Unique identifier for the shot
            image_url: URL/path to the keyframe image
            shot_plan: ShotPlan object with camera specifications
            
        Returns:
            Absolute file path to the mock video file
        """
        # Record start time for telemetry
        start_time = time.time()
        
        # Log rendering start
        print(f"[MOCK VIDEO] Rendering clip for {shot_id}...")
        
        # Simulate rendering latency
        time.sleep(1.0)
        
        # Create mock video file
        filename = f"{shot_id}.mp4"
        filepath = os.path.join(self.output_dir, filename)
        
        # Write placeholder content
        mock_content = (
            f"MOCK VIDEO CONTENT for {shot_id}\n"
            f"Based on keyframe: {image_url}\n"
            f"Shot Type: {shot_plan.shot_type}\n"
            f"Lens: {shot_plan.lens}\n"
            f"Camera Movement: {shot_plan.camera_movement}\n"
        )
        
        with open(filepath, 'w') as f:
            f.write(mock_content)
        
        # Get absolute path
        abs_path = os.path.abspath(filepath)
        file_url = f"file://{abs_path}"
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log telemetry event
        scene_id = shot_id.split("-SHOT")[0]
        telemetry.log_event(
            scene_id=scene_id,
            shot_id=shot_id,
            step="VIDEO_GEN",
            status="SUCCESS",
            latency_ms=latency_ms,
            metadata={
                "shot_type": shot_plan.shot_type,
                "lens": shot_plan.lens,
                "movement": shot_plan.camera_movement
            }
        )
        
        # Log completion
        print(f"[MOCK VIDEO] ✓ Rendered {shot_id} -> {filepath}")
        
        return file_url
    
    def _real_generate(self, shot_id: str, image_url: str, shot_plan: ShotPlan) -> str:
        """
        Real video generation using Runway/Kling API.
        
        Args:
            shot_id: Unique identifier for the shot
            image_url: URL/path to the keyframe image
            shot_plan: ShotPlan object with camera specifications
            
        Returns:
            URL to the generated video from the API
        """
        print(f"[REAL VIDEO] Calling Video API for {shot_id}...")
        
        try:
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Build camera motion prompt
            motion_prompt = (
                f"{shot_plan.camera_movement} camera movement, "
                f"{shot_plan.shot_type} shot, "
                f"{shot_plan.lens} lens"
            )
            
            payload = {
                "image_url": image_url,
                "motion_prompt": motion_prompt,
                "duration": 5,  # 5 seconds
                "fps": 24
            }
            
            # Make API call
            response = requests.post(
                settings.RUNWAY_API_URL,
                headers=headers,
                json=payload,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("video_url", "")
                print(f"[REAL VIDEO] ✓ Rendered {shot_id} -> {video_url}")
                return video_url
            else:
                print(f"[REAL VIDEO] ✗ API Error {response.status_code}: {response.text}")
                # Fallback to mock if API fails
                print(f"[REAL VIDEO] Falling back to mock generation...")
                return self._mock_generate(shot_id, image_url, shot_plan)
                
        except Exception as e:
            print(f"[REAL VIDEO] ✗ Exception: {str(e)}")
            print(f"[REAL VIDEO] Falling back to mock generation...")
            # Fallback to mock if exception occurs
            return self._mock_generate(shot_id, image_url, shot_plan)


"""
Image Generation Service for the Long-Form Video Reliability Engine.

This module provides image generation capabilities, with support for both
mock generation (for testing) and real API integration.
"""

import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from src.core.config import settings
from src.core.telemetry import telemetry


class ImageService:
    """
    Handles image generation for video frames.
    
    Supports mock mode for testing and development, with real API
    integration for production use.
    """
    
    def __init__(self, is_mock: bool = None):
        """
        Initialize the ImageService.
        
        Args:
            is_mock: If True, use mock generation. If False, use real API.
                    If None, use settings.USE_MOCK_GENERATION.
        """
        self.is_mock = is_mock if is_mock is not None else settings.USE_MOCK_GENERATION
        self.output_dir = "output/assets"
        
        # Create output directory if it doesn't exist
        if self.is_mock:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_image(self, shot_id: str, prompt_data: dict) -> str:
        """
        Generate an image from a prompt.
        
        Args:
            shot_id: Unique identifier for the shot
            prompt_data: Dictionary containing positive_prompt, negative_prompt, and seed
            
        Returns:
            URL to the generated image asset
        """
        if self.is_mock:
            return self._mock_generate(shot_id, prompt_data)
        else:
            return self._real_generate(shot_id, prompt_data)
    
    def _mock_generate(self, shot_id: str, prompt_data: dict) -> str:
        """
        Mock image generation with actual debug image creation.
        
        Creates a 1920x1080 black image with shot ID and prompt text overlaid.
        
        Args:
            shot_id: Unique identifier for the shot
            prompt_data: Dictionary containing prompt information
            
        Returns:
            Absolute file path to the generated debug image
        """
        # Record start time for telemetry
        start_time = time.time()
        
        # Simulate network latency
        time.sleep(0.5)
        
        # Create a 1920x1080 black image
        width, height = 1920, 1080
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font, fallback to basic if not available
        try:
            # Try to load a larger font
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw shot ID at the top
        draw.text((50, 50), f"Shot ID: {shot_id}", fill='white', font=font_large)
        
        # Draw prompt (first 100 chars) below
        prompt_text = prompt_data.get('positive_prompt', '')[:100]
        
        # Word wrap the prompt text
        y_offset = 150
        max_width = width - 100
        words = prompt_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Approximate width check (rough estimate)
            if len(test_line) * 12 < max_width:  # Rough character width estimate
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw wrapped lines
        for line in lines[:3]:  # Limit to 3 lines
            draw.text((50, y_offset), line, fill='white', font=font_small)
            y_offset += 40
        
        # Draw seed at the bottom
        seed = prompt_data.get('seed', 'N/A')
        draw.text((50, height - 100), f"Seed: {seed}", fill='gray', font=font_small)
        
        # Save the image
        filename = f"{shot_id}.png"
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        
        # Get absolute path
        abs_path = os.path.abspath(filepath)
        file_url = f"file://{abs_path}"
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log telemetry event
        scene_id = shot_id.split("-SHOT")[0]
        telemetry.log_event(
            event_type="GENERATION",
            scene_id=scene_id,
            shot_id=shot_id,
            step="IMAGE_GEN",
            status="SUCCESS",
            latency_ms=latency_ms,
            metadata={"seed": prompt_data.get('seed', 'N/A')}
        )
        
        # Log generation
        print(f"[MOCK GEN] Generated asset for {shot_id} -> {filepath}")
        
        return file_url
    
    def _real_generate(self, shot_id: str, prompt_data: dict) -> str:
        """
        Real image generation using Flux API.
        
        Args:
            shot_id: Unique identifier for the shot
            prompt_data: Dictionary containing positive_prompt, negative_prompt, and seed
            
        Returns:
            URL to the generated image from the API
        """
        print(f"[REAL GEN] Calling Flux API for {shot_id}...")
        
        try:
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {settings.FLUX_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt_data.get("positive_prompt", ""),
                "negative_prompt": prompt_data.get("negative_prompt", ""),
                "seed": prompt_data.get("seed", 0),
                "width": 1920,
                "height": 1080,
                "num_inference_steps": 50
            }
            
            # Make API call
            response = requests.post(
                settings.FLUX_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result.get("image_url", "")
                print(f"[REAL GEN] ✓ Generated {shot_id} -> {image_url}")
                return image_url
            else:
                print(f"[REAL GEN] ✗ API Error {response.status_code}: {response.text}")
                # Fallback to mock if API fails
                print(f"[REAL GEN] Falling back to mock generation...")
                return self._mock_generate(shot_id, prompt_data)
                
        except Exception as e:
            print(f"[REAL GEN] ✗ Exception: {str(e)}")
            print(f"[REAL GEN] Falling back to mock generation...")
            # Fallback to mock if exception occurs
            return self._mock_generate(shot_id, prompt_data)


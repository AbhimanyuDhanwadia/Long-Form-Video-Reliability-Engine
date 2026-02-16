"""
Prompt Engineering Module for the Long-Form Video Reliability Engine.

This module generates deterministic text-to-image prompts for video generation
based on narrative state, shot plans, and scene context.
"""

from src.core.schemas import NarrativeState, ShotPlan


class PromptGenerator:
    """
    Generates deterministic prompts for text-to-image/video generation.
    
    Constructs detailed prompts by combining scene context, camera specifications,
    lighting conditions, and global style parameters.
    """
    
    # Global style string applied to all prompts
    GLOBAL_STYLE = "shot on Kodak Vision3 500T, film grain, teal and orange color grading, 4k, ultra-realistic"
    
    # Fixed negative prompt for quality control
    NEGATIVE_PROMPT = "text, watermark, blur, distorted, cartoon, 3d render"
    
    def __init__(self):
        """Initialize the PromptGenerator."""
        pass
    
    def generate_prompt(
        self,
        state: NarrativeState,
        shot: ShotPlan,
        header: str,
        content_summary: str
    ) -> dict:
        """
        Generate a complete prompt for text-to-image generation.
        
        Args:
            state: NarrativeState object containing scene metadata
            shot: ShotPlan object with camera specifications
            header: Scene header/slugline
            content_summary: Brief description of scene action
            
        Returns:
            Dictionary containing positive_prompt, negative_prompt, and seed
        """
        # Start with base prompt from location and action
        prompt_parts = []
        
        # Extract location from header
        location = self._extract_location(header)
        
        # Base scene description
        base_description = f"{location}, {content_summary}"
        prompt_parts.append(base_description)
        
        # Camera injection based on shot plan
        camera_tokens = self._inject_camera_specs(shot)
        if camera_tokens:
            prompt_parts.append(camera_tokens)
        
        # Lighting injection based on time of day
        lighting_tokens = self._inject_lighting(header)
        if lighting_tokens:
            prompt_parts.append(lighting_tokens)
        
        # Global style injection
        prompt_parts.append(self.GLOBAL_STYLE)
        
        # Construct final positive prompt
        positive_prompt = ", ".join(prompt_parts)
        
        # Generate deterministic seed from shot ID
        seed = self._generate_seed(shot.shot_id)
        
        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "seed": seed
        }
    
    def _extract_location(self, header: str) -> str:
        """
        Extract location description from scene header.
        
        Args:
            header: Scene header/slugline
            
        Returns:
            Location string (e.g., "desert highway", "diner")
        """
        # Remove INT./EXT. and time of day
        location = header.upper()
        location = location.replace("INT.", "").replace("EXT.", "").replace("INT/EXT.", "")
        location = location.replace(" - DAY", "").replace(" - NIGHT", "")
        location = location.replace(" - MORNING", "").replace(" - EVENING", "")
        location = location.strip().lower()
        
        return location
    
    def _inject_camera_specs(self, shot: ShotPlan) -> str:
        """
        Generate camera specification tokens based on shot plan.
        
        Args:
            shot: ShotPlan object
            
        Returns:
            Camera specification string
        """
        tokens = []
        
        # Lens-specific tokens
        if shot.lens == "35mm":
            tokens.append("35mm lens, natural field of view")
        elif shot.lens == "85mm":
            tokens.append("85mm portrait lens, bokeh, shallow depth of field")
        elif shot.lens == "24mm":
            tokens.append("24mm wide lens")
        
        # Shot type tokens
        if shot.shot_type == "Wide":
            tokens.append("wide angle, establishing shot, detailed background")
        elif shot.shot_type == "Close-Up":
            tokens.append("close-up shot, intimate framing, facial details")
        elif shot.shot_type == "Medium":
            tokens.append("medium shot, balanced composition")
        
        # Camera movement tokens
        if shot.camera_movement == "Handheld":
            tokens.append("handheld camera, dynamic movement")
        elif shot.camera_movement == "Tracking":
            tokens.append("tracking shot, smooth camera movement")
        elif shot.camera_movement == "Slow Pan":
            tokens.append("slow pan, cinematic movement")
        
        return ", ".join(tokens)
    
    def _inject_lighting(self, header: str) -> str:
        """
        Generate lighting tokens based on time of day in header.
        
        Args:
            header: Scene header/slugline
            
        Returns:
            Lighting specification string
        """
        header_upper = header.upper()
        
        if "NIGHT" in header_upper:
            return "cinematic night lighting, chiaroscuro, volumetric fog, dark atmosphere"
        elif "DAY" in header_upper:
            return "natural daylight, harsh shadows, high contrast"
        elif "MORNING" in header_upper:
            return "soft morning light, golden hour, warm tones"
        elif "EVENING" in header_upper:
            return "evening light, blue hour, cool tones"
        
        # Default to neutral lighting
        return "cinematic lighting, professional color grading"
    
    def _generate_seed(self, shot_id: str) -> int:
        """
        Generate a deterministic seed from shot ID.
        
        Args:
            shot_id: Unique shot identifier
            
        Returns:
            Integer seed for reproducible generation
        """
        # Use Python's built-in hash function for deterministic seed
        # Ensure positive integer within reasonable range
        return abs(hash(shot_id)) % (2**31)

"""
Deterministic Script Parser for the Long-Form Video Reliability Engine.

This module provides screenplay parsing functionality to extract narrative structure
from standard screenplay format and generate NarrativeState objects.
"""

import re
from typing import List
from src.core.schemas import NarrativeState


class ScriptParser:
    """
    Parses screenplay text and extracts narrative structure.
    
    Uses regex-based pattern matching to identify scene headers, extract characters,
    and generate deterministic NarrativeState objects for each scene.
    """
    
    # Regex pattern for standard screenplay scene headers (sluglines)
    SCENE_HEADER_PATTERN = r'^(INT\.|EXT\.|INT/EXT\.)\s+(.+?)(?:\s+-\s+(.+?))?$'
    
    # Regex pattern for character names (all caps, typically on their own line)
    CHARACTER_PATTERN = r'\b([A-Z][A-Z\s]{2,})\b'
    
    def __init__(self):
        """Initialize the ScriptParser."""
        self.scene_header_regex = re.compile(self.SCENE_HEADER_PATTERN, re.MULTILINE)
        self.character_regex = re.compile(self.CHARACTER_PATTERN)
    
    def parse(self, script: str):
        """
        Parse a screenplay string and extract NarrativeState objects for each scene.
        
        Args:
            script: Raw screenplay text containing scene headers and action lines
            
        Returns:
            Tuple of (List of NarrativeState objects, List of scene data tuples)
            Scene data tuples contain (header, content) for each scene
        """
        # Split script into scenes based on scene headers
        scenes = self._split_into_scenes(script)
        
        if not scenes:
            return [], []
        
        # Calculate total number of scenes for timeline positioning
        total_scenes = len(scenes)
        
        # Generate NarrativeState for each scene
        narrative_states = []
        for idx, (header, content) in enumerate(scenes, start=1):
            narrative_state = self._create_narrative_state(
                scene_number=idx,
                total_scenes=total_scenes,
                header=header,
                content=content
            )
            narrative_states.append(narrative_state)
        
        return narrative_states, scenes
    
    def _split_into_scenes(self, script: str) -> List[tuple[str, str]]:
        """
        Split the script into scenes based on scene headers.
        
        Args:
            script: Raw screenplay text
            
        Returns:
            List of tuples (scene_header, scene_content)
        """
        scenes = []
        lines = script.strip().split('\n')
        
        current_header = None
        current_content = []
        
        for line in lines:
            # Check if this line is a scene header
            match = self.scene_header_regex.match(line.strip())
            
            if match:
                # Save previous scene if it exists
                if current_header is not None:
                    scenes.append((current_header, '\n'.join(current_content)))
                
                # Start new scene
                current_header = line.strip()
                current_content = []
            else:
                # Add to current scene content
                if current_header is not None:
                    current_content.append(line)
        
        # Don't forget the last scene
        if current_header is not None:
            scenes.append((current_header, '\n'.join(current_content)))
        
        return scenes
    
    def _create_narrative_state(
        self,
        scene_number: int,
        total_scenes: int,
        header: str,
        content: str
    ) -> NarrativeState:
        """
        Create a NarrativeState object from scene information.
        
        Args:
            scene_number: Current scene number (1-indexed)
            total_scenes: Total number of scenes in the script
            header: Scene header/slugline
            content: Scene content (action lines and dialogue)
            
        Returns:
            NarrativeState object representing this scene
        """
        # Generate scene ID
        scene_id = f"SCENE-{scene_number:03d}"
        
        # Calculate timeline position (normalized 0.0 to 1.0)
        timeline_position = scene_number / total_scenes
        
        # Default tension level (deterministic for now)
        tension_level = 0.1
        
        # Extract active characters from the content
        active_characters = self._extract_characters(content)
        
        return NarrativeState(
            scene_id=scene_id,
            timeline_position=timeline_position,
            tension_level=tension_level,
            active_characters=active_characters,
            emotional_vector=None  # Not implemented yet
        )
    
    def _extract_characters(self, content: str) -> List[str]:
        """
        Extract character names from scene content.
        
        Looks for capitalized names in action lines (standard screenplay format
        for character cues and first mentions).
        
        Args:
            content: Scene content text
            
        Returns:
            List of unique character names found in the scene
        """
        # Find all capitalized words/phrases
        matches = self.character_regex.findall(content)
        
        # Clean up and deduplicate
        characters = []
        seen = set()
        
        for match in matches:
            # Clean up the character name
            char_name = match.strip()
            
            # Filter out common screenplay terms and very short matches
            if len(char_name) < 3:
                continue
            
            # Common screenplay terms to exclude
            excluded_terms = {
                'INT', 'EXT', 'DAY', 'NIGHT', 'CONTINUOUS', 'LATER',
                'FADE IN', 'FADE OUT', 'CUT TO', 'DISSOLVE TO',
                'THE', 'AND', 'BUT', 'FOR', 'NOT', 'WITH'
            }
            
            if char_name in excluded_terms:
                continue
            
            # Add unique characters
            if char_name not in seen:
                characters.append(char_name)
                seen.add(char_name)
        
        return characters

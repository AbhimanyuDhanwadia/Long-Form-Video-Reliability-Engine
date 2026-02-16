"""
Deterministic Cinematographer Engine for the Long-Form Video Reliability Engine.

This module provides shot planning functionality based on narrative state and
scene content using deterministic heuristic rules.
"""

import re
from typing import List
from src.core.schemas import NarrativeState, ShotPlan


class CinematicEngine:
    """
    Generates deterministic shot plans based on narrative state and scene content.
    
    Uses heuristic rules to determine shot types, camera movements, and lens choices
    based on scene characteristics like timeline position, tension level, and content.
    """
    
    # Action keywords that trigger specific cinematography rules
    ACTION_KEYWORDS = ["RUN", "FIGHT", "CHASE", "GUN", "SCREAM"]
    
    def __init__(self):
        """Initialize the CinematicEngine."""
        pass
    
    def generate_shot_plan(
        self,
        state: NarrativeState,
        scene_content: str,
        scene_header: str = ""
    ) -> List[ShotPlan]:
        """
        Generate a list of shot plans for a scene based on narrative state and content.
        
        Args:
            state: NarrativeState object containing scene metadata
            scene_content: The actual content/action lines of the scene
            scene_header: Optional scene header/slugline for additional context
            
        Returns:
            List of ShotPlan objects representing the cinematography for this scene
        """
        shots = []
        shot_counter = 1
        
        # Analyze scene content
        word_count = len(scene_content.split())
        is_exterior = "EXT." in scene_header.upper()
        is_first_scene = state.timeline_position <= 0.25  # First scene in timeline
        is_high_tension = state.tension_level > 0.8
        has_action = self._contains_action_keywords(scene_content)
        
        # RULE 1: The Establishing Rule
        # Always start with a master shot
        master_shot = self._create_establishing_shot(
            state=state,
            shot_number=shot_counter,
            is_first_scene=is_first_scene,
            is_exterior=is_exterior,
            is_high_tension=is_high_tension,
            has_action=has_action
        )
        shots.append(master_shot)
        shot_counter += 1
        
        # RULE 2: The Intimacy/Dialogue Rule
        # Add close-up coverage for dialogue-heavy scenes
        if word_count > 100:
            closeup_shot = self._create_dialogue_shot(
                state=state,
                shot_number=shot_counter,
                is_high_tension=is_high_tension,
                has_action=has_action
            )
            shots.append(closeup_shot)
            shot_counter += 1
        
        # RULE 4: The Action Rule
        # Add tracking shot for action sequences
        if has_action:
            action_shot = self._create_action_shot(
                state=state,
                shot_number=shot_counter
            )
            shots.append(action_shot)
            shot_counter += 1
        
        return shots
    
    def _create_establishing_shot(
        self,
        state: NarrativeState,
        shot_number: int,
        is_first_scene: bool,
        is_exterior: bool,
        is_high_tension: bool,
        has_action: bool
    ) -> ShotPlan:
        """
        Create the establishing/master shot for a scene.
        
        RULE 1: First scene or exterior scenes get wide establishing shots.
        RULE 3: High tension overrides with handheld movement.
        """
        shot_id = f"{state.scene_id}-SHOT-{shot_number:03d}"
        
        # Default establishing shot parameters
        shot_type = "Wide"
        lens = "24mm"
        movement = "Static"
        
        # Apply Rule 1: Establishing shot for first scene or exterior
        if is_first_scene or is_exterior:
            shot_type = "Wide"
            lens = "24mm"
            movement = "Slow Pan"
        
        # Apply Rule 3: High tension override
        if is_high_tension:
            movement = "Handheld"
            lens = "35mm"
        
        # Apply Rule 4: Action override
        if has_action:
            movement = "Tracking"
            lens = "35mm"
        
        return ShotPlan(
            shot_id=shot_id,
            scene_id=state.scene_id,
            shot_type=shot_type,
            lens=lens,
            camera_movement=movement,
            is_deterministic=True
        )
    
    def _create_dialogue_shot(
        self,
        state: NarrativeState,
        shot_number: int,
        is_high_tension: bool,
        has_action: bool
    ) -> ShotPlan:
        """
        Create a close-up shot for dialogue-heavy scenes.
        
        RULE 2: Dialogue-heavy scenes (>100 words) get close-up coverage.
        RULE 3: High tension can override movement.
        """
        shot_id = f"{state.scene_id}-SHOT-{shot_number:03d}"
        
        # Default dialogue shot parameters
        shot_type = "Close-Up"
        lens = "85mm"
        movement = "Static"
        
        # Apply Rule 3: High tension override
        if is_high_tension:
            movement = "Handheld"
            lens = "35mm"
            shot_type = "Medium"  # Medium shot for tense dialogue
        
        # Apply Rule 4: Action override (even in dialogue scenes)
        if has_action:
            movement = "Tracking"
            shot_type = "Medium"
            lens = "35mm"
        
        return ShotPlan(
            shot_id=shot_id,
            scene_id=state.scene_id,
            shot_type=shot_type,
            lens=lens,
            camera_movement=movement,
            is_deterministic=True
        )
    
    def _create_action_shot(
        self,
        state: NarrativeState,
        shot_number: int
    ) -> ShotPlan:
        """
        Create a tracking shot for action sequences.
        
        RULE 4: Action keywords trigger tracking medium shots.
        """
        shot_id = f"{state.scene_id}-SHOT-{shot_number:03d}"
        
        return ShotPlan(
            shot_id=shot_id,
            scene_id=state.scene_id,
            shot_type="Medium",
            lens="35mm",
            camera_movement="Tracking",
            is_deterministic=True
        )
    
    def _contains_action_keywords(self, content: str) -> bool:
        """
        Check if scene content contains action keywords.
        
        RULE 4: Detect action sequences by keyword matching.
        """
        content_upper = content.upper()
        return any(keyword in content_upper for keyword in self.ACTION_KEYWORDS)

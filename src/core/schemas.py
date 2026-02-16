"""
Core Pydantic schemas for the Long-Form Video Reliability Engine (LFV-RE).

This module defines the fundamental data structures for narrative state tracking,
style consistency, and shot planning in long-form video generation.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class NarrativeState(BaseModel):
    """
    Represents the narrative state at a specific point in the video timeline.
    
    Tracks scene progression, dramatic tension, active characters, and emotional context
    to ensure narrative coherence across long-form video generation.
    """
    scene_id: str = Field(..., description="Unique identifier for the current scene")
    timeline_position: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Normalized position in the overall timeline (0.0 = start, 1.0 = end)"
    )
    tension_level: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Current dramatic tension level (0.0 = calm, 1.0 = peak tension)"
    )
    active_characters: List[str] = Field(
        default_factory=list,
        description="List of character identifiers currently present in the scene"
    )
    emotional_vector: Optional[List[float]] = Field(
        default=None,
        description="Multi-dimensional emotional state representation (optional for now)"
    )


class StyleVector(BaseModel):
    """
    Defines the visual style parameters for consistent cinematography.
    
    Ensures visual coherence across shots by maintaining consistent lighting,
    film grain, and color palette characteristics.
    """
    lighting_bias: float = Field(
        ..., 
        ge=-1.0, 
        le=1.0, 
        description="Lighting tendency (-1.0 = dark/moody, 0.0 = neutral, 1.0 = bright/airy)"
    )
    film_grain: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Amount of film grain texture (0.0 = none, 1.0 = maximum)"
    )
    color_palette: List[float] = Field(
        ...,
        description="Color palette representation as a list of normalized values"
    )


class ShotPlan(BaseModel):
    """
    Defines a single shot within a scene, including camera and technical parameters.
    
    Specifies all necessary information for shot execution, including framing,
    lens choice, camera movement, and determinism flags for reproducibility.
    """
    shot_id: str = Field(..., description="Unique identifier for this shot")
    scene_id: str = Field(..., description="Parent scene identifier")
    shot_type: Literal["Wide", "Medium", "Close-Up"] = Field(
        ...,
        description="Shot framing type"
    )
    lens: str = Field(..., description="Lens specification (e.g., '35mm', '85mm')")
    camera_movement: str = Field(
        ...,
        description="Camera movement description (e.g., 'static', 'dolly-in', 'pan-left')"
    )
    is_deterministic: bool = Field(
        default=True,
        description="Whether this shot should be generated deterministically for reproducibility"
    )

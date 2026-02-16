"""
Unit tests for the Long-Form Video Reliability Engine.

Tests cover:
1. Determinism of the Cinematic Engine
2. Logic of the Semantic Critic
3. Schema Validation of Shot Plans
"""

import pytest
from src.core.schemas import NarrativeState, ShotPlan
from src.core.cinematographer import CinematicEngine
from src.services.critic import SemanticCritic


def test_shot_plan_determinism():
    """
    Test 1: Determinism.
    
    Ensure that calling the CinematicEngine twice with the same 
    NarrativeState produces identical ShotPlan lists.
    """
    engine = CinematicEngine()
    
    state = NarrativeState(
        scene_id="SCENE-001",
        timeline_position=0.5,
        tension_level=0.8,
        active_characters=["HERO", "VILLAIN"]
    )
    
    # Run planning twice
    scene_content = "HERO runs down the hallway. VILLAIN shoots a GUN."
    plan_1 = engine.generate_shot_plan(state, scene_content)
    plan_2 = engine.generate_shot_plan(state, scene_content)
    
    # Assert expected outputs
    assert len(plan_1) > 0, "Shot plan should not be empty"
    assert len(plan_1) == len(plan_2), "Plans should have same number of shots"
    
    # Check strict equality of all fields
    for shot_1, shot_2 in zip(plan_1, plan_2):
        assert shot_1.shot_type == shot_2.shot_type
        assert shot_1.lens == shot_2.lens
        assert shot_1.camera_movement == shot_2.camera_movement
        assert shot_1.is_deterministic == shot_2.is_deterministic
        
    print("\n[TEST] ✓ Cinematic Engine is Deterministic")


def test_semantic_critic_alignment():
    """
    Test 2: Semantic Logic.
    
    Ensure SemanticCritic correctly identifies semantic alignment.
    """
    critic = SemanticCritic()
    
    text_a = "A cat on a mat"
    text_b = "A cat on a mat"  # Exact match
    text_c = "The economy is failing"  # Complete mismatch
    
    # Test Similarity
    score_match = critic.evaluate_shot(text_a, text_b)
    assert score_match > 0.9, f"Expected high similarity (>0.9), got {score_match}"
    
    # Test Drift
    score_drift = critic.evaluate_shot(text_a, text_c)
    assert score_drift < 0.3, f"Expected low similarity (<0.3), got {score_drift}"
    
    print(f"\n[TEST] ✓ Semantic Critic Logic Verified (Match: {score_match:.2f}, Drift: {score_drift:.2f})")


def test_parser_integrity():
    """
    Test 3: Parser Integrity.
    
    Pass a small 2-scene script to ScriptParser.
    Assert that output contains exactly 2 NarrativeState objects.
    """
    from src.core.parser import ScriptParser
    
    script = """
    EXT. SCENE ONE - DAY
    Character A walks.
    
    INT. SCENE TWO - NIGHT
    Character B talks.
    """
    
    parser = ScriptParser()
    narrative_states, scenes = parser.parse(script)
    
    assert len(narrative_states) == 2, f"Expected 2 narrative states, got {len(narrative_states)}"
    assert len(scenes) == 2, f"Expected 2 scenes, got {len(scenes)}"
    
    # Check assertions on the SCENE TUPLES, not NarrativeState
    assert scenes[0][0].strip() == "EXT. SCENE ONE - DAY"
    assert scenes[1][0].strip() == "INT. SCENE TWO - NIGHT"
    
    print(f"\n[TEST] ✓ Parser Integrity Verified ({len(narrative_states)} scenes parsed)")


def test_schema_validation():
    """
    Test 3: Schema Validation.
    
    Ensure raw dictionary correctly parses into Pydantic ShotPlan.
    """
    raw_data = {
        "scene_id": "SCENE-001",
        "shot_id": "TEST-001",
        "shot_type": "Close-Up",
        "lens": "85mm",
        "camera_movement": "Static",
        "is_deterministic": True
    }
    
    # Parse into Pydantic model
    shot = ShotPlan(**raw_data)
    
    # Validate fields
    assert shot.scene_id == "SCENE-001"
    assert shot.shot_id == "TEST-001"
    assert shot.shot_type == "Close-Up"
    assert shot.lens == "85mm"
    assert shot.is_deterministic is True
    
    print("\n[TEST] ✓ Schema Validation Passed")

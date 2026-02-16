"""
Long-Form Video Reliability Engine (LFV-RE) - LangGraph Workflow

This script executes the complete deterministic pipeline using a stateful
LangGraph workflow:
1. Script parsing
2. Shot planning
3. Prompt generation
4. Asset production (images + videos)
"""

import json
from src.core.graph import build_workflow


# Sample screenplay for testing the workflow
SAMPLE_SCRIPT = """
EXT. DESERT HIGHWAY - DAY

A lonely wind blows across the asphalt.

INT. DINER - NIGHT

JOHN sits across from SARAH. The tension is palpable.

JOHN
You took the money, didn't you?

SARAH
I had no choice. They were going to kill him. You don't understand 
what it's like to have a gun to your head. I ran. I ran as fast as 
I could but they were everywhere.

EXT. ALLEYWAY - NIGHT

John pulls a GUN. He CHASEs the shadow down the wet pavement. 
A SCREAM echoes.
"""


def main():
    """Execute the LangGraph workflow."""
    print("=" * 70)
    print("LONG-FORM VIDEO RELIABILITY ENGINE - LANGGRAPH WORKFLOW")
    print("=" * 70)
    
    # Build the workflow
    print("\n[INIT] Building LangGraph workflow...")
    app = build_workflow()
    print("[INIT] ✓ Workflow compiled")
    
    # Initialize state
    initial_state = {
        "script": SAMPLE_SCRIPT,
        "narrative_states": [],
        "scenes": [],
        "shot_plans": [],
        "prompts": {},
        "assets": {},
        "logs": [],
        "retry_count": 0,
        "rejected_shots": []
    }
    
    # Execute the workflow
    print("\n[EXEC] Running workflow...\n")
    final_state = app.invoke(initial_state)
    
    # Print logs
    print("\n" + "=" * 70)
    print("WORKFLOW LOGS")
    print("=" * 70)
    for log in final_state["logs"]:
        print(log)
    
    # Build final output structure
    print("\n" + "=" * 70)
    print("FINAL PIPELINE OUTPUT")
    print("=" * 70)
    
    results = []
    for ns, (header, content) in zip(final_state["narrative_states"], final_state["scenes"]):
        # Get shots for this scene
        scene_shots = [sp for sp in final_state["shot_plans"] if sp.shot_id.startswith(ns.scene_id)]
        
        shot_results = []
        for shot in scene_shots:
            shot_result = {
                "shot_id": shot.shot_id,
                "shot_type": shot.shot_type,
                "lens": shot.lens,
                "camera_movement": shot.camera_movement,
                "is_deterministic": shot.is_deterministic,
                "prompt": final_state["prompts"][shot.shot_id],
                "assets": final_state["assets"][shot.shot_id]
            }
            shot_results.append(shot_result)
        
        scene_result = {
            "scene_id": ns.scene_id,
            "header": header,
            "timeline_position": ns.timeline_position,
            "tension_level": ns.tension_level,
            "active_characters": ns.active_characters,
            "word_count": len(content.split()),
            "shot_plans": shot_results
        }
        results.append(scene_result)
    
    print(json.dumps(results, indent=2))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_shots = len(final_state["shot_plans"])
    print(f"Total Scenes: {len(final_state['narrative_states'])}")
    print(f"Total Shots: {total_shots}")
    print(f"Total Images Generated: {total_shots}")
    print(f"Total Videos Generated: {total_shots}")
    print("\nShot Breakdown:")
    for scene in results:
        print(f"  {scene['scene_id']}: {len(scene['shot_plans'])} shot(s)")
    
    print("\n" + "=" * 70)
    print("WORKFLOW STATUS: COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

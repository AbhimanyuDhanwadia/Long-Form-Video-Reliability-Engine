"""
LangGraph Workflow for the Long-Form Video Reliability Engine.

This module defines a stateful workflow using LangGraph to orchestrate
the entire pipeline from script parsing to video generation, with
self-healing capabilities.
"""

import os
import json
import random
from typing import TypedDict, List, Dict, Annotated, Literal
from langgraph.graph import StateGraph, END
from src.core.schemas import NarrativeState, ShotPlan
from src.core.parser import ScriptParser
from src.core.cinematographer import CinematicEngine
from src.core.prompt_engineer import PromptGenerator
from src.services.generator import ImageService
from src.services.generator import ImageService
from src.services.video import VideoService
from src.services.critic import SemanticCritic
from src.services.vision import VisionService
from src.core.telemetry import telemetry


class AgentState(TypedDict):
    """
    State definition for the LFV-RE pipeline workflow.
    
    This holds the complete memory of the pipeline as it progresses
    through each stage.
    """
    script: str
    narrative_states: List[NarrativeState]
    scenes: List[tuple]  # List of (header, content) tuples
    shot_plans: List[ShotPlan]
    prompts: Dict[str, dict]  # Keyed by shot_id
    assets: Dict[str, dict]  # Keyed by shot_id, holds image/video URLs
    logs: List[str]
    retry_count: int
    rejected_shots: List[str]  # List of shot_ids that failed QA


# Initialize services (singleton pattern)
parser = ScriptParser()
cinematographer = CinematicEngine()
prompt_generator = PromptGenerator()
image_service = ImageService()  # Uses settings.USE_MOCK_GENERATION
video_service = VideoService()  # Uses settings.USE_MOCK_GENERATION
semantic_critic = SemanticCritic()  # Semantic similarity evaluator
vision_service = VisionService()  # Visual Reality Validator


def save_checkpoint(state: AgentState, step_name: str):
    """
    Save the current state to a JSON checkpoint file.
    
    Args:
        state: Current agent state
        step_name: Name of the checkpoint (e.g., "01_parsed")
    """
    # Create checkpoints directory
    checkpoint_dir = "output/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Prepare state for serialization
    serializable_state = {}
    
    for key, value in state.items():
        if key == "narrative_states" and value:
            # Convert list of NarrativeState Pydantic models
            serializable_state[key] = [ns.model_dump() for ns in value]
        elif key == "shot_plans" and value:
            # Convert list of ShotPlan Pydantic models
            serializable_state[key] = [sp.model_dump() for sp in value]
        else:
            # Keep other values as-is (primitives, dicts, lists)
            serializable_state[key] = value
    
    # Save to file
    filename = f"state_{step_name}.json"
    filepath = os.path.join(checkpoint_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(serializable_state, f, indent=2)
    
    print(f"[PERSISTENCE] Saved checkpoint: {filename}")


def node_parse_script(state: AgentState) -> AgentState:
    """
    Node 1: Parse the screenplay into narrative states.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with narrative_states and scenes populated
    """
    script = state["script"]
    state["logs"].append("[NODE 1] Parsing screenplay...")
    
    # Parse script
    narrative_states, scenes = parser.parse(script)
    
    # Apply manual tension override for ALLEYWAY scene (testing)
    for ns in narrative_states:
        if "ALLEYWAY" in scenes[narrative_states.index(ns)][0].upper():
            state["logs"].append(f"[NODE 1] Applying tension override for {ns.scene_id}")
            ns.tension_level = 0.9
    
    state["narrative_states"] = narrative_states
    state["scenes"] = scenes
    state["logs"].append(f"[NODE 1] ✓ Extracted {len(narrative_states)} scenes")
    
    # Save checkpoint
    save_checkpoint(state, "01_parsed")
    
    return state


def node_plan_shots(state: AgentState) -> AgentState:
    """
    Node 2: Generate shot plans for each scene.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with shot_plans populated
    """
    state["logs"].append("[NODE 2] Generating shot plans...")
    
    narrative_states = state["narrative_states"]
    scenes = state["scenes"]
    all_shot_plans = []
    
    for ns, (header, content) in zip(narrative_states, scenes):
        shot_plans = cinematographer.generate_shot_plan(ns, content, header)
        all_shot_plans.extend(shot_plans)
    
    state["shot_plans"] = all_shot_plans
    state["logs"].append(f"[NODE 2] ✓ Generated {len(all_shot_plans)} shot plans")
    
    # Save checkpoint
    save_checkpoint(state, "02_planned")
    
    return state


def node_generate_prompts(state: AgentState) -> AgentState:
    """
    Node 3: Generate text-to-image prompts for each shot.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with prompts populated
    """
    # Check if this is a retry
    if state["retry_count"] > 0:
        state["logs"].append(f"[NODE 3] Regenerating prompts (Retry {state['retry_count']})...")
        # Only regenerate prompts for rejected shots
        rejected = state["rejected_shots"]
    else:
        state["logs"].append("[NODE 3] Generating prompts...")
        rejected = []
    
    narrative_states = state["narrative_states"]
    scenes = state["scenes"]
    shot_plans = state["shot_plans"]
    prompts = state.get("prompts", {})
    
    shot_idx = 0
    for ns, (header, content) in zip(narrative_states, scenes):
        # Get shots for this scene
        scene_shots = [sp for sp in shot_plans if sp.shot_id.startswith(ns.scene_id)]
        
        # Create content summary
        content_summary = content.strip().replace("\n", " ")[:50]
        
        for shot in scene_shots:
            # Only regenerate if this is first pass or shot was rejected
            if state["retry_count"] == 0 or shot.shot_id in rejected:
                prompt_data = prompt_generator.generate_prompt(
                    state=ns,
                    shot=shot,
                    header=header,
                    content_summary=content_summary
                )
                prompts[shot.shot_id] = prompt_data
                shot_idx += 1
    
    state["prompts"] = prompts
    
    if state["retry_count"] > 0:
        state["logs"].append(f"[NODE 3] ✓ Regenerated {len(rejected)} prompts")
    else:
        state["logs"].append(f"[NODE 3] ✓ Generated {len(prompts)} prompts")
    
    # Save checkpoint (only on first pass, not retries)
    if state["retry_count"] == 0:
        save_checkpoint(state, "03_prompted")
    
    return state


def node_production_factory(state: AgentState) -> AgentState:
    """
    Node 4: Generate images and videos for each shot.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with assets populated
    """
    # Check if this is a retry
    if state["retry_count"] > 0:
        state["logs"].append(f"[NODE 4] Regenerating assets (Retry {state['retry_count']})...")
        rejected = state["rejected_shots"]
    else:
        state["logs"].append("[NODE 4] Production factory - generating assets...")
        rejected = []
    
    shot_plans = state["shot_plans"]
    prompts = state["prompts"]
    assets = state.get("assets", {})
    
    for shot in shot_plans:
        shot_id = shot.shot_id
        
        # Only regenerate if this is first pass or shot was rejected
        if state["retry_count"] == 0 or shot_id in rejected:
            prompt_data = prompts[shot_id]
            
            # Generate image
            image_url = image_service.generate_image(shot_id, prompt_data)
            
            # Generate video
            video_url = video_service.generate_video(shot_id, image_url, shot)
            
            assets[shot_id] = {
                "image_url": image_url,
                "video_url": video_url
            }
    
    state["assets"] = assets
    
    if state["retry_count"] > 0:
        state["logs"].append(f"[NODE 4] ✓ Regenerated {len(rejected)} asset pairs")
    else:
        state["logs"].append(f"[NODE 4] ✓ Generated {len(assets)} image/video pairs")
    
    # Save checkpoint (only on first pass, not retries)
    if state["retry_count"] == 0:
        save_checkpoint(state, "04_produced")
    
    return state


def node_critic(state: AgentState) -> AgentState:
    """
    Node 5: Visual Reality Critic (VLM + Semantic)
    
    Validates visual fidelity by:
    1. Generating a caption for the image using VisionService (VLM).
    2. Comparing the Scene Content vs VLM Caption using SemanticCritic.
    """
    state["logs"].append("[NODE 5] Running visual reality validation...")
    
    rejected_shots = []
    scenes = state["scenes"]
    prompts = state["prompts"]
    assets = state["assets"]
    retry_count = state.get("retry_count", 0)
    
    # Check each generated asset
    for shot_id in assets.keys():
        # Get the scene content for this shot
        scene_id = shot_id.split("-SHOT")[0]
        scene_index = int(scene_id.split("-")[1]) - 1  # SCENE-001 -> index 0
        
        if scene_index < len(scenes):
            _, scene_content = scenes[scene_index]
        else:
            scene_content = ""
        
        # Get the positive prompt (kept for reference, but not used for comparison now)
        prompt_data = prompts.get(shot_id, {})
        positive_prompt = prompt_data.get("positive_prompt", "")
        
        # Get image path
        image_url = assets[shot_id].get("image_url", "")
        # Strip file:// prefix if present for local paths
        image_path = image_url.replace("file://", "") if image_url.startswith("file://") else image_url
        
        # Step 1: VLM Caption Generation
        caption = vision_service.describe_image(image_path, positive_prompt)
        print(f"[CRITIC] VLM Caption for {shot_id}: {caption[:50]}...")
        
        # Step 2: Semantic comparison (Scene Content vs Generated Caption)
        score = semantic_critic.evaluate_shot(scene_content, caption)
        
        # Use configurable threshold from settings
        from src.core.config import settings
        threshold = settings.SIMILARITY_THRESHOLD
        
        if score >= threshold:  # Pass
            print(f"[CRITIC] Shot {shot_id} PASSED - Visually Aligned (Score: {score:.2f})")
            
            # Log telemetry for pass
            telemetry.log_event(
                scene_id=scene_id,
                shot_id=shot_id,
                step="CRITIC_QA",
                status="PASS",
                latency_ms=0,
                metadata={
                    "score": f"{score:.2f}", 
                    "method": "vlm_semantic_match",
                    "retry_count": retry_count,
                    "final_score": f"{score:.2f}"
                }
            )
        else:  # Fail
            print(f"[CRITIC] Shot {shot_id} REJECTED - Visual Hallucination (Score: {score:.2f})")
            rejected_shots.append(shot_id)
            
            # Log telemetry for fail
            telemetry.log_event(
                scene_id=scene_id,
                shot_id=shot_id,
                step="CRITIC_QA",
                status="FAIL",
                latency_ms=0,
                metadata={
                    "score": f"{score:.2f}", 
                    "reason": "visual_hallucination", 
                    "method": "vlm_semantic_match",
                    "retry_count": retry_count,
                    "final_score": f"{score:.2f}"
                }
            )
    
    # Update state with rejected shots
    state["rejected_shots"] = rejected_shots
    
    # Increment retry count if there are rejected shots
    if rejected_shots:
        state["retry_count"] = retry_count + 1
        state["logs"].append(f"[CRITIC] Incrementing retry count to {state['retry_count']}")
        print(f"[CRITIC] ⚠ {len(rejected_shots)} shot(s) failed visual QA")
    else:
        print(f"[CRITIC] ✓ All shots passed visual QA")
    
    return state


def should_continue(state: AgentState) -> Literal["generate_prompts", "end"]:
    """
    Router function to determine if workflow should retry or end.
    
    Args:
        state: Current agent state
        
    Returns:
        "generate_prompts" to retry, "end" to finish
    """
    rejected_shots = state["rejected_shots"]
    retry_count = state.get("retry_count", 0)
    
    # If there are rejected shots and we haven't exceeded max retries
    if rejected_shots and retry_count <= 3:
        state["logs"].append(f"[ROUTER] Looping back to regenerate {len(rejected_shots)} shot(s)...")
        return "generate_prompts"
    elif rejected_shots and retry_count > 3:
        state["logs"].append(f"[ROUTER] Max retries reached. Proceeding with {len(rejected_shots)} imperfect shot(s).")
        return "end"
    else:
        state["logs"].append("[ROUTER] All shots approved. Workflow complete.")
        return "end"


def build_workflow() -> StateGraph:
    """
    Build and compile the LangGraph workflow with self-healing loop.
    
    Returns:
        Compiled StateGraph application
    """
    # Initialize workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_script", node_parse_script)
    workflow.add_node("plan_shots", node_plan_shots)
    workflow.add_node("generate_prompts", node_generate_prompts)
    workflow.add_node("production_factory", node_production_factory)
    workflow.add_node("critic", node_critic)
    
    # Add edges (linear flow with loop)
    workflow.set_entry_point("parse_script")
    workflow.add_edge("parse_script", "plan_shots")
    workflow.add_edge("plan_shots", "generate_prompts")
    workflow.add_edge("generate_prompts", "production_factory")
    workflow.add_edge("production_factory", "critic")
    
    # Add conditional edge for self-healing loop
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "generate_prompts": "generate_prompts",
            "end": END
        }
    )
    
    # Compile
    app = workflow.compile()
    
    return app


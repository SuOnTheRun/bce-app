from typing import List, Literal, Optional
from pydantic import BaseModel, Field

DecisionType = Literal[
    "Habit reinforcement",
    "Habit disruption",
    "Impulse capture",
    "Planned consideration",
    "Risk mitigation",
    "Identity signaling",
    "Loss avoidance",
    "Convenience optimization",
]

PrimaryTension = Literal[
    "Time vs Value",
    "Certainty vs Opportunity",
    "Effort vs Reward",
    "Familiarity vs Novelty",
    "Control vs Convenience",
    "Identity vs Price",
]

DecisionWindow = Literal[
    "In-motion",
    "Pre-planned",
    "At-threshold",
    "Reflective",
    "Socially triggered",
    "Environmentally triggered",
]

class BehavioralTension(BaseModel):
    tradeoff: str = Field(..., description="One sentence describing the primary tradeoff in plain English.")
    why_this_tension_exists: str = Field(..., description="Why this tension is present for this campaign.")
    what_resolves_it: str = Field(..., description="What must be true for the audience to choose action now.")

class MomentOfInstability(BaseModel):
    when: str
    where: str
    why_here_not_elsewhere: str

class Signal(BaseModel):
    signal: str
    classification: Literal["Observed", "Inferred", "Hypothesis"]
    implication: Optional[str] = None

class PlanningImplications(BaseModel):
    what_to_prioritize: str
    what_to_avoid: str
    channel_role_logic: str

class ConfidenceAssessment(BaseModel):
    level: Literal["Low", "Medium", "High"]
    drivers: List[str]
    limitations: List[str]

class RejectedAlternatives(BaseModel):
    # This is the "cut-throat" part: it must say what it rejected and why.
    not_decision_types: List[str] = Field(default_factory=list, description="Decision types considered but rejected.")
    why_not_decision_types: str = Field(..., description="Why those decision types are not dominant here.")
    not_tensions: List[str] = Field(default_factory=list, description="Tensions considered but rejected.")
    why_not_tensions: str = Field(..., description="Why those tensions are not primary here.")
    not_windows: List[str] = Field(default_factory=list, description="Decision windows considered but rejected.")
    why_not_windows: str = Field(..., description="Why those windows are not dominant here.")

class DecisionMap(BaseModel):
    # Core
    decision_being_influenced: str = Field(..., description="The user decision we are trying to change, in plain English.")
    human_context: str = Field(..., description="Compressed context in 2–3 sentences. No fluff.")
    emotional_state: str = Field(..., description="Dominant emotional state driving the choice (e.g., anxious, pragmatic, status-seeking).")
    cognitive_load: str = Field(..., description="Low/Medium/High with a short reason.")

    # Forcing discriminators
    decision_type: DecisionType
    primary_tension: PrimaryTension
    decision_window: DecisionWindow

    # Now build the rest around them
    behavioral_tension: BehavioralTension
    moment_of_instability: MomentOfInstability
    observable_signals: List[Signal] = Field(default_factory=list)
    strategic_levers: List[str] = Field(default_factory=list)

    planning_implications: PlanningImplications
    confidence_assessment: ConfidenceAssessment

    # Explicit rejections so outputs don't collapse into the same story
    rejected_alternatives: RejectedAlternatives

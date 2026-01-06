from pydantic import BaseModel, Field
from typing import List, Literal

SignalClassification = Literal["Observed", "Inferred", "Hypothesis"]
DecisionScope = Literal["pre-trip", "in-moment", "post-experience", "ongoing"]
ConfidenceLevel = Literal["High", "Medium", "Low"]

class HumanContext(BaseModel):
    situation: str
    cognitive_load: str
    emotional_state: str

class BehavioralTension(BaseModel):
    tradeoff: str = Field(description='Must be in form "X vs Y".')
    why_this_tension_exists: str

class MomentOfInstability(BaseModel):
    when: str
    where: str
    why_here_not_elsewhere: str

class ObservableSignal(BaseModel):
    signal: str
    classification: SignalClassification
    input_dependency: str

class PlanningImplications(BaseModel):
    what_to_prioritize: str
    what_to_avoid: str
    channel_role_logic: str

class ConfidenceAssessment(BaseModel):
    level: ConfidenceLevel
    drivers: List[str]
    limitations: List[str]

class DecisionMap(BaseModel):
    decision_being_influenced: str
    decision_scope: DecisionScope
    human_context: HumanContext
    behavioral_tension: BehavioralTension
    moment_of_instability: MomentOfInstability
    observable_signals: List[ObservableSignal]
    strategic_levers: List[str]
    planning_implications: PlanningImplications
    confidence_assessment: ConfidenceAssessment

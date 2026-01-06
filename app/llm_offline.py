import json
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

OFFLINE_DECISION_MAP = {
  "decision_being_influenced": "Whether to make a spontaneous store visit during routine travel in the promo window.",
  "decision_scope": "in-moment",
  "human_context": {
    "situation": "People moving through transit-adjacent retail corridors with limited time and competing errands.",
    "cognitive_load": "Medium—attention is fragmented and decisions are made fast.",
    "emotional_state": "Pragmatic value-seeking; low patience for friction."
  },
  "behavioral_tension": {
    "tradeoff": "Save time vs Get value now",
    "why_this_tension_exists": "The promo creates perceived gain, but the store visit adds uncertainty, detour cost, and time risk."
  },
  "moment_of_instability": {
    "when": "Weekday evenings + weekend mid-day peaks during the promo window",
    "where": "Within 3–8 minutes of route adjacency (subway exits, commuter corridors, pedestrian choke points)",
    "why_here_not_elsewhere": "The decision becomes viable only when the detour cost collapses and the offer feels immediate."
  },
  "observable_signals": [
    {
      "signal": "Repeat presence near retail corridors during peak windows",
      "classification": "Observed",
      "input_dependency": "Audience_Logic + POI_Context"
    },
    {
      "signal": "Higher visit propensity when messaging is time-bound and simple",
      "classification": "Inferred",
      "input_dependency": "Creative_Notes"
    },
    {
      "signal": "Uplift is likely strongest at locations with commute adjacency and clear storefront visibility",
      "classification": "Hypothesis",
      "input_dependency": "POI_Context + Notes"
    }
  ],
  "strategic_levers": [
    "Collapse detour cost: prioritise route-adjacent inventory and commuter choke points.",
    "Use a justification device: time-bound value framing + 'quick win' language.",
    "Pair DOOH (environmental validation) with Display (follow-through + reinforcement)."
  ],
  "planning_implications": {
    "what_to_prioritize": "Route adjacency, dayparting, and creative that signals 'fast, easy, limited-time value'.",
    "what_to_avoid": "Broad geo without journey context; generic brand-led copy without a reason-to-go-now.",
    "channel_role_logic": "DOOH does in-the-world permission + salience; Display catches the second look and drives completion."
  },
  "confidence_assessment": {
    "level": "Medium",
    "drivers": [
      "Objective–measurement alignment (footfall)",
      "POI and movement context specified",
      "Promo window supports urgency framing"
    ],
    "limitations": [
      "No numeric uplift provided",
      "No control design details",
      "Limited creative detail"
    ]
  }
}

def generate_structured_offline(*, response_model: Type[T]) -> T:
    return response_model.model_validate(OFFLINE_DECISION_MAP)

def generate_text_offline(*, decision_map_json: str) -> str:
    dm = json.loads(decision_map_json)
    conf = dm.get("confidence_assessment", {}).get("level", "Medium")

    return f"""Executive Decision Headline
A store visit is most influenceable when the retail location collapses into a commuter’s route AND the offer provides a credible “go-now” justification.

Human Context
- Situation: {dm["human_context"]["situation"]}
- Cognitive load: {dm["human_context"]["cognitive_load"]}
- Emotional state: {dm["human_context"]["emotional_state"]}

Core Behavioral Tension
- {dm["behavioral_tension"]["tradeoff"]}
- Why: {dm["behavioral_tension"]["why_this_tension_exists"]}

Moment of Instability
- When: {dm["moment_of_instability"]["when"]}
- Where: {dm["moment_of_instability"]["where"]}
- Why here: {dm["moment_of_instability"]["why_here_not_elsewhere"]}

Observable Signals
- (Observed) {dm["observable_signals"][0]["signal"]}
- (Inferred) {dm["observable_signals"][1]["signal"]}
- (Hypothesis) {dm["observable_signals"][2]["signal"]}

Planning Implications
Prioritise inventory that sits on-route (transit exits, choke points, last-mile corridors). Daypart the message to commute + weekend peaks. Keep creative brutally simple: time-bound value + “quick visit” cues. Use DOOH as environmental validation; use Display for follow-through once attention returns to mobile.

Confidence
{conf}
"""

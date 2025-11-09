# AI-Assisted Ranking System Specification

**Feature Name:** AI-Assisted Ranking System
**Version:** 1.0
**Date:** 2025-11-08
**Status:** Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Goals & Requirements](#goals--requirements)
3. [User Workflow](#user-workflow)
4. [UI Design Specification](#ui-design-specification)
5. [Data Models](#data-models)
6. [API Specification](#api-specification)
7. [Backend Implementation](#backend-implementation)
8. [Frontend Implementation](#frontend-implementation)
9. [Algorithms](#algorithms)
10. [Implementation Plan](#implementation-plan)

---

## Overview

### Purpose

Enable users to find the optimal LLM configuration for each prompt by combining AI-powered evaluation with human judgment. The system automatically evaluates all configuration results, then allows humans to review and adjust rankings through an intuitive drag-and-drop interface that emphasizes side-by-side comparison of full results.

### Key Principles

1. **AI evaluates first** - Automated baseline ranking with detailed scoring
2. **Results are primary** - Full response text front and center for easy comparison
3. **Human has final say** - Intuitive drag-to-reorder interface
4. **Track everything** - Both AI and human rankings preserved
5. **Clear recommendations** - Weighted algorithm determines best config

### Priority Weights

- **Quality:** 60% (highest priority)
- **Speed:** 30% (second priority)
- **Cost:** 10% (lowest priority)

---

## Goals & Requirements

### Functional Requirements

**FR-1: AI Batch Evaluation**
- System can evaluate all configurations for a prompt using a review prompt template
- Evaluations include structured criteria scores and overall ranking
- Support multiple evaluator models (GPT-4, Claude, etc.)

**FR-2: Review Prompt Templates**
- Users can create/edit/manage review prompt templates
- Templates use variable substitution: `{original_prompt}`, `{config_name}`, `{result}`
- Templates define evaluation criteria

**FR-3: Human Ranking Interface**
- Display all results side-by-side in horizontal carousel
- Full response text visible in each card (primary content)
- Drag-and-drop to reorder from best to worst
- Start with AI's ranking as default order

**FR-4: Dual Ranking System**
- Store both AI rankings and human rankings separately
- Calculate agreement metrics between AI and human
- Track changes humans made from AI baseline

**FR-5: Recommendation Engine**
- Calculate weighted score: quality (60%) + speed (30%) + cost (10%)
- Determine best configuration with confidence level
- Show clear reasoning for recommendation

**FR-6: Consensus Ranking**
- When multiple humans rank the same prompt, calculate consensus
- Use Borda count or similar algorithm
- Compare consensus with AI ranking

### Non-Functional Requirements

**NFR-1: Performance**
- AI batch evaluation completes within 5 minutes for 10 configs
- UI drag operations feel smooth (60fps)
- Results load in under 2 seconds

**NFR-2: Usability**
- First-time users can complete ranking without tutorial
- Mobile-friendly drag interaction
- Keyboard accessible

**NFR-3: Reliability**
- Handle AI evaluation failures gracefully
- Preserve rankings if page refreshes
- Retry failed API calls

---

## User Workflow

### Happy Path

```
1. User runs experiments for a prompt with multiple configs
   ↓
2. User clicks "Compare & Rank" for the prompt
   ↓
3. System checks: Has AI evaluation been run?
   - If NO: Prompt user to run AI evaluation first
   - If YES: Proceed to comparison view
   ↓
4. AI Evaluation (if needed)
   - User selects review prompt template
   - User selects evaluator model (GPT-4, Claude, etc.)
   - System evaluates all configs in batch
   - Progress indicator shows status
   ↓
5. Comparison View Loads
   - Results displayed in horizontal carousel
   - Ordered by AI ranking (best → worst)
   - Full response text visible in each card
   ↓
6. User Reviews Results
   - Reads responses side-by-side
   - Checks AI scores and reasoning
   - Drags cards to adjust ranking
   ↓
7. User Saves Ranking
   - System calculates agreement with AI
   - Shows what changed
   - Stores human ranking
   ↓
8. Recommendation Generated
   - System combines quality, speed, cost
   - Shows best config with confidence
   - Displays reasoning
```

### Alternative Paths

**Path A: Re-run AI Evaluation**
- User disagrees with AI evaluation
- Clicks "Re-evaluate with Different Template"
- Selects new review prompt
- System re-evaluates, user can compare old vs new

**Path B: Skip Human Ranking**
- User trusts AI evaluation
- Clicks "Accept AI Ranking"
- System records as human confirmation of AI order

**Path C: Multiple Evaluators**
- Different team members rank independently
- System calculates consensus
- Shows agreement/disagreement metrics

---

## UI Design Specification

### Compare Page Layout

**Route:** `/compare/:promptName`

```
┌────────────────────────────────────────────────────────────────────┐
│  ← Back to Experiments          Compare: re-organize-idea-puzzle   │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ ✅ AI Evaluation Complete                                  │   │
│  │ Model: GPT-4 Turbo | Review: "Code Quality Reviewer"      │   │
│  │ [View AI Reasoning] [Re-evaluate]                          │   │
│  └────────────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  💡 Drag cards left/right to rank • Best (left) → Worst (right)   │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ 🥇 RANK #1   │  │ 🥈 RANK #2   │  │ 🥉 RANK #3   │           │
│  │ AI Score 9.2 │  │ AI Score 8.8 │  │ AI Score 7.5 │           │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤           │
│  │              │  │              │  │              │           │
│  │ gpt5-        │  │ gpt5-        │  │ gpt5-        │           │
│  │ standard     │  │ detailed     │  │ minimal      │           │
│  │              │  │              │  │              │           │
│  │ **Response** │  │ **Response** │  │ **Response** │           │
│  │              │  │              │  │              │           │
│  │ Lorem ipsum  │  │ Lorem ipsum  │  │ Lorem ipsum  │           │
│  │ dolor sit    │  │ dolor sit    │  │ dolor sit    │           │
│  │ amet, cons-  │  │ amet, cons-  │  │ amet, cons-  │           │
│  │ ectetur ad-  │  │ ectetur ad-  │  │ ectetur ad-  │           │
│  │ ipisicing... │  │ ipisicing... │  │ ipisicing... │           │
│  │              │  │              │  │              │           │
│  │ [full text   │  │ [full text   │  │ [full text   │           │
│  │  scrollable  │  │  scrollable  │  │  scrollable  │           │
│  │  in card]    │  │  in card]    │  │  in card]    │           │
│  │              │  │              │  │              │           │
│  │              │  │              │  │              │           │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤           │
│  │ ⏱ 45s        │  │ ⏱ 67s        │  │ ⏱ 23s        │           │
│  │ 💰 $0.12     │  │ 💰 $0.18     │  │ 💰 $0.06     │           │
│  │ 📊 5000 tok  │  │ 📊 6800 tok  │  │ 📊 2800 tok  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ← Scroll for more configs →                                      │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Changes from AI ranking:                                          │
│  • None yet (same as AI order)                                     │
│                                                                    │
│  [Reset to AI Order] [Save My Ranking] [View Detailed Analysis]   │
└────────────────────────────────────────────────────────────────────┘
```

### Card Design (Results-First)

**Dimensions:**
- Width: 380px (fixed)
- Height: 600px (fixed, scrollable content)
- Gap between cards: 24px

**Card Structure:**

```
┌──────────────────────────────┐
│ 🥇 RANK #1   AI Score: 9.2/10│ ← Header (60px, sticky)
│ gpt5-standard                │
├──────────────────────────────┤
│                              │
│ RESPONSE TEXT (PRIMARY)      │ ← Main content (scrollable)
│                              │
│ This is the full response    │   - 16px font size
│ from the LLM. It can be      │   - Line height 1.6
│ quite long and will scroll   │   - Max-width for readability
│ within this card.            │   - Syntax highlighting if code
│                              │   - Markdown rendering
│ The user can read the entire │
│ response here and compare    │
│ it side-by-side with other   │
│ results in the carousel.     │
│                              │
│ Lorem ipsum dolor sit amet,  │
│ consectetur adipiscing elit. │
│ Sed do eiusmod tempor inc-   │
│ ididunt ut labore et dolore  │
│ magna aliqua.                │
│                              │
│ [Content continues...]       │
│                              │
│                              │
├──────────────────────────────┤
│ ⏱ 45.3s  💰 $0.12  📊 5000   │ ← Footer (metrics, 40px)
└──────────────────────────────┘
```

**Visual States:**

1. **Default State**
   - White background
   - Subtle border
   - Drop shadow

2. **Hover State**
   - Slightly larger shadow
   - Cursor changes to grab hand
   - Border becomes more visible

3. **Dragging State**
   - Increased scale (1.05x)
   - Stronger shadow
   - Slight rotation (2deg)
   - Reduced opacity (0.8)
   - Cursor: grabbing

4. **Drop Target State**
   - Between-card gap expands
   - Dashed line indicator
   - Highlighted drop zone

### Drag Interaction

**Desktop:**
- Hover over card → Grab cursor appears
- Click and hold → Card lifts, scales up
- Drag left/right → Card follows cursor
- Drop zones appear between cards
- Release → Card snaps to new position
- Animation: smooth 300ms ease-out

**Mobile:**
- Long press (500ms) → Card lifts
- Drag with touch → Card follows finger
- Visual feedback: haptic vibration
- Release → Card snaps to position

**Keyboard:**
- Tab to focus card
- Space bar → "Grab" card
- Arrow left/right → Move position
- Space bar again → "Drop" card
- Escape → Cancel move

### AI Evaluation Modal

```
┌────────────────────────────────────────────┐
│  Run AI Evaluation                      ✕  │
├────────────────────────────────────────────┤
│                                            │
│  Select Review Prompt Template:            │
│  ┌──────────────────────────────────────┐  │
│  │ Code Quality Reviewer             ▼ │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Select Evaluator Model:                   │
│  ┌──────────────────────────────────────┐  │
│  │ GPT-4 Turbo                       ▼ │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  This will evaluate 8 configurations       │
│  Estimated time: ~3 minutes                │
│  Estimated cost: ~$0.50                    │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ ⚙️ Advanced Options                   │  │
│  │   [ ] Include previous evaluations    │  │
│  │   [ ] Run in parallel (faster)        │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  [Cancel]              [Start Evaluation]  │
└────────────────────────────────────────────┘
```

**Progress State:**

```
┌────────────────────────────────────────────┐
│  Evaluating Results...                  ✕  │
├────────────────────────────────────────────┤
│                                            │
│  ████████████████░░░░░░  65% (5/8)        │
│                                            │
│  Currently evaluating: gpt5-detailed       │
│                                            │
│  ✓ gpt5-standard (9.2/10)                 │
│  ✓ gpt5-minimal (7.5/10)                  │
│  ✓ gpt5-compact (8.1/10)                  │
│  ✓ gpt5-concise (8.8/10)                  │
│  ⏳ gpt5-detailed...                       │
│  ⏳ gpt5-verbose                           │
│  ⏳ gpt5-thorough                          │
│  ⏳ gpt5-extended                          │
│                                            │
│  [Cancel Evaluation]                       │
└────────────────────────────────────────────┘
```

### Recommendation Display

**Location:** Top of Compare page after saving ranking

```
┌────────────────────────────────────────────────────────┐
│  🏆 RECOMMENDED CONFIGURATION                          │
│                                                        │
│  gpt5-standard                                         │
│  Confidence: HIGH (AI + 3 human rankings agree)        │
│                                                        │
│  Why this config won:                                  │
│  ✓ Highest quality (9.2/10, ranked #1 by all)         │
│  ✓ Balanced speed (45s, faster than 70% of configs)   │
│  ✓ Reasonable cost ($0.12, middle tier)               │
│                                                        │
│  Weighted Score: 8.9/10                                │
│  Quality: 9.2 (60%) | Speed: 8.5 (30%) | Cost: 7.8 (10%)│
│                                                        │
│  [Use This Config]  [View Full Breakdown]             │
└────────────────────────────────────────────────────────┘
```

### Agreement Metrics Display

**After saving human ranking:**

```
┌────────────────────────────────────────────┐
│  Your Ranking vs AI Evaluation             │
├────────────────────────────────────────────┤
│  Agreement: 87.5% ████████████████░░░░     │
│                                            │
│  ✅ Same top 3 configs                     │
│  ✅ Same winner (#1)                       │
│  ⚠️  2 position swaps                      │
│                                            │
│  Changes you made:                         │
│  • gpt5-detailed: #3 → #2 (moved up 1)    │
│  • gpt5-minimal: #2 → #3 (moved down 1)   │
│                                            │
│  Kendall Tau: 0.89 (strong agreement)     │
│                                            │
│  [View Detailed Comparison]                │
└────────────────────────────────────────────┘
```

---

## Data Models

### Review Prompt Template

```python
class ReviewPrompt(BaseModel):
    """Template for AI evaluation prompts"""
    prompt_id: str  # UUID
    name: str  # e.g., "Code Quality Reviewer"
    description: Optional[str]

    # The actual prompt template
    template: str  # Uses {original_prompt}, {config_name}, {result}
    system_prompt: Optional[str]

    # Evaluation criteria
    criteria: List[str]  # ["accuracy", "clarity", "completeness", ...]

    # Default evaluator model
    default_model: str  # "gpt-4-turbo", "claude-3-opus"

    # Metadata
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    # Example template:
    # """
    # You are evaluating LLM outputs for quality.
    #
    # ORIGINAL PROMPT: {original_prompt}
    # CONFIGURATION: {config_name}
    # OUTPUT: {result}
    #
    # Rate on criteria (1-10 each): accuracy, clarity, completeness
    # Return JSON: {"criteria_scores": {...}, "overall_score": 8.5, ...}
    # """
```

### AI Evaluation

```python
class AIEvaluation(BaseModel):
    """Result of AI evaluating a single experiment"""
    evaluation_id: str  # UUID
    experiment_id: str  # Links to experiment
    review_prompt_id: str  # Which template was used
    batch_id: str  # Groups evaluations from same batch

    # Evaluator info
    model_evaluator: str  # "gpt-4-turbo", "claude-3-opus"

    # Scores
    criteria_scores: Dict[str, float]  # {"accuracy": 8.5, "clarity": 9.0}
    overall_score: float  # 0-10

    # Ranking within this batch
    ai_rank: int  # 1 = best, 2 = second, etc.

    # Explanations
    justification: str  # 2-3 sentence explanation
    strengths: List[str]  # Key strengths identified
    weaknesses: List[str]  # Key weaknesses identified

    # Metadata
    evaluated_at: datetime
    evaluation_duration: float  # Seconds taken
```

### AI Evaluation Batch

```python
class AIEvaluationBatch(BaseModel):
    """Tracks a batch AI evaluation of all configs for a prompt"""
    batch_id: str  # UUID
    prompt_name: str
    review_prompt_id: str
    model_evaluator: str

    # Status
    status: str  # "pending", "running", "completed", "failed"
    num_experiments: int
    num_completed: int

    # Results
    evaluation_ids: List[str]  # All evaluations in this batch
    ranked_experiment_ids: List[str]  # Ordered by AI ranking

    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: Optional[float]

    # Cost
    estimated_cost: float
```

### Human Ranking

```python
class HumanRanking(BaseModel):
    """Human's ranking of configs for a prompt"""
    ranking_id: str  # UUID
    prompt_name: str
    evaluator_name: str  # Who did the ranking

    # The ranking (ordered list, best to worst)
    ranked_experiment_ids: List[str]

    # Context
    based_on_ai_batch_id: Optional[str]  # If started from AI ranking

    # Track changes from AI
    changes_from_ai: List[Dict]  # [{"experiment_id": "x", "from_rank": 2, "to_rank": 1}]

    # Agreement metrics
    ai_agreement_score: Optional[float]  # Kendall Tau: -1 to 1
    top_3_overlap: Optional[int]  # 0-3, how many of top 3 match
    exact_position_matches: Optional[int]  # How many same position

    # User notes
    notes: Optional[str]

    # Metadata
    created_at: datetime
    time_spent_seconds: float  # How long they spent ranking
```

### Ranking Weights

```python
class RankingWeights(BaseModel):
    """Configurable weights for recommendation algorithm"""
    prompt_name: str  # Weights can be per-prompt or global
    quality_weight: float  # 0-1, default 0.60
    speed_weight: float  # 0-1, default 0.30
    cost_weight: float  # 0-1, default 0.10

    # Validation: weights must sum to 1.0

    updated_by: str
    updated_at: datetime
```

### Recommendation

```python
class Recommendation(BaseModel):
    """Best config recommendation for a prompt"""
    prompt_name: str
    recommended_config: str  # Config name

    # Scoring
    final_score: float  # 0-10, weighted score
    quality_score: float
    speed_score: float
    cost_score: float

    # Confidence
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    confidence_factors: List[str]  # Reasons for confidence level

    # Evidence
    num_ai_evaluations: int
    num_human_rankings: int
    consensus_agreement: float  # If multiple humans

    # Reasoning
    reasoning: str  # Human-readable explanation

    # Alternatives
    runner_up_config: Optional[str]
    score_difference: Optional[float]  # How close was runner-up

    generated_at: datetime
```

---

## API Specification

### Review Prompt Endpoints

#### Create Review Prompt
```http
POST /api/review-prompts
Content-Type: application/json

{
  "name": "Code Quality Reviewer",
  "description": "Evaluates code quality and best practices",
  "template": "You are evaluating...",
  "system_prompt": "You are an expert...",
  "criteria": ["accuracy", "clarity", "completeness"],
  "default_model": "gpt-4-turbo"
}

Response 201:
{
  "prompt_id": "uuid-here",
  "name": "Code Quality Reviewer",
  ...
}
```

#### List Review Prompts
```http
GET /api/review-prompts?active_only=true

Response 200:
{
  "prompts": [
    {
      "prompt_id": "uuid-1",
      "name": "Code Quality Reviewer",
      "is_active": true,
      ...
    }
  ]
}
```

#### Get Review Prompt
```http
GET /api/review-prompts/{prompt_id}

Response 200:
{
  "prompt_id": "uuid-here",
  "name": "Code Quality Reviewer",
  "template": "...",
  ...
}
```

#### Update Review Prompt
```http
PUT /api/review-prompts/{prompt_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "template": "Updated template..."
}

Response 200:
{
  "prompt_id": "uuid-here",
  ...
}
```

#### Delete Review Prompt
```http
DELETE /api/review-prompts/{prompt_id}

Response 204: No Content
```

### AI Evaluation Endpoints

#### Start Batch Evaluation
```http
POST /api/ai-evaluate/batch
Content-Type: application/json

{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "review_prompt_id": "uuid-here",
  "model_evaluator": "gpt-4-turbo",
  "options": {
    "parallel": true,
    "include_previous": false
  }
}

Response 202:
{
  "batch_id": "batch-uuid",
  "status": "running",
  "num_experiments": 8,
  "estimated_duration": 180,
  "estimated_cost": 0.50
}
```

#### Get Batch Status
```http
GET /api/ai-evaluate/batch/{batch_id}

Response 200:
{
  "batch_id": "batch-uuid",
  "status": "running",
  "num_experiments": 8,
  "num_completed": 5,
  "progress": 0.625,
  "current_experiment": "gpt5-detailed",
  "evaluations": [
    {
      "experiment_id": "exp-1",
      "status": "completed",
      "overall_score": 9.2,
      "ai_rank": 1
    },
    ...
  ]
}
```

#### Get AI Evaluations for Prompt
```http
GET /api/ai-evaluations/prompt/{prompt_name}?latest=true

Response 200:
{
  "batch_id": "batch-uuid",
  "evaluated_at": "2025-11-08T10:30:00Z",
  "model_evaluator": "gpt-4-turbo",
  "ranked_experiments": [
    {
      "experiment_id": "exp-1",
      "config_name": "gpt5-standard",
      "ai_rank": 1,
      "overall_score": 9.2,
      "criteria_scores": {
        "accuracy": 9.0,
        "clarity": 9.5,
        "completeness": 9.0
      },
      "justification": "Excellent response...",
      "strengths": ["Clear structure", "Accurate"],
      "weaknesses": ["Could be more concise"]
    },
    ...
  ]
}
```

#### Get Single AI Evaluation
```http
GET /api/ai-evaluations/{evaluation_id}

Response 200:
{
  "evaluation_id": "eval-uuid",
  "experiment_id": "exp-1",
  "overall_score": 9.2,
  ...
}
```

### Human Ranking Endpoints

#### Save Human Ranking
```http
POST /api/rankings
Content-Type: application/json

{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "evaluator_name": "Bill",
  "ranked_experiment_ids": ["exp-1", "exp-3", "exp-2", "exp-4"],
  "based_on_ai_batch_id": "batch-uuid",
  "notes": "Preferred exp-3 over exp-2 for clarity"
}

Response 201:
{
  "ranking_id": "rank-uuid",
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "ranked_experiment_ids": ["exp-1", "exp-3", "exp-2", "exp-4"],
  "changes_from_ai": [
    {
      "experiment_id": "exp-3",
      "from_rank": 3,
      "to_rank": 2,
      "direction": "up"
    },
    {
      "experiment_id": "exp-2",
      "from_rank": 2,
      "to_rank": 3,
      "direction": "down"
    }
  ],
  "ai_agreement_score": 0.87,
  "top_3_overlap": 3,
  "exact_position_matches": 6,
  "created_at": "2025-11-08T11:00:00Z"
}
```

#### Get Rankings for Prompt
```http
GET /api/rankings/prompt/{prompt_name}

Response 200:
{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "rankings": [
    {
      "ranking_id": "rank-1",
      "evaluator_name": "Bill",
      "ranked_experiment_ids": [...],
      "created_at": "2025-11-08T11:00:00Z",
      ...
    },
    ...
  ],
  "consensus": {
    "ranked_experiment_ids": [...],
    "confidence_scores": {"exp-1": 45, "exp-2": 38, ...},
    "num_rankers": 3
  }
}
```

#### Get Consensus Ranking
```http
GET /api/rankings/consensus/{prompt_name}

Response 200:
{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "consensus_ranking": ["exp-1", "exp-3", "exp-2", ...],
  "confidence_scores": {
    "exp-1": 45,
    "exp-3": 38,
    "exp-2": 31,
    ...
  },
  "num_rankers": 3,
  "agreement_with_ai": 0.85,
  "variability": "low"
}
```

### Recommendation Endpoints

#### Get Recommendation
```http
GET /api/recommendations/{prompt_name}

Response 200:
{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "recommended_config": "gpt5-standard",
  "final_score": 8.9,
  "quality_score": 9.2,
  "speed_score": 8.5,
  "cost_score": 7.8,
  "confidence": "HIGH",
  "confidence_factors": [
    "Multiple human rankings agree",
    "AI evaluation confidence: high",
    "Low variance in scores"
  ],
  "num_ai_evaluations": 1,
  "num_human_rankings": 3,
  "consensus_agreement": 1.0,
  "reasoning": "gpt5-standard achieved the highest quality score (9.2/10) and was ranked #1 by all 3 human evaluators. It offers balanced performance with 45s duration and $0.12 cost.",
  "runner_up_config": "gpt5-detailed",
  "score_difference": 0.3,
  "breakdown": {
    "gpt5-standard": {
      "final_score": 8.9,
      "quality": 9.2,
      "speed": 8.5,
      "cost": 7.8
    },
    "gpt5-detailed": {
      "final_score": 8.6,
      "quality": 8.8,
      "speed": 7.2,
      "cost": 6.9
    },
    ...
  }
}
```

#### Update Weights
```http
POST /api/recommendations/weights/{prompt_name}
Content-Type: application/json

{
  "quality_weight": 0.70,
  "speed_weight": 0.20,
  "cost_weight": 0.10
}

Response 200:
{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "weights": {
    "quality_weight": 0.70,
    "speed_weight": 0.20,
    "cost_weight": 0.10
  },
  "updated_recommendation": {
    "recommended_config": "gpt5-standard",
    "final_score": 9.0,
    ...
  }
}
```

### Compare Page Data Endpoint

#### Get All Compare Data
```http
GET /api/compare/{prompt_name}

Response 200:
{
  "prompt_name": "re-organize-idea-wooden-puzzle",
  "experiments": [
    {
      "experiment_id": "exp-1",
      "config_name": "gpt5-standard",
      "response": "Full response text...",
      "duration_seconds": 45.3,
      "estimated_cost_usd": 0.12,
      "total_tokens": 5000,
      ...
    },
    ...
  ],
  "ai_evaluation": {
    "batch_id": "batch-uuid",
    "model_evaluator": "gpt-4-turbo",
    "review_prompt_name": "Code Quality Reviewer",
    "ranked_experiment_ids": ["exp-1", "exp-3", "exp-2", ...],
    "evaluations": [
      {
        "experiment_id": "exp-1",
        "ai_rank": 1,
        "overall_score": 9.2,
        "criteria_scores": {...},
        "justification": "...",
        "strengths": [...],
        "weaknesses": [...]
      },
      ...
    ]
  },
  "human_rankings": [
    {
      "ranking_id": "rank-1",
      "evaluator_name": "Bill",
      "ranked_experiment_ids": [...],
      "ai_agreement_score": 0.87,
      ...
    }
  ],
  "consensus": {
    "ranked_experiment_ids": [...],
    "confidence_scores": {...}
  },
  "recommendation": {
    "recommended_config": "gpt5-standard",
    "final_score": 8.9,
    "confidence": "HIGH",
    ...
  }
}
```

---

## Backend Implementation

### File Structure

```
src/prompt_benchmark/
├── models.py                # Add new models
├── storage.py              # Add new DB tables/methods
├── evaluator.py            # Enhance with batch AI evaluation
├── ranker.py               # NEW: Ranking algorithms
├── recommender.py          # NEW: Recommendation engine
└── api/
    ├── schemas.py          # Add new schemas
    └── routes.py           # Add new endpoints
```

### Database Schema

```sql
-- Review prompt templates
CREATE TABLE review_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    template TEXT NOT NULL,
    system_prompt TEXT,
    criteria JSON NOT NULL,
    default_model VARCHAR,
    created_by VARCHAR,
    created_at DATETIME,
    updated_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);

-- AI evaluation batches
CREATE TABLE ai_evaluation_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id VARCHAR UNIQUE NOT NULL,
    prompt_name VARCHAR NOT NULL,
    review_prompt_id VARCHAR NOT NULL,
    model_evaluator VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    num_experiments INTEGER,
    num_completed INTEGER DEFAULT 0,
    started_at DATETIME,
    completed_at DATETIME,
    total_duration FLOAT,
    estimated_cost FLOAT,
    FOREIGN KEY (review_prompt_id) REFERENCES review_prompts(prompt_id)
);

-- AI evaluations
CREATE TABLE ai_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id VARCHAR UNIQUE NOT NULL,
    experiment_id VARCHAR NOT NULL,
    review_prompt_id VARCHAR NOT NULL,
    batch_id VARCHAR NOT NULL,
    model_evaluator VARCHAR NOT NULL,
    criteria_scores JSON NOT NULL,
    overall_score FLOAT NOT NULL,
    ai_rank INTEGER,
    justification TEXT,
    strengths JSON,
    weaknesses JSON,
    evaluated_at DATETIME,
    evaluation_duration FLOAT,
    FOREIGN KEY (experiment_id) REFERENCES experiment_results(experiment_id),
    FOREIGN KEY (review_prompt_id) REFERENCES review_prompts(prompt_id),
    FOREIGN KEY (batch_id) REFERENCES ai_evaluation_batches(batch_id)
);

-- Human rankings
CREATE TABLE human_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ranking_id VARCHAR UNIQUE NOT NULL,
    prompt_name VARCHAR NOT NULL,
    evaluator_name VARCHAR NOT NULL,
    ranked_experiment_ids JSON NOT NULL,
    based_on_ai_batch_id VARCHAR,
    changes_from_ai JSON,
    ai_agreement_score FLOAT,
    top_3_overlap INTEGER,
    exact_position_matches INTEGER,
    notes TEXT,
    created_at DATETIME,
    time_spent_seconds FLOAT,
    FOREIGN KEY (based_on_ai_batch_id) REFERENCES ai_evaluation_batches(batch_id)
);

-- Ranking weights
CREATE TABLE ranking_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_name VARCHAR UNIQUE,
    quality_weight FLOAT NOT NULL DEFAULT 0.60,
    speed_weight FLOAT NOT NULL DEFAULT 0.30,
    cost_weight FLOAT NOT NULL DEFAULT 0.10,
    updated_by VARCHAR,
    updated_at DATETIME,
    CHECK (quality_weight + speed_weight + cost_weight = 1.0)
);
```

### Key Backend Functions

#### Batch AI Evaluation

```python
# src/prompt_benchmark/evaluator.py

async def batch_evaluate_prompt(
    prompt_name: str,
    review_prompt: ReviewPrompt,
    evaluator_model: str,
    storage: ResultStorage,
    parallel: bool = True
) -> AIEvaluationBatch:
    """
    Evaluate all experiments for a prompt using AI.

    Args:
        prompt_name: Name of prompt to evaluate
        review_prompt: Review prompt template to use
        evaluator_model: Model to use for evaluation (e.g., "gpt-4-turbo")
        storage: Database storage
        parallel: Run evaluations in parallel (default True)

    Returns:
        AIEvaluationBatch with all evaluations and rankings
    """

    # 1. Get all successful experiments for this prompt
    experiments = storage.get_results_by_prompt(prompt_name, success_only=True)

    # 2. Create batch record
    batch = AIEvaluationBatch(
        batch_id=str(uuid.uuid4()),
        prompt_name=prompt_name,
        review_prompt_id=review_prompt.prompt_id,
        model_evaluator=evaluator_model,
        status="running",
        num_experiments=len(experiments),
        started_at=datetime.utcnow()
    )
    storage.save_ai_batch(batch)

    # 3. Evaluate each experiment
    evaluations = []

    if parallel:
        # Run in parallel with rate limiting
        tasks = [
            evaluate_single_experiment(exp, review_prompt, evaluator_model, batch.batch_id)
            for exp in experiments
        ]
        evaluations = await asyncio.gather(*tasks)
    else:
        # Run sequentially
        for exp in experiments:
            eval = await evaluate_single_experiment(exp, review_prompt, evaluator_model, batch.batch_id)
            evaluations.append(eval)

            # Update progress
            batch.num_completed += 1
            storage.update_ai_batch(batch)

    # 4. Rank evaluations by overall_score
    evaluations.sort(key=lambda e: e.overall_score, reverse=True)
    for i, eval in enumerate(evaluations):
        eval.ai_rank = i + 1

    # 5. Save all evaluations
    for eval in evaluations:
        storage.save_ai_evaluation(eval)

    # 6. Update batch as completed
    batch.status = "completed"
    batch.num_completed = len(evaluations)
    batch.completed_at = datetime.utcnow()
    batch.total_duration = (batch.completed_at - batch.started_at).total_seconds()
    batch.evaluation_ids = [e.evaluation_id for e in evaluations]
    batch.ranked_experiment_ids = [e.experiment_id for e in evaluations]
    storage.update_ai_batch(batch)

    return batch


async def evaluate_single_experiment(
    experiment: ExperimentResult,
    review_prompt: ReviewPrompt,
    evaluator_model: str,
    batch_id: str
) -> AIEvaluation:
    """Evaluate a single experiment using AI."""

    # Render the review prompt
    rendered_prompt = review_prompt.template.format(
        original_prompt=experiment.rendered_prompt,
        config_name=experiment.config_name,
        result=experiment.response
    )

    # Call evaluator LLM
    start_time = time.time()

    client = AsyncOpenAI()  # or Claude client
    response = await client.chat.completions.create(
        model=evaluator_model,
        messages=[
            {"role": "system", "content": review_prompt.system_prompt or "You are an expert evaluator."},
            {"role": "user", "content": rendered_prompt}
        ],
        response_format={"type": "json_object"}  # Ensure JSON response
    )

    duration = time.time() - start_time

    # Parse response
    eval_data = json.loads(response.choices[0].message.content)

    # Create evaluation object
    evaluation = AIEvaluation(
        evaluation_id=str(uuid.uuid4()),
        experiment_id=experiment.experiment_id,
        review_prompt_id=review_prompt.prompt_id,
        batch_id=batch_id,
        model_evaluator=evaluator_model,
        criteria_scores=eval_data["criteria_scores"],
        overall_score=eval_data["overall_score"],
        justification=eval_data.get("justification", ""),
        strengths=eval_data.get("key_strengths", []),
        weaknesses=eval_data.get("key_weaknesses", []),
        evaluated_at=datetime.utcnow(),
        evaluation_duration=duration
    )

    return evaluation
```

#### Calculate Agreement

```python
# src/prompt_benchmark/ranker.py

def calculate_agreement(
    ai_ranking: List[str],
    human_ranking: List[str]
) -> Dict[str, Any]:
    """
    Calculate agreement metrics between AI and human rankings.

    Uses Kendall Tau correlation and other metrics.
    """

    # Kendall Tau: measures rank correlation
    tau = calculate_kendall_tau(ai_ranking, human_ranking)

    # Top-3 overlap: how many of top 3 are the same
    top_3_ai = set(ai_ranking[:3])
    top_3_human = set(human_ranking[:3])
    top_3_overlap = len(top_3_ai & top_3_human)

    # Exact position matches
    exact_matches = sum(
        1 for i in range(len(ai_ranking))
        if ai_ranking[i] == human_ranking[i]
    )

    # Track all position changes
    changes = []
    for exp_id in ai_ranking:
        ai_pos = ai_ranking.index(exp_id) + 1
        human_pos = human_ranking.index(exp_id) + 1
        if ai_pos != human_pos:
            changes.append({
                "experiment_id": exp_id,
                "from_rank": ai_pos,
                "to_rank": human_pos,
                "direction": "up" if human_pos < ai_pos else "down",
                "magnitude": abs(human_pos - ai_pos)
            })

    return {
        "kendall_tau": tau,
        "top_3_overlap": top_3_overlap,
        "exact_position_matches": exact_matches,
        "agreement_percentage": (exact_matches / len(ai_ranking)) * 100,
        "changes": changes,
        "num_changes": len(changes)
    }


def calculate_kendall_tau(ranking1: List[str], ranking2: List[str]) -> float:
    """
    Kendall Tau correlation coefficient.

    Measures ordinal association between two rankings.
    Returns value between -1 (complete disagreement) and 1 (complete agreement).
    """
    n = len(ranking1)
    concordant = 0
    discordant = 0

    # Create position maps
    pos1 = {item: i for i, item in enumerate(ranking1)}
    pos2 = {item: i for i, item in enumerate(ranking2)}

    # Count concordant and discordant pairs
    for i in range(n):
        for j in range(i + 1, n):
            item_i = ranking1[i]
            item_j = ranking1[j]

            # Check if pair is concordant or discordant
            if (pos2[item_i] < pos2[item_j]):
                concordant += 1
            else:
                discordant += 1

    # Calculate tau
    tau = (concordant - discordant) / (n * (n - 1) / 2)
    return tau
```

#### Consensus Ranking

```python
# src/prompt_benchmark/ranker.py

def calculate_consensus_ranking(
    rankings: List[HumanRanking],
    ai_ranking: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate consensus from multiple human rankings using Borda count.

    Each ranker assigns points: n points for 1st place, n-1 for 2nd, etc.
    Sum points for each item to get consensus ranking.
    """

    if not rankings:
        return None

    # Initialize scores
    scores = defaultdict(float)
    n = len(rankings[0].ranked_experiment_ids)

    # Borda count
    for ranking in rankings:
        for position, exp_id in enumerate(ranking.ranked_experiment_ids):
            points = n - position  # Higher position = more points
            scores[exp_id] += points

    # Sort by score (descending)
    consensus = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    # Calculate agreement with AI if provided
    ai_agreement = None
    if ai_ranking:
        ai_agreement = calculate_agreement(ai_ranking, consensus)

    # Calculate variability (how much humans disagree)
    variability = calculate_ranking_variability(rankings)

    return {
        "consensus_ranking": consensus,
        "confidence_scores": dict(scores),
        "num_rankers": len(rankings),
        "ai_agreement": ai_agreement,
        "variability": variability
    }
```

#### Weighted Recommendation

```python
# src/prompt_benchmark/recommender.py

def calculate_recommendation(
    prompt_name: str,
    storage: ResultStorage,
    weights: Optional[RankingWeights] = None
) -> Recommendation:
    """
    Calculate best config recommendation based on weighted scoring.

    Default weights: quality 60%, speed 30%, cost 10%
    """

    # Get weights (use defaults if not provided)
    if weights is None:
        weights = storage.get_weights(prompt_name) or RankingWeights(
            prompt_name=prompt_name,
            quality_weight=0.60,
            speed_weight=0.30,
            cost_weight=0.10
        )

    # Get all data
    experiments = storage.get_results_by_prompt(prompt_name, success_only=True)
    ai_evals = storage.get_ai_evaluations_by_prompt(prompt_name)
    human_rankings = storage.get_human_rankings_by_prompt(prompt_name)

    # Group by config
    config_groups = {}
    for exp in experiments:
        if exp.config_name not in config_groups:
            config_groups[exp.config_name] = []
        config_groups[exp.config_name].append(exp)

    # Calculate scores for each config
    config_scores = {}

    for config_name, exps in config_groups.items():
        # Quality score (from evaluations)
        quality = calculate_quality_score(config_name, ai_evals, human_rankings)

        # Speed score (normalized, inverted - faster is better)
        avg_duration = sum(e.duration_seconds for e in exps) / len(exps)
        max_duration = max(e.duration_seconds for e in experiments)
        speed = 10 * (1 - (avg_duration / max_duration))

        # Cost score (normalized, inverted - cheaper is better)
        avg_cost = sum(e.estimated_cost_usd for e in exps) / len(exps)
        max_cost = max(e.estimated_cost_usd for e in experiments)
        cost = 10 * (1 - (avg_cost / max_cost))

        # Weighted final score
        final_score = (
            quality * weights.quality_weight +
            speed * weights.speed_weight +
            cost * weights.cost_weight
        )

        config_scores[config_name] = {
            "final_score": final_score,
            "quality_score": quality,
            "speed_score": speed,
            "cost_score": cost
        }

    # Find best config
    best_config = max(config_scores.keys(), key=lambda k: config_scores[k]["final_score"])

    # Calculate confidence
    confidence, confidence_factors = calculate_confidence(
        best_config, ai_evals, human_rankings
    )

    # Generate reasoning
    reasoning = generate_reasoning(best_config, config_scores, experiments, ai_evals, human_rankings)

    # Find runner-up
    sorted_configs = sorted(config_scores.keys(), key=lambda k: config_scores[k]["final_score"], reverse=True)
    runner_up = sorted_configs[1] if len(sorted_configs) > 1 else None
    score_diff = config_scores[best_config]["final_score"] - config_scores[runner_up]["final_score"] if runner_up else 0

    return Recommendation(
        prompt_name=prompt_name,
        recommended_config=best_config,
        final_score=config_scores[best_config]["final_score"],
        quality_score=config_scores[best_config]["quality_score"],
        speed_score=config_scores[best_config]["speed_score"],
        cost_score=config_scores[best_config]["cost_score"],
        confidence=confidence,
        confidence_factors=confidence_factors,
        num_ai_evaluations=len(ai_evals),
        num_human_rankings=len(human_rankings),
        reasoning=reasoning,
        runner_up_config=runner_up,
        score_difference=score_diff,
        generated_at=datetime.utcnow()
    )


def calculate_quality_score(
    config_name: str,
    ai_evals: List[AIEvaluation],
    human_rankings: List[HumanRanking]
) -> float:
    """
    Calculate quality score from AI evaluations and human rankings.

    Priority:
    1. If human rankings exist, use consensus
    2. Otherwise, use AI evaluation
    3. Otherwise, return 5.0 (neutral)
    """

    # Find evaluations for this config
    config_ai_evals = [e for e in ai_evals if e.experiment_id.startswith(config_name)]

    if human_rankings:
        # Use human consensus
        # Convert rankings to scores (1st = 10, 2nd = 9, etc.)
        scores = []
        for ranking in human_rankings:
            if config_name in ranking.ranked_experiment_ids:
                position = ranking.ranked_experiment_ids.index(config_name)
                # Convert position to score (lower position = higher score)
                score = 10 - (position * 10 / len(ranking.ranked_experiment_ids))
                scores.append(score)

        return sum(scores) / len(scores) if scores else 5.0

    elif config_ai_evals:
        # Use AI evaluation
        return sum(e.overall_score for e in config_ai_evals) / len(config_ai_evals)

    else:
        # No evaluations yet
        return 5.0


def calculate_confidence(
    config_name: str,
    ai_evals: List[AIEvaluation],
    human_rankings: List[HumanRanking]
) -> Tuple[str, List[str]]:
    """
    Determine confidence level and factors.

    Returns: ("HIGH"|"MEDIUM"|"LOW", [list of reasons])
    """

    factors = []
    score = 0

    # Check for AI evaluations
    if ai_evals:
        score += 1
        factors.append("AI evaluation available")

    # Check for human rankings
    if human_rankings:
        score += 2
        factors.append(f"{len(human_rankings)} human ranking(s)")

        # Check for agreement
        if len(human_rankings) > 1:
            # Calculate variance
            variance = calculate_ranking_variance(human_rankings, config_name)
            if variance < 1.0:
                score += 1
                factors.append("High human agreement")
            else:
                factors.append("Some human disagreement")

    # Check AI-human agreement
    if ai_evals and human_rankings:
        # Check if humans agreed with AI
        consensus = calculate_consensus_ranking(human_rankings)
        if consensus and config_name == consensus["consensus_ranking"][0]:
            score += 1
            factors.append("Humans confirm AI ranking")

    # Determine confidence
    if score >= 4:
        confidence = "HIGH"
    elif score >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
        if not human_rankings:
            factors.append("No human rankings yet")

    return confidence, factors
```

---

## Frontend Implementation

### File Structure

```
frontend/src/
├── types/
│   └── index.ts              # Add new types
├── api/
│   └── client.ts             # Add new API methods
├── hooks/
│   ├── useRankings.ts        # NEW: Ranking hooks
│   └── useReviewPrompts.ts   # NEW: Review prompt hooks
├── components/
│   ├── RankingCard.tsx       # NEW: Result card
│   ├── DragCarousel.tsx      # NEW: Drag container
│   └── RecommendationBanner.tsx  # NEW
├── pages/
│   ├── Compare.tsx           # NEW: Main ranking page
│   ├── ReviewPrompts.tsx     # NEW: Template management
│   └── Analysis.tsx          # Enhanced with recommendations
└── utils/
    └── dragUtils.ts          # NEW: Drag helpers
```

### Key Components

#### RankingCard Component

```typescript
// frontend/src/components/RankingCard.tsx

interface RankingCardProps {
  experiment: Experiment;
  rank: number;
  aiScore?: number;
  aiRank?: number;
  isDragging: boolean;
  dragHandleProps: any;
}

export function RankingCard({
  experiment,
  rank,
  aiScore,
  aiRank,
  isDragging,
  dragHandleProps
}: RankingCardProps) {
  const getRankBadge = (rank: number) => {
    const badges = {
      1: { emoji: '🥇', color: 'text-yellow-600', bg: 'bg-yellow-50' },
      2: { emoji: '🥈', color: 'text-gray-600', bg: 'bg-gray-50' },
      3: { emoji: '🥉', color: 'text-orange-600', bg: 'bg-orange-50' },
    };
    return badges[rank] || { emoji: '', color: 'text-gray-500', bg: 'bg-white' };
  };

  const badge = getRankBadge(rank);

  return (
    <div
      className={`
        ranking-card
        w-[380px] h-[600px]
        bg-white rounded-lg shadow-md border border-gray-200
        flex flex-col
        transition-all duration-300
        ${isDragging ? 'scale-105 shadow-2xl opacity-80 rotate-2' : 'hover:shadow-lg'}
      `}
      {...dragHandleProps}
    >
      {/* Header - Sticky */}
      <div className={`
        ${badge.bg} ${badge.color}
        p-4 rounded-t-lg border-b border-gray-200
        flex items-center justify-between
        sticky top-0 z-10
      `}>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{badge.emoji}</span>
          <div>
            <div className="font-bold text-lg">RANK #{rank}</div>
            <div className="text-sm font-medium">{experiment.config_name}</div>
          </div>
        </div>
        {aiScore && (
          <div className="text-right">
            <div className="text-xs text-gray-600">AI Score</div>
            <div className="text-lg font-bold">{aiScore.toFixed(1)}/10</div>
            {aiRank !== rank && (
              <div className="text-xs text-orange-600">AI: #{aiRank}</div>
            )}
          </div>
        )}
      </div>

      {/* Main Content - Response (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
            {experiment.response}
          </div>
        </div>
      </div>

      {/* Footer - Metrics */}
      <div className="p-3 bg-gray-50 rounded-b-lg border-t border-gray-200 flex justify-around text-xs">
        <div className="flex items-center gap-1">
          <span>⏱</span>
          <span className="font-medium">{experiment.duration_seconds.toFixed(1)}s</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💰</span>
          <span className="font-medium">${experiment.estimated_cost_usd.toFixed(4)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>📊</span>
          <span className="font-medium">{experiment.total_tokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
```

#### DragCarousel Component

```typescript
// frontend/src/components/DragCarousel.tsx
import { DndContext, DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { SortableContext, horizontalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface DragCarouselProps {
  experiments: Experiment[];
  aiEvaluations?: Map<string, AIEvaluation>;
  onReorder: (newOrder: string[]) => void;
}

function SortableCard({ experiment, rank, aiEval }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: experiment.experiment_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <RankingCard
        experiment={experiment}
        rank={rank}
        aiScore={aiEval?.overall_score}
        aiRank={aiEval?.ai_rank}
        isDragging={isDragging}
        dragHandleProps={listeners}
      />
    </div>
  );
}

export function DragCarousel({ experiments, aiEvaluations, onReorder }: DragCarouselProps) {
  const [items, setItems] = useState(experiments);
  const [activeId, setActiveId] = useState<string | null>(null);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex(item => item.experiment_id === active.id);
      const newIndex = items.findIndex(item => item.experiment_id === over.id);

      const newItems = arrayMove(items, oldIndex, newIndex);
      setItems(newItems);
      onReorder(newItems.map(item => item.experiment_id));
    }
  };

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="relative">
        <SortableContext
          items={items.map(exp => exp.experiment_id)}
          strategy={horizontalListSortingStrategy}
        >
          <div className="flex gap-6 overflow-x-auto pb-4 px-4">
            {items.map((exp, index) => (
              <SortableCard
                key={exp.experiment_id}
                experiment={exp}
                rank={index + 1}
                aiEval={aiEvaluations?.get(exp.experiment_id)}
              />
            ))}
          </div>
        </SortableContext>
      </div>
    </DndContext>
  );
}
```

#### Compare Page

```typescript
// frontend/src/pages/Compare.tsx

export default function Compare() {
  const { promptName } = useParams<{ promptName: string }>();
  const [rankedIds, setRankedIds] = useState<string[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  // Fetch all data
  const { data: compareData, isLoading } = useQuery({
    queryKey: ['compare', promptName],
    queryFn: () => api.getCompareData(promptName!),
  });

  const saveRanking = useMutation({
    mutationFn: (ranking: RankingCreate) => api.createRanking(ranking),
    onSuccess: () => {
      // Show success, refresh data
    },
  });

  useEffect(() => {
    if (compareData) {
      // Initialize with AI ranking or default order
      const initialOrder = compareData.ai_evaluation
        ? compareData.ai_evaluation.ranked_experiment_ids
        : compareData.experiments.map(exp => exp.experiment_id);

      setRankedIds(initialOrder);
    }
  }, [compareData]);

  const handleReorder = (newOrder: string[]) => {
    setRankedIds(newOrder);

    // Check if different from AI ranking
    const aiOrder = compareData?.ai_evaluation?.ranked_experiment_ids || [];
    setHasChanges(JSON.stringify(newOrder) !== JSON.stringify(aiOrder));
  };

  const handleSave = () => {
    saveRanking.mutate({
      prompt_name: promptName!,
      evaluator_name: 'Current User', // Get from auth
      ranked_experiment_ids: rankedIds,
      based_on_ai_batch_id: compareData?.ai_evaluation?.batch_id,
    });
  };

  if (isLoading) return <LoadingSpinner />;
  if (!compareData) return <ErrorMessage />;

  const orderedExperiments = rankedIds
    .map(id => compareData.experiments.find(exp => exp.experiment_id === id))
    .filter(Boolean);

  const aiEvalMap = new Map(
    compareData.ai_evaluation?.evaluations.map(eval => [
      eval.experiment_id,
      eval
    ]) || []
  );

  return (
    <div className="max-w-full">
      {/* Header */}
      <div className="mb-6">
        <Link to="/experiments" className="text-blue-600 hover:underline">
          ← Back to Experiments
        </Link>
        <h1 className="text-3xl font-bold mt-2">Compare: {promptName}</h1>
      </div>

      {/* AI Evaluation Status */}
      {compareData.ai_evaluation ? (
        <AIEvaluationBanner evaluation={compareData.ai_evaluation} />
      ) : (
        <RunEvaluationPrompt promptName={promptName!} />
      )}

      {/* Recommendation */}
      {compareData.recommendation && (
        <RecommendationBanner recommendation={compareData.recommendation} />
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          💡 <strong>Drag cards left/right to rank</strong> • Best (left) → Worst (right)
        </p>
      </div>

      {/* Carousel */}
      <DragCarousel
        experiments={orderedExperiments}
        aiEvaluations={aiEvalMap}
        onReorder={handleReorder}
      />

      {/* Changes Summary */}
      {hasChanges && (
        <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h3 className="font-semibold text-orange-900 mb-2">
            Changes from AI ranking:
          </h3>
          <ChangesSummary
            aiOrder={compareData.ai_evaluation!.ranked_experiment_ids}
            humanOrder={rankedIds}
            experiments={compareData.experiments}
          />
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex gap-4 justify-center">
        <button
          onClick={() => {
            setRankedIds(compareData.ai_evaluation!.ranked_experiment_ids);
            setHasChanges(false);
          }}
          className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Reset to AI Order
        </button>
        <button
          onClick={handleSave}
          disabled={!hasChanges}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          Save My Ranking
        </button>
      </div>
    </div>
  );
}
```

---

## Algorithms

### Weighted Scoring Formula

```
final_score = (quality × 0.60) + (speed × 0.30) + (cost × 0.10)

where:
  quality = 0-10 from evaluations (AI or human consensus)
  speed = 10 × (1 - (duration / max_duration))  // normalized, inverted
  cost = 10 × (1 - (cost / max_cost))  // normalized, inverted
```

### Kendall Tau Calculation

```
τ = (concordant_pairs - discordant_pairs) / total_pairs

where:
  concordant_pairs = pairs in same order in both rankings
  discordant_pairs = pairs in different order
  total_pairs = n(n-1)/2 for n items

Range: -1 (complete disagreement) to 1 (perfect agreement)
```

### Borda Count for Consensus

```
For each ranker:
  - 1st place gets n points
  - 2nd place gets n-1 points
  - 3rd place gets n-2 points
  - ...
  - Last place gets 1 point

Sum all points for each item across all rankers
Sort by total points (descending) to get consensus ranking
```

---

## Implementation Plan

### Phase 1: AI Evaluation System (Week 1)

**Days 1-2: Backend Foundation**
- [ ] Add new models to `models.py`
- [ ] Create database tables in `storage.py`
- [ ] Implement review prompt CRUD
- [ ] Basic batch evaluation function

**Days 3-4: API & Evaluation Logic**
- [ ] Add API endpoints for review prompts
- [ ] Implement batch AI evaluation with progress tracking
- [ ] Add API endpoint for starting/monitoring batch evaluation
- [ ] Error handling and retries

**Day 5: Frontend - Review Prompts**
- [ ] Review prompt management page
- [ ] "Run AI Evaluation" modal
- [ ] Progress indicator component
- [ ] Display AI results

### Phase 2: Human Ranking UI (Week 2)

**Days 1-2: Compare Page Foundation**
- [ ] Create Compare page route and layout
- [ ] Fetch and display experiments
- [ ] RankingCard component (results-first design)
- [ ] Basic list view

**Days 3-4: Drag & Drop**
- [ ] Install and configure @dnd-kit
- [ ] Implement DragCarousel component
- [ ] Smooth drag animations
- [ ] Mobile touch support
- [ ] Keyboard accessibility

**Day 5: Save & Tracking**
- [ ] Save ranking endpoint
- [ ] Calculate changes from AI
- [ ] Agreement metrics display
- [ ] Changes summary component

### Phase 3: Recommendations (Week 3)

**Days 1-2: Recommendation Engine**
- [ ] Weighted scoring algorithm
- [ ] Quality score calculation
- [ ] Confidence calculation
- [ ] Consensus ranking algorithm
- [ ] Recommendation generation

**Days 3-4: UI Display**
- [ ] RecommendationBanner component
- [ ] Detailed breakdown view
- [ ] Agreement metrics visualization
- [ ] Weight configuration UI

**Day 5: Integration & Testing**
- [ ] End-to-end testing
- [ ] Edge case handling
- [ ] Performance optimization
- [ ] Documentation

### Phase 4: Polish & Features (Week 4)

**Days 1-2: Enhanced Analysis**
- [ ] Update Analysis page with recommendations
- [ ] Add consensus rankings
- [ ] Historical ranking views
- [ ] Export rankings

**Days 3-4: UX Improvements**
- [ ] Tutorial overlays
- [ ] Keyboard shortcuts
- [ ] Loading skeletons
- [ ] Error states
- [ ] Mobile optimizations

**Day 5: Documentation & Launch**
- [ ] User guide
- [ ] API documentation
- [ ] Review prompt examples
- [ ] Video walkthrough

---

## Testing Checklist

### Unit Tests

- [ ] Kendall Tau calculation
- [ ] Borda count consensus
- [ ] Weighted scoring
- [ ] Agreement metrics
- [ ] Quality score calculation

### Integration Tests

- [ ] Batch AI evaluation
- [ ] Save human ranking
- [ ] Calculate recommendation
- [ ] Update weights, recalculate

### UI Tests

- [ ] Drag and drop cards
- [ ] Reorder updates state
- [ ] Save ranking workflow
- [ ] Display AI vs human diff
- [ ] Keyboard navigation

### E2E Tests

- [ ] Full workflow: run experiments → AI evaluate → human rank → recommendation
- [ ] Multiple users ranking same prompt
- [ ] Re-evaluate with different template
- [ ] Adjust weights, see updated recommendation

---

## Success Metrics

### Functional Metrics

- AI evaluation completes in < 5 minutes for 10 configs
- Human ranking saved successfully 100% of the time
- Recommendation generated with confidence level
- Agreement metrics calculated correctly

### UX Metrics

- Time to complete ranking < 5 minutes
- Drag interaction feels smooth (no jank)
- Mobile users can rank effectively
- First-time users complete flow without help

### Business Metrics

- Users find optimal config faster
- Confidence in recommendations high
- Human-AI agreement improves over time
- Users trust and use recommended configs

---

## Future Enhancements

### Phase 5 (Future)

- **A/B Testing Integration**: Track which configs actually perform better in production
- **Automated Re-ranking**: Trigger AI re-evaluation when new data available
- **Multi-Prompt Analysis**: Find best config across multiple prompts
- **Team Collaboration**: Multiple team members ranking, real-time updates
- **Machine Learning**: Train on human rankings to improve AI evaluation
- **Custom Criteria**: Users define their own evaluation criteria
- **Prompt Templates**: Save and reuse ranking configurations
- **Export & Reports**: Generate PDF reports of recommendations
- **API Access**: External systems query recommendations
- **Slack/Email Notifications**: Alert when new evaluations complete

---

## Appendix

### Example Review Prompt Templates

#### Code Quality Reviewer
```
You are an expert software engineer evaluating code quality.

ORIGINAL PROMPT: {original_prompt}
CONFIGURATION: {config_name}
OUTPUT:
{result}

Evaluate this code on:
1. CORRECTNESS: Does it solve the problem correctly?
2. EFFICIENCY: Is the algorithm/approach optimal?
3. READABILITY: Is the code clean and well-structured?
4. BEST PRACTICES: Does it follow language conventions?

Return JSON:
{
  "criteria_scores": {"correctness": 9.0, "efficiency": 8.5, ...},
  "overall_score": 8.7,
  "justification": "...",
  "key_strengths": ["...", "..."],
  "key_weaknesses": ["...", "..."]
}
```

#### Creative Writing Judge
```
You are a literary critic evaluating creative writing.

ORIGINAL PROMPT: {original_prompt}
CONFIGURATION: {config_name}
OUTPUT:
{result}

Evaluate on:
1. CREATIVITY: Originality and imagination
2. COHERENCE: Story structure and flow
3. ENGAGEMENT: How compelling and interesting
4. LANGUAGE: Quality of prose and style

Return JSON with scores 1-10 for each criterion.
```

#### Business Analysis Evaluator
```
You are a business consultant evaluating strategic analysis.

ORIGINAL PROMPT: {original_prompt}
CONFIGURATION: {config_name}
OUTPUT:
{result}

Evaluate on:
1. INSIGHT: Depth and quality of analysis
2. ACTIONABILITY: Practical, implementable recommendations
3. DATA-DRIVEN: Use of evidence and logic
4. CLARITY: Clear communication of ideas

Return JSON with scores 1-10 for each criterion.
```

---

**End of Specification**

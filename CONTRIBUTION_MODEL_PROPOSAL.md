# Kingdom 3584 - Player Contribution Model Proposal

## Executive Summary

Based on extensive research into Rise of Kingdoms DKP systems, mobile strategy games, and academic research on fair team-based scoring, I propose a **multi-tiered contribution model** that fairly represents each player's value to the kingdom during KvK.

---

## Research Findings Summary

### Industry Standards

**Rise of Kingdoms DKP Formula (Community Standard):**
```
DKP = (T4 kills × 10) + (T5 kills × 30) + (Deaths × 80)
```

**Key Insights:**
- Deaths are weighted POSITIVELY (80 points) - rewards active combat participation
- T5 kills worth 3x T4 kills (reflects resource cost and difficulty)
- T1-T3 kills ignored (too easy to farm)
- Power-normalized expectations prevent whale domination
- Diminishing returns above 40M points (prevents one player getting 50% of rewards)

**Game Design Principle:**
> "Not all players contribute equally, but fair systems give multiple ways to succeed and prevent whales from completely dominating rewards."

---

## Proposed Contribution Model

### Model 1: **Weighted Combat Score (DKP-Based)** ⭐ RECOMMENDED

This is the most battle-tested model used by successful RoK kingdoms.

#### Formula:
```
Combat Score = (T4 Kills × 10) + (T5 Kills × 30) + (Deaths × 80)

Contribution % = (Player Combat Score / Total Kingdom Combat Score) × 100
```

#### Why This Works:

**T4 Weight = 10 points**
- Standard tier, moderate difficulty to kill
- Most common troop type in battles
- Base value for comparison

**T5 Weight = 30 points (3x T4)**
- Requires months of research
- Costs 3-5x more resources than T4
- Significantly harder to kill
- Killing T5 shows tactical skill

**Deaths Weight = 80 points (8x T4)**
- Rewards players who "take one for the team"
- Shows active combat participation
- Prevents players from only sniping easy kills
- Recognizes sacrifice for kingdom goals

#### Example Calculations:

**Example Kingdom Stats:**
```
Total Kingdom:
- T4 Kills: 10,000,000
- T5 Kills: 5,000,000
- Total Deaths: 3,000,000

Total Combat Score = (10M × 10) + (5M × 30) + (3M × 80)
                   = 100M + 150M + 240M
                   = 490,000,000 points
```

**Player Examples:**

**Player A - "The Whale" (Big Spender, High Power)**
```
Governor: ˢᵖBigWhale
Power: 200M
Stats:
- T4 Kills: 500,000
- T5 Kills: 300,000
- Deaths: 150,000

Combat Score = (500k × 10) + (300k × 30) + (150k × 80)
             = 5M + 9M + 12M
             = 26,000,000 points

Contribution % = 26M / 490M × 100 = 5.31%
```

**Player B - "The Warrior" (Mid-Spender, Very Active)**
```
Governor: ⚔️WarriorKing
Power: 80M
Stats:
- T4 Kills: 300,000
- T5 Kills: 100,000
- Deaths: 200,000

Combat Score = (300k × 10) + (100k × 30) + (200k × 80)
             = 3M + 3M + 16M
             = 22,000,000 points

Contribution % = 22M / 490M × 100 = 4.49%
```

**Player C - "The F2P Hero" (Free-to-Play, Strategic)**
```
Governor: F2PHero
Power: 35M
Stats:
- T4 Kills: 150,000
- T5 Kills: 20,000
- Deaths: 80,000

Combat Score = (150k × 10) + (20k × 30) + (80k × 80)
             = 1.5M + 0.6M + 6.4M
             = 8,500,000 points

Contribution % = 8.5M / 490M × 100 = 1.73%
```

**Player D - "The Sniper" (Kill Stealer, Avoids Combat)**
```
Governor: EasySniper
Power: 60M
Stats:
- T4 Kills: 200,000
- T5 Kills: 50,000
- Deaths: 10,000

Combat Score = (200k × 10) + (50k × 30) + (10k × 80)
             = 2M + 1.5M + 0.8M
             = 4,300,000 points

Contribution % = 4.3M / 490M × 100 = 0.88%
```

#### Analysis:

✅ **Player B** (Warrior) gets 4.49% despite having 2.5x less power than Player A
- Shows the model rewards ACTIVE participation over raw power
- 200k deaths shows willingness to fight hard battles

✅ **Player C** (F2P) gets 1.73% with only 35M power
- Proves F2P players can contribute meaningfully
- 80k deaths shows commitment despite smaller army

❌ **Player D** (Sniper) gets only 0.88% despite 60M power
- Low deaths (10k) shows avoiding real combat
- Model discourages kill-stealing behavior

---

### Model 2: **Power-Normalized Performance Score**

This model shows who "performs above their weight class."

#### Formula:
```
Expected Score = Power × 0.0003  (30% of power divided by 1000)
Performance Ratio = Actual Combat Score / Expected Score

Contribution % = (Player Performance Ratio / Sum of All Ratios) × 100
```

#### Same Players, Different View:

**Player A - The Whale**
```
Expected = 200M × 0.0003 = 60,000
Actual = 26,000,000
Performance Ratio = 26M / 60k = 433.33
```

**Player B - The Warrior**
```
Expected = 80M × 0.0003 = 24,000
Actual = 22,000,000
Performance Ratio = 22M / 24k = 916.67 ⭐ HIGHEST
```

**Player C - F2P Hero**
```
Expected = 35M × 0.0003 = 10,500
Actual = 8,500,000
Performance Ratio = 8.5M / 10.5k = 809.52
```

**Player D - Sniper**
```
Expected = 60M × 0.0003 = 18,000
Actual = 4,300,000
Performance Ratio = 4.3M / 18k = 238.89
```

**Total Performance Ratios = 433.33 + 916.67 + 809.52 + 238.89 = 2,398.41**

**Normalized Contributions:**
- Player A: 433.33 / 2398.41 = 18.06%
- Player B: 916.67 / 2398.41 = 38.22% ⭐
- Player C: 809.52 / 2398.41 = 33.75%
- Player D: 238.89 / 2398.41 = 9.96%

#### Analysis:

This model shows **relative performance** rather than absolute contribution:
- Player B is "performing the best" relative to their power
- Player C (F2P) gets recognized for high effort
- Player A's massive power is normalized
- Player D is clearly underperforming

**Use Case:** Best for internal kingdom "MVP" awards or identifying who's punching above their weight.

---

### Model 3: **Multi-Bracket Leaderboard** ⭐ FAIREST

Divide players into power brackets and calculate contribution % within each bracket.

#### Power Brackets:
```
Bracket 1: 0-50M Power    (F2P, Low Spenders)
Bracket 2: 50-100M Power  (Mid Spenders)
Bracket 3: 100-150M Power (High Spenders)
Bracket 4: 150M+ Power    (Whales)
```

#### Example (Bracket 1: 0-50M Power):

**Players in Bracket:**
- Player C (F2P Hero): 8,500,000 points
- Player E: 5,000,000 points
- Player F: 3,200,000 points
- Player G: 2,100,000 points

**Bracket Total = 18,800,000 points**

**Bracket 1 Contributions:**
- Player C: 8.5M / 18.8M = **45.21%** of their bracket
- Player E: 5M / 18.8M = 26.60%
- Player F: 3.2M / 18.8M = 17.02%
- Player G: 2.1M / 18.8M = 11.17%

**Overall Kingdom Contribution:**
If Bracket 1 represents 15% of total kingdom score:
- Player C Overall: 45.21% × 15% = **6.78%** of kingdom

#### Analysis:

✅ Player C can be #1 in their bracket even though overall they're ranked lower
✅ Encourages competition at ALL power levels
✅ Prevents F2P players from feeling hopeless
✅ Each bracket has meaningful rankings

---

## Recommended Implementation

### Primary System: **Model 1 (Weighted Combat Score)**

**Use for:**
- Main leaderboard ranking
- Overall contribution percentages
- Reward distribution calculations
- Public displays

**Advantages:**
- Industry-proven (used by successful RoK kingdoms)
- Easy to understand
- Rewards the right behaviors
- Balanced between power and activity

### Secondary System: **Model 3 (Multi-Bracket)**

**Use for:**
- Power-tier leaderboards
- Internal motivation
- Showing F2P players they matter
- Identifying MVPs in each tier

**Advantages:**
- Keeps all players engaged
- Fair competition within peer groups
- Multiple "winners" instead of just top 10

### Tertiary System: **Model 2 (Performance Ratio)**

**Use for:**
- "Efficiency" or "MVP" special rankings
- Identifying underperformers for their power level
- Coaching and feedback
- Special recognition awards

**Advantages:**
- Shows who's performing above/below expectations
- Useful for leadership decisions
- Identifies active vs inactive players

---

## Implementation Formulas

### Core Contribution Score (Python):

```python
def calculate_combat_score(player):
    """
    DKP-based combat score (Model 1)
    """
    t4_weight = 10
    t5_weight = 30
    death_weight = 80

    score = (
        player.t4_kills * t4_weight +
        player.t5_kills * t5_weight +
        player.deads * death_weight
    )

    return score

def calculate_contribution_percentage(player, kingdom_total_score):
    """
    Player's % contribution to kingdom
    """
    player_score = calculate_combat_score(player)

    if kingdom_total_score == 0:
        return 0.0

    contribution_pct = (player_score / kingdom_total_score) * 100
    return round(contribution_pct, 2)

def calculate_performance_ratio(player):
    """
    How well player performs relative to their power (Model 2)
    """
    expected_score = player.power * 0.0003  # 30% of power / 1000

    if expected_score == 0:
        return 0.0

    actual_score = calculate_combat_score(player)
    ratio = actual_score / expected_score

    return round(ratio, 2)

def get_power_bracket(power):
    """
    Classify player into power bracket (Model 3)
    """
    if power < 50_000_000:
        return "0-50M"
    elif power < 100_000_000:
        return "50-100M"
    elif power < 150_000_000:
        return "100-150M"
    else:
        return "150M+"

def calculate_bracket_contribution(player, bracket_players):
    """
    Player's % contribution within their power bracket
    """
    player_score = calculate_combat_score(player)
    bracket_total = sum(calculate_combat_score(p) for p in bracket_players)

    if bracket_total == 0:
        return 0.0

    bracket_pct = (player_score / bracket_total) * 100
    return round(bracket_pct, 2)
```

### Display Example (Discord Bot):

```
🏆 Top Contributors (Overall)

1. 👑 ˢᵖBigWhale (200M) - 5.31%
   Combat Score: 26.0M | Performance: 433x

2. ⚔️ WarriorKing (80M) - 4.49%
   Combat Score: 22.0M | Performance: 917x ⭐ MVP

3. 🛡️ F2PHero (35M) - 1.73%
   Combat Score: 8.5M | Performance: 810x

━━━━━━━━━━━━━━━━━━━━━━━━
💡 Performance Rating Legend:
⭐ 800+ = Exceptional
🔥 500-799 = Excellent
✅ 300-499 = Good
⚠️ <300 = Underperforming

📊 Bracket Leaders:
0-50M: F2PHero (45.2% of bracket)
50-100M: WarriorKing (62.3% of bracket)
100-150M: TankMaster (38.1% of bracket)
150M+: BigWhale (41.7% of bracket)
```

---

## Additional Metrics (Optional Enhancements)

### Efficiency Score (K/D Ratio):
```python
def calculate_efficiency(player):
    """
    Kill/Death ratio based on power (not count)
    """
    if player.deads == 0:
        return 0.0  # No combat participation

    kd_ratio = player.kill_points / player.deads
    return round(kd_ratio, 2)

# Benchmarks:
# > 2.0 = Elite (more than double kills vs deaths)
# 1.2-2.0 = Excellent
# 0.8-1.2 = Average
# < 0.8 = Poor (dying more than killing)
```

### Activity Score (Consistency):
```python
def calculate_activity_score(upload_history):
    """
    Rewards consistent participation across all uploads
    """
    uploads_with_activity = 0
    total_uploads = len(upload_history)

    for upload in upload_history:
        if upload.kill_points_gained > 0 or upload.deads_gained > 0:
            uploads_with_activity += 1

    activity_pct = (uploads_with_activity / total_uploads) * 100
    return round(activity_pct, 2)

# 100% = Active in every upload
# 80-99% = Very active
# 50-79% = Moderately active
# < 50% = Inactive
```

---

## Comparison: All Three Models Side-by-Side

| Player | Power | Kills | Deaths | Model 1 (Absolute %) | Model 2 (Performance %) | Model 3 (Bracket %) |
|--------|-------|-------|--------|---------------------|------------------------|---------------------|
| BigWhale | 200M | 800k | 150k | **5.31%** | 18.06% | 41.7% (150M+ bracket) |
| WarriorKing | 80M | 400k | 200k | **4.49%** | **38.22%** ⭐ | **62.3%** (50-100M) |
| F2PHero | 35M | 170k | 80k | **1.73%** | 33.75% | **45.2%** (0-50M) ⭐ |
| Sniper | 60M | 250k | 10k | **0.88%** | 9.96% | 15.3% (50-100M) |

**Key Insights:**
- **Model 1**: Shows true kingdom impact (BigWhale contributes most)
- **Model 2**: Shows MVP (WarriorKing performing best for their size)
- **Model 3**: Shows bracket winners (F2PHero dominates their tier)

All three tell different but valuable stories!

---

## Final Recommendation

### Implement ALL Three Models:

**1. Default Display: Model 1 (Weighted Combat Score)**
- Main leaderboard
- Primary contribution percentage
- Reward distribution basis

**2. Secondary View: Model 3 (Power Brackets)**
- Separate leaderboards per bracket
- Keeps F2P engaged
- Shows peer comparison

**3. Stats Page: Model 2 (Performance Ratio)**
- "Efficiency Rating" or "Performance Score"
- Internal metric for leaders
- MVP identification

### Discord Bot Commands:
```
/top                  → Model 1 (default)
/top bracket 0-50M    → Model 3 (power bracket)
/mvp                  → Model 2 (performance ratio ranking)
```

### Website Display:
- **Main Leaderboard Tab**: Model 1 with contribution %
- **Power Brackets Tab**: Model 3 with bracket leaders
- **Player Profile**: Shows all three metrics
  - Contribution: 5.31%
  - Performance: 433x
  - Bracket Rank: #2 in 150M+ tier

---

## Questions for You

1. **Do you want deaths to be positive (reward participation) or negative (penalty)?**
   - Research shows positive works better for team morale

2. **Should we cap whale contributions with diminishing returns?**
   - Example: Above 40M score, each additional point counts as 0.75x

3. **Power bracket ranges - do these make sense for your kingdom?**
   - 0-50M, 50-100M, 100-150M, 150M+
   - Can be customized based on your player distribution

4. **Weighting adjustments?**
   - T4: 10, T5: 30, Deaths: 80
   - Want to tweak these?

5. **Should we include T1-T3 kills?**
   - Research suggests NO (too easy to farm)
   - But could add small weights (1, 3, 5)

Let me know which model(s) you prefer and any adjustments needed!

# Judge Neutrality Analysis

## Objective

The neutrality analysis module allows for objectively evaluating the impartiality of each judge during a competition. It automatically detects potential biases by comparing the scores assigned according to several statistical criteria.

This module is a **training and continuous improvement** tool for judges, not a disciplinary tool. It allows each judge to become aware of their unconscious tendencies in order to improve.

---

## Neutrality Score (0-100)

Each judge receives a **global neutrality score** calculated out of 100 points. The higher the score, the more impartial the judge is considered to be.

The score is calculated by subtracting penalties from the perfect score of 100, based on 4 weighted criteria:

| Criterion | Weight | Maximum Penalty |
|-----------|--------|-----------------|
| Club bias | 30% | -30 points |
| Nationality bias | 25% | -25 points |
| Positioning bias | 20% | -20 points |
| Peer concordance | 25% | -25 points |

### Risk Levels

| Score | Level | Meaning |
|-------|-------|---------|
| **80-100** | Low risk (green) | The judge scores consistently and impartially |
| **60-79** | Moderate risk (orange) | Trends detected, to be monitored |
| **0-59** | High risk (red) | Significant biases detected, training recommended |

---

## Criterion 1: Club Bias

### Principle
This criterion compares the average scores a judge gives to practitioners from **their own club** versus practitioners from **other clubs**.

### Calculation
```
Difference = Average(scores for same-club practitioners) - Average(scores for other practitioners)
```

### Detection Thresholds

| Difference (absolute value) | Severity | Interpretation |
|-----------------------------|----------|----------------|
| < 0.3 points | Neutral | No bias detected |
| 0.3 to 0.5 points | Low | Slight favoritism or unfavoritism |
| 0.5 to 0.8 points | Moderate | Significant trend to monitor |
| > 0.8 points | High | Marked bias, corrective action recommended |

### How to Interpret
- **Positive value** (+): the judge tends to score more favorably for practitioners from their club
- **Negative value** (-): the judge tends to be harsher with practitioners from their club (overcompensation)
- Both situations are biases that need correction

### Penalty on Global Score

| Severity | Penalty |
|----------|---------|
| Neutral | 0 points |
| Low | -10 points |
| Moderate | -20 points |
| High | -30 points |

---

## Criterion 2: Nationality Bias

### Principle
This criterion compares the average scores given to practitioners of **the same nationality** as the judge versus practitioners of **other nationalities**.

### Calculation
```
Difference = Average(scores for same nationality) - Average(scores for other nationalities)
```

### Detection Thresholds

| Difference (absolute value) | Severity | Interpretation |
|-----------------------------|----------|----------------|
| < 0.2 points | Neutral | No bias detected |
| 0.2 to 0.4 points | Low | Slight favoritism or unfavoritism |
| 0.4 to 0.6 points | Moderate | Significant trend |
| > 0.6 points | High | Marked bias |

### How to Interpret
- **Stricter thresholds** than club bias, as nationality should have no influence on technical scoring
- **Positive value**: favoritism toward own nationality
- **Negative value**: excessive severity toward own nationality

### Penalty on Global Score

| Severity | Penalty |
|----------|---------|
| Neutral | 0 points |
| Low | -8 points |
| Moderate | -16 points |
| High | -25 points |

---

## Criterion 3: Positioning Bias

### Principle
This criterion compares a judge's **overall average scores** to the **average of all judges** in the competition. It detects judges who are systematically too generous or too strict.

### Calculation
```
Difference = Average(all judge's scores) - Average(all scores from all judges)
```

### Detection Thresholds

| Difference (absolute value) | Severity | Interpretation |
|-----------------------------|----------|----------------|
| < 0.2 points | Neutral | Within average, well-calibrated scoring |
| 0.2 to 0.4 points | Low | Slightly generous or strict |
| 0.4 to 0.6 points | Moderate | Notably generous or strict |
| > 0.6 points | High | Very generous or very strict |

### How to Interpret
- **Positive value** (+): the judge systematically scores above average (generous)
- **Negative value** (-): the judge systematically scores below average (strict)
- A good judge falls within the neutral range (< 0.2 point deviation)

### Penalty on Global Score

| Severity | Penalty |
|----------|---------|
| Neutral | 0 points |
| Low | -5 points |
| Moderate | -12 points |
| High | -20 points |

---

## Criterion 4: Peer Concordance

### Principle
This criterion measures how much a judge's scores **agree with those of other judges** for the same performances. A judge whose scores constantly diverge from their colleagues may have a calibration or bias issue.

### Calculation
For each performance scored by the judge:
```
Others' average = Average(other judges' scores for this performance)
Deviation = |Judge's score - Others' average|
Individual concordance = max(0, 100 - (Deviation × 20))
```

The **global concordance score** is the average of all individual concordances.

### Interpretation

| Concordance | Meaning |
|-------------|---------|
| **90-100%** | Excellent concordance, very aligned scoring |
| **75-89%** | Good concordance |
| **60-74%** | Acceptable concordance but needs improvement |
| **< 60%** | Low concordance, **alert generated** |

### Impact on Global Score
Concordance influences the neutrality score via a bonus/penalty:
```
Adjustment = (Concordance - 50) / 2
```
- 100% concordance: +25 point bonus
- 50% concordance: neither bonus nor penalty
- 0% concordance: -25 point penalty

### Conditions
- A minimum of **3 performances** scored is required for the calculation to be meaningful
- Only active (non-training) scores are taken into account

---

## Alert System

Alerts are automatically generated in the following cases:

| Condition | Alert |
|-----------|-------|
| Moderate or high club bias | "Club bias detected" with the deviation value |
| Moderate or high nationality bias | "Nationality bias detected" with the deviation value |
| High positioning only | "Extreme position" with deviation from average |
| Concordance < 60% | "Low concordance with other judges" |

Alerts are visible on each judge's detailed profile in the analysis interface.

---

## Most Impartial Judges Podium

At the end of the analysis, a **podium** highlights the 3 judges who achieved the best neutrality scores:

- **1st place (Gold)**: Highest neutrality score
- **2nd place (Silver)**: Second best score
- **3rd place (Bronze)**: Third best score

This ranking rewards impartiality and encourages all judges to improve.

---

## Recommendations for Judges

### How to Improve Your Neutrality Score

1. **Club bias**: Be particularly attentive when scoring a practitioner from your own club. Apply the same technical criteria as for others.

2. **Nationality bias**: Focus solely on technique and execution. The practitioner's nationality should not influence your evaluation.

3. **Positioning**: Calibrate your scores by aligning with defined criteria. Neither too generous nor too strict. When in doubt, refer to the official scoring scale.

4. **Concordance**: If your scores often diverge from those of your colleagues, it may indicate a misunderstanding of the criteria. Participate in calibration sessions.

### Best Practices

- Score each performance independently, without looking at other judges' scores
- Use the full range of the scoring scale
- Do not modify your scores after seeing those of others
- Take the time to evaluate each criterion separately
- In case of fatigue, take a break to maintain your concentration

---

## Access and Confidentiality

- The neutrality analysis is accessible to **competition organizers** and **federation administrators**
- Each judge can view **their own results**
- Data is calculated in **real time** from existing scores (no neutrality data is permanently stored)
- The analysis requires a sufficient number of scores to be reliable (minimum 3 performances for concordance)

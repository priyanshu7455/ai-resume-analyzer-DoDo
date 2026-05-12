"""
utils/analyzer.py
-----------------
Sends resume text to Azure OpenAI and parses the structured JSON response.
Every step is commented for beginners.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv          # Reads our .env file automatically

# Load environment variables from .env the moment this module is imported
load_dotenv()


# ---------------------------------------------------------------------------
# 1.  Build the Azure OpenAI client once (reused across all calls)
# ---------------------------------------------------------------------------

def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "Missing GROQ_API_KEY in .env file."
        )

    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# 2.  The prompt that tells the AI *exactly* what to return
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an expert resume coach and HR specialist with 15+ years of experience
reviewing resumes across tech, finance, healthcare, and creative industries.

Analyze the provided resume text and return ONLY a valid JSON object — no
markdown fences, no extra prose — with this exact structure:

{
  "score": <integer 0-100>,
  "score_breakdown": {
    "formatting":    <0-20>,
    "skills":        <0-20>,
    "experience":    <0-20>,
    "achievements":  <0-20>,
    "keywords":      <0-20>
  },
  "summary": "<2-3 sentence overall assessment>",
  "detected_skills": ["skill1", "skill2", ...],
  "experience_highlights": [
    {"title": "...", "company": "...", "duration": "...", "impact": "..."},
    ...
  ],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "strengths": ["strength1", "strength2", ...],
  "improvement_suggestions": [
    {"priority": "High|Medium|Low", "category": "...", "suggestion": "..."},
    ...
  ],
  "career_recommendations": [
    {"role": "...", "reason": "...", "match_percent": <0-100>},
    ...
  ],
  "ats_tips": ["tip1", "tip2", ...]
}

Rules:
- score_breakdown sub-scores must sum to exactly the overall score.
- Return at least 5 detected_skills, 5 missing_keywords, 3 strengths,
  5 improvement_suggestions, 3 career_recommendations, and 3 ats_tips.
- Be honest but constructive — this feedback helps real people.
- Do NOT wrap the JSON in markdown code fences.
"""


# ---------------------------------------------------------------------------
# 3.  The main analysis function
# ---------------------------------------------------------------------------

def analyze_resume(resume_text: str, job_role: str = "") -> dict:
    """
    Send resume text to Azure OpenAI and get back a structured analysis.

    Args:
        resume_text: Plain-text content extracted from the PDF.
        job_role:    Optional target job role to tailor keyword suggestions.

    Returns:
        Python dict matching the JSON schema defined in SYSTEM_PROMPT.

    Raises:
        ValueError:  If the AI returns malformed JSON.
        RuntimeError: If the API call fails.
    """
    client = get_client()
    

    # Build the user message — include job role context if provided
    user_message = f"Resume Text:\n\n{resume_text}"
    if job_role.strip():
        user_message += f"\n\nTarget Job Role: {job_role.strip()}"

    try:
        # Make the API call ─────────────────────────────────────────────────
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,    # Lower = more deterministic / consistent
            max_tokens=2500,    # Enough for a detailed JSON response
        )

        # Extract the raw text from the response ────────────────────────────
        raw_text = response.choices[0].message.content.strip()

        # Parse JSON ─────────────────────────────────────────────────────────
        result = parse_json_response(raw_text)
        return result

    except EnvironmentError:
        raise   # Re-raise config errors as-is
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e


# ---------------------------------------------------------------------------
# 4.  Robust JSON parser — handles common AI quirks
# ---------------------------------------------------------------------------

def parse_json_response(raw: str) -> dict:
    """
    Parse the AI's text response into a Python dict.

    The AI sometimes wraps JSON in markdown fences even when told not to.
    This function strips those before parsing.

    Args:
        raw: Raw string from the API response.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If valid JSON cannot be found.
    """
    # Strip markdown code fences if present  (```json ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Last resort: try to find the first { ... } block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"AI returned invalid JSON. Raw response:\n{raw[:500]}"
        ) from e


# ---------------------------------------------------------------------------
# 5.  Helpers used by app.py for display logic
# ---------------------------------------------------------------------------

def get_score_color(score: int) -> str:
    """Return a hex color representing the score quality."""
    if score >= 80:
        return "#22c55e"   # Green  — excellent
    elif score >= 60:
        return "#f59e0b"   # Amber  — good
    elif score >= 40:
        return "#f97316"   # Orange — needs work
    else:
        return "#ef4444"   # Red    — poor


def get_score_label(score: int) -> str:
    """Return a human-readable label for the score band."""
    if score >= 80:
        return "Excellent 🌟"
    elif score >= 60:
        return "Good 👍"
    elif score >= 40:
        return "Needs Improvement 🔧"
    else:
        return "Poor — Significant Revision Needed ⚠️"


def get_priority_color(priority: str) -> str:
    """Return badge color for suggestion priority levels."""
    colors = {
        "High":   "#ef4444",
        "Medium": "#f59e0b",
        "Low":    "#22c55e",
    }
    return colors.get(priority, "#94a3b8")

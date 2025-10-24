"""
Scoring Engine for Candidate Evaluation
Scores new candidates against job requirements and patterns from good hires.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv


class CandidateScorer:
    """Score candidates based on JD requirements and good hire patterns."""

    def __init__(self,
                 jd_file: str = "data/processed/jd_requirements.json",
                 profiles_file: str = "data/processed/structured_profiles.json"):
        """
        Initialize the scorer with JD requirements and good hire profiles.

        Args:
            jd_file: Path to job description requirements JSON
            profiles_file: Path to structured profiles JSON
        """
        load_dotenv()

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-nano"

        # Load data
        self.jd_requirements = self._load_json(jd_file)
        self.good_hires = self._load_json(profiles_file)

        # Calculate baseline patterns from good hires
        self.baseline_patterns = self._calculate_baseline_patterns()

    def _load_json(self, file_path: str) -> Dict:
        """Load JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _calculate_baseline_patterns(self) -> Dict:
        """Calculate patterns from good hires."""
        valid_profiles = [p for p in self.good_hires.values() if "error" not in p]

        if not valid_profiles:
            raise ValueError("No valid profiles found in good hires data")

        # Calculate statistics
        total = len(valid_profiles)

        # Experience stats
        experiences = [p.get("years_of_experience", 0) for p in valid_profiles]
        avg_experience = sum(experiences) / total

        # Education stats
        mba_count = sum(1 for p in valid_profiles if p.get("has_mba", False))
        eng_count = sum(1 for p in valid_profiles if p.get("has_engineering_degree", False))
        tech_count = sum(1 for p in valid_profiles if p.get("has_tech_background", False))

        # Skills frequency
        all_skills = []
        for p in valid_profiles:
            skills = p.get("skills", [])
            if isinstance(skills, list):
                all_skills.extend(skills)

        skill_frequency = Counter(all_skills)

        return {
            "total_profiles": total,
            "avg_experience": avg_experience,
            "pct_with_mba": (mba_count / total) * 100,
            "pct_with_engineering": (eng_count / total) * 100,
            "pct_with_tech_background": (tech_count / total) * 100,
            "common_skills": skill_frequency.most_common(20),
            "experience_range": (min(experiences), max(experiences))
        }

    def _semantic_skill_match(self, candidate_skills: List[str], target_skills: List[str]) -> float:
        """
        Use OpenAI to check semantic similarity of skills.
        Returns match score 0-1.
        """
        if not candidate_skills or not target_skills:
            return 0.0

        prompt = f"""Compare these two skill lists and return a similarity score from 0 to 1.

Candidate skills: {', '.join(candidate_skills[:15])}
Target skills: {', '.join(target_skills[:15])}

Consider semantic similarity (e.g., "Python programming" matches "Python", "stakeholder management" matches "stakeholder communication").

Return ONLY a number between 0 and 1."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skill matching expert. Return only a decimal number."},
                    {"role": "user", "content": prompt}
                ]
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(0.0, min(1.0, score))

        except Exception as e:
            print(f"Warning: Semantic matching failed, using fallback: {e}")
            # Fallback to exact matching
            matches = sum(1 for skill in candidate_skills if any(skill.lower() in ts.lower() or ts.lower() in skill.lower() for ts in target_skills))
            return matches / len(target_skills) if target_skills else 0.0

    def _score_jd_match(self, candidate: Dict) -> Tuple[float, Dict, List[str]]:
        """
        Score candidate against job description requirements.
        Returns (score, breakdown, explanations).
        """
        breakdown = {}
        explanations = []

        # 1. Qualifications match (25%)
        has_mba = candidate.get("has_mba", False)
        has_eng = candidate.get("has_engineering_degree", False)

        qual_score = 0
        if has_mba and has_eng:
            qual_score = 1.0
            explanations.append("✓ Excellent: Has both MBA and Engineering degree (meets all qualifications)")
        elif has_mba or has_eng:
            qual_score = 0.7
            qual = "MBA" if has_mba else "Engineering degree"
            explanations.append(f"✓ Good: Has {qual} (partial qualification match)")
        else:
            qual_score = 0.3
            explanations.append("⚠ Weakness: Missing MBA and Engineering degree from requirements")

        breakdown["qualifications"] = qual_score * 25

        # 2. Experience level (20%)
        candidate_exp = candidate.get("years_of_experience", 0)
        required_exp = self.jd_requirements.get("required_experience", {}).get("years", 5)

        exp_diff = abs(candidate_exp - required_exp)
        if exp_diff <= 1:
            exp_score = 1.0
            explanations.append(f"✓ Excellent: {candidate_exp} years experience perfectly matches requirement")
        elif exp_diff <= 3:
            exp_score = 0.8
            explanations.append(f"✓ Good: {candidate_exp} years experience close to {required_exp} year requirement")
        elif candidate_exp >= required_exp:
            exp_score = 0.7
            explanations.append(f"✓ Acceptable: {candidate_exp} years experience exceeds minimum")
        else:
            exp_score = 0.4
            explanations.append(f"⚠ Below requirement: {candidate_exp} years vs {required_exp} years required")

        breakdown["experience"] = exp_score * 20

        # 3. Must-have skills (30%)
        must_have_skills = self.jd_requirements.get("must_have_skills", [])
        candidate_skills = candidate.get("skills", [])

        if must_have_skills:
            skills_match = self._semantic_skill_match(candidate_skills, must_have_skills)
            breakdown["must_have_skills"] = skills_match * 30
            matched_count = int(skills_match * len(must_have_skills))
            explanations.append(f"Skills: {matched_count}/{len(must_have_skills)} must-have skills matched ({skills_match*100:.0f}%)")
        else:
            breakdown["must_have_skills"] = 15

        # 4. Nice-to-have skills (15%)
        nice_skills = self.jd_requirements.get("nice_to_have_skills", [])
        if nice_skills:
            nice_match = self._semantic_skill_match(candidate_skills, nice_skills)
            breakdown["nice_to_have_skills"] = nice_match * 15
        else:
            breakdown["nice_to_have_skills"] = 7.5

        # 5. Domain expertise (10%)
        required_domains = self.jd_requirements.get("required_experience", {}).get("domains", [])
        candidate_domains = candidate.get("domain_expertise", [])

        if required_domains:
            domain_match = self._semantic_skill_match(candidate_domains, required_domains)
            breakdown["domain_expertise"] = domain_match * 10
        else:
            breakdown["domain_expertise"] = 5

        total_score = sum(breakdown.values())
        return total_score, breakdown, explanations

    def _score_pattern_match(self, candidate: Dict) -> Tuple[float, Dict, List[str]]:
        """
        Score candidate against patterns from good hires.
        Returns (score, breakdown, explanations).
        """
        breakdown = {}
        explanations = []
        patterns = self.baseline_patterns

        # 1. Experience similarity (25%)
        candidate_exp = candidate.get("years_of_experience", 0)
        avg_exp = patterns["avg_experience"]
        exp_diff = abs(candidate_exp - avg_exp)

        if exp_diff <= 2:
            exp_score = 1.0
            explanations.append(f"✓ Strong match: {candidate_exp} years aligns with good hires average of {avg_exp:.1f} years")
        elif exp_diff <= 4:
            exp_score = 0.75
            explanations.append(f"✓ Good match: {candidate_exp} years close to good hires average of {avg_exp:.1f} years")
        else:
            exp_score = 0.5
            explanations.append(f"⚠ Different from pattern: {candidate_exp} years vs {avg_exp:.1f} years average")

        breakdown["experience_similarity"] = exp_score * 25

        # 2. Skills overlap (30%)
        common_skills = [skill for skill, _ in patterns["common_skills"][:10]]
        candidate_skills = candidate.get("skills", [])

        skill_overlap = sum(1 for cs in candidate_skills if any(cs.lower() in gs.lower() or gs.lower() in cs.lower() for gs in common_skills))
        overlap_score = skill_overlap / len(common_skills) if common_skills else 0.5

        breakdown["skills_overlap"] = overlap_score * 30
        explanations.append(f"Skills overlap: {skill_overlap}/{len(common_skills)} common skills from good hires")

        # 3. Education pattern (20%)
        has_mba = candidate.get("has_mba", False)
        has_eng = candidate.get("has_engineering_degree", False)

        edu_score = 0
        if has_mba:
            edu_score += 0.5
            explanations.append(f"✓ Has MBA (found in {patterns['pct_with_mba']:.0f}% of good hires)")
        if has_eng:
            edu_score += 0.5
            explanations.append(f"✓ Has Engineering degree (found in {patterns['pct_with_engineering']:.0f}% of good hires)")

        breakdown["education_pattern"] = edu_score * 20

        # 4. Tech background (15%)
        has_tech = candidate.get("has_tech_background", False)
        tech_score = 1.0 if has_tech else 0.3

        if has_tech:
            explanations.append(f"✓ Tech background matches {patterns['pct_with_tech_background']:.0f}% of good hires")
        else:
            explanations.append(f"⚠ No tech background (found in {patterns['pct_with_tech_background']:.0f}% of good hires)")

        breakdown["tech_background"] = tech_score * 15

        # 5. Career progression (10%)
        # Simple heuristic: check if experience progresses logically
        current_role = candidate.get("current_role", "").lower()
        progression_score = 0.7  # Default moderate score

        if "senior" in current_role or "lead" in current_role or "principal" in current_role:
            if candidate_exp >= 8:
                progression_score = 1.0
            else:
                progression_score = 0.6

        breakdown["career_progression"] = progression_score * 10

        total_score = sum(breakdown.values())
        return total_score, breakdown, explanations

    def score_candidate(self, candidate: Dict) -> Dict:
        """
        Score a candidate profile.

        Args:
            candidate: Structured candidate profile dictionary

        Returns:
            Dictionary with scores and explanations
        """
        # Calculate component scores
        jd_score, jd_breakdown, jd_explanations = self._score_jd_match(candidate)
        pattern_score, pattern_breakdown, pattern_explanations = self._score_pattern_match(candidate)

        # Weighted overall score (JD: 40%, Pattern: 60%)
        overall_score = (jd_score * 0.4) + (pattern_score * 0.6)

        # Determine recommendation
        if overall_score >= 75:
            recommendation = "Strong Candidate"
            comparison = "Above average compared to good hires"
        elif overall_score >= 60:
            recommendation = "Good Candidate"
            comparison = "Comparable to good hires"
        elif overall_score >= 45:
            recommendation = "Moderate Candidate"
            comparison = "Below average compared to good hires"
        else:
            recommendation = "Weak Candidate"
            comparison = "Significantly below good hire pattern"

        # Separate strengths and weaknesses
        all_explanations = jd_explanations + pattern_explanations
        strengths = [e for e in all_explanations if e.startswith("✓")]
        weaknesses = [e for e in all_explanations if e.startswith("⚠")]

        return {
            "candidate_name": candidate.get("name", "Unknown"),
            "overall_score": round(overall_score, 1),
            "recommendation": recommendation,
            "jd_match_score": round(jd_score, 1),
            "pattern_match_score": round(pattern_score, 1),
            "detailed_breakdown": {
                "jd_components": {k: round(v, 1) for k, v in jd_breakdown.items()},
                "pattern_components": {k: round(v, 1) for k, v in pattern_breakdown.items()}
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "comparison_to_good_hires": comparison,
            "baseline_stats": {
                "good_hires_avg_experience": round(self.baseline_patterns["avg_experience"], 1),
                "good_hires_with_mba": f"{self.baseline_patterns['pct_with_mba']:.0f}%",
                "good_hires_with_engineering": f"{self.baseline_patterns['pct_with_engineering']:.0f}%"
            }
        }


def main():
    """Test the scoring engine."""
    scorer = CandidateScorer()
    print(f"Scoring engine initialized with {scorer.baseline_patterns['total_profiles']} good hires")
    print(f"Average experience: {scorer.baseline_patterns['avg_experience']:.1f} years")


if __name__ == "__main__":
    main()

"""
Test Scoring System
Tests the scoring engine by evaluating existing good hire profiles.
"""

import json
from pathlib import Path
from scoring_engine import CandidateScorer


def test_scoring_system():
    """Test scoring system with existing profiles."""
    print("=" * 70)
    print(" " * 20 + "SCORING SYSTEM TEST")
    print("=" * 70)
    print()

    # Initialize scorer
    print("Initializing scoring engine...")
    scorer = CandidateScorer()
    print(f"✓ Loaded {scorer.baseline_patterns['total_profiles']} good hire profiles")
    print(f"  Average experience: {scorer.baseline_patterns['avg_experience']:.1f} years")
    print(f"  With MBA: {scorer.baseline_patterns['pct_with_mba']:.0f}%")
    print(f"  With Engineering: {scorer.baseline_patterns['pct_with_engineering']:.0f}%")

    # Load profiles
    profiles_path = Path("data/processed/structured_profiles.json")
    with open(profiles_path, 'r') as f:
        profiles = json.load(f)

    # Test with first 3 profiles from good hires
    print("\n" + "=" * 70)
    print("Testing with 3 sample profiles from good hires:")
    print("=" * 70)

    test_profiles = list(profiles.items())[:3]

    results = []

    for idx, (profile_id, profile) in enumerate(test_profiles, 1):
        print(f"\n--- Profile {idx}: {profile.get('name', 'Unknown')} ---")

        # Score the candidate
        evaluation = scorer.score_candidate(profile)

        print(f"Overall Score: {evaluation['overall_score']}/100")
        print(f"Recommendation: {evaluation['recommendation']}")
        print(f"JD Match: {evaluation['jd_match_score']}/100")
        print(f"Pattern Match: {evaluation['pattern_match_score']}/100")

        print(f"\nTop Strengths:")
        for strength in evaluation['strengths'][:3]:
            print(f"  {strength}")

        if evaluation['weaknesses']:
            print(f"\nConsiderations:")
            for weakness in evaluation['weaknesses'][:2]:
                print(f"  {weakness}")

        results.append({
            "name": evaluation['candidate_name'],
            "score": evaluation['overall_score'],
            "recommendation": evaluation['recommendation']
        })

    # Summary statistics
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    scores = [r['score'] for r in results]
    print(f"\nTested {len(results)} profiles from good hires:")
    print(f"  Average Score: {sum(scores) / len(scores):.1f}/100")
    print(f"  Score Range: {min(scores):.1f} - {max(scores):.1f}")

    print(f"\nRecommendation Distribution:")
    recommendations = {}
    for r in results:
        rec = r['recommendation']
        recommendations[rec] = recommendations.get(rec, 0) + 1

    for rec, count in recommendations.items():
        print(f"  {rec}: {count}")

    print("\n" + "=" * 70)
    print("Expected: Scores should generally be 60-85 for good hires")
    print("Note: Existing good hires should score well but may not be perfect")
    print("      due to JD requirements matching and individual variation.")
    print("=" * 70)

    # Save test results
    output_path = Path("outputs/scoring_test_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump({
            "test_date": "2025-10-24",
            "profiles_tested": len(results),
            "results": results,
            "average_score": sum(scores) / len(scores),
            "score_range": {"min": min(scores), "max": max(scores)}
        }, f, indent=2)

    print(f"\n✓ Test results saved to: {output_path}")


def test_scoring_engine_only():
    """Quick test of just the scoring engine initialization."""
    print("=" * 70)
    print(" " * 15 + "QUICK SCORING ENGINE TEST")
    print("=" * 70)
    print()

    try:
        scorer = CandidateScorer()
        print("✓ Scoring engine initialized successfully")
        print(f"\nBaseline patterns loaded:")
        print(f"  Total good hires: {scorer.baseline_patterns['total_profiles']}")
        print(f"  Average experience: {scorer.baseline_patterns['avg_experience']:.1f} years")
        print(f"  Experience range: {scorer.baseline_patterns['experience_range'][0]:.1f} - {scorer.baseline_patterns['experience_range'][1]:.1f} years")
        print(f"  % with MBA: {scorer.baseline_patterns['pct_with_mba']:.1f}%")
        print(f"  % with Engineering: {scorer.baseline_patterns['pct_with_engineering']:.1f}%")
        print(f"  % with Tech background: {scorer.baseline_patterns['pct_with_tech_background']:.1f}%")

        print(f"\nTop 10 common skills from good hires:")
        for idx, (skill, count) in enumerate(scorer.baseline_patterns['common_skills'][:10], 1):
            print(f"  {idx:2d}. {skill:<35s} ({count} candidates)")

        print("\n" + "=" * 70)
        print("✓ Scoring engine is ready to evaluate candidates!")
        print("=" * 70)

    except Exception as e:
        print(f"✗ Failed to initialize scoring engine: {e}")
        raise


def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_scoring_engine_only()
    else:
        test_scoring_system()


if __name__ == "__main__":
    main()

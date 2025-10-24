"""
Main Analysis Runner
Orchestrates the complete resume screening analysis pipeline.
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter

from jd_analyzer import JDAnalyzer
from profile_analyzer import ProfileAnalyzer


class AnalysisRunner:
    """Orchestrate the complete analysis pipeline."""

    def __init__(self):
        """Initialize the analysis runner."""
        self.jd_analyzer = JDAnalyzer()
        self.profile_analyzer = ProfileAnalyzer()
        self.jd_requirements = None
        self.structured_profiles = None

    def run_jd_analysis(self):
        """Run job description analysis."""
        print("\n" + "=" * 60)
        print("STEP 1: Job Description Analysis")
        print("=" * 60)

        try:
            self.jd_requirements = self.jd_analyzer.run()
            print("\n✓ Job description analysis completed successfully")
        except Exception as e:
            print(f"\n✗ Job description analysis failed: {str(e)}")
            raise

    def run_profile_analysis(self):
        """Run profile analysis."""
        print("\n" + "=" * 60)
        print("STEP 2: Profile Analysis")
        print("=" * 60)

        try:
            self.structured_profiles = self.profile_analyzer.run()
            print("\n✓ Profile analysis completed successfully")
        except Exception as e:
            print(f"\n✗ Profile analysis failed: {str(e)}")
            raise

    def calculate_statistics(self) -> Dict:
        """
        Calculate summary statistics from analyzed profiles.

        Returns:
            Dictionary of statistics
        """
        if not self.structured_profiles:
            return {}

        total_profiles = len(self.structured_profiles)

        # Filter out error profiles
        valid_profiles = [
            p for p in self.structured_profiles.values()
            if "error" not in p
        ]

        if not valid_profiles:
            print("\nWarning: No valid profiles to calculate statistics")
            return {
                "total_profiles": total_profiles,
                "valid_profiles": 0
            }

        valid_count = len(valid_profiles)

        # Calculate experience statistics
        experience_values = [
            p.get("years_of_experience", 0)
            for p in valid_profiles
        ]
        avg_experience = sum(experience_values) / valid_count if valid_count > 0 else 0

        # Calculate percentages
        mba_count = sum(1 for p in valid_profiles if p.get("has_mba", False))
        eng_count = sum(1 for p in valid_profiles if p.get("has_engineering_degree", False))
        tech_count = sum(1 for p in valid_profiles if p.get("has_tech_background", False))

        pct_mba = (mba_count / valid_count * 100) if valid_count > 0 else 0
        pct_eng = (eng_count / valid_count * 100) if valid_count > 0 else 0
        pct_tech = (tech_count / valid_count * 100) if valid_count > 0 else 0

        # Collect all skills
        all_skills = []
        for profile in valid_profiles:
            skills = profile.get("skills", [])
            if isinstance(skills, list):
                all_skills.extend(skills)

        # Get top 10 most common skills
        skill_counter = Counter(all_skills)
        top_skills = skill_counter.most_common(10)

        return {
            "total_profiles": total_profiles,
            "valid_profiles": valid_count,
            "error_profiles": total_profiles - valid_count,
            "avg_years_of_experience": round(avg_experience, 1),
            "pct_with_mba": round(pct_mba, 1),
            "pct_with_engineering": round(pct_eng, 1),
            "pct_with_tech_background": round(pct_tech, 1),
            "profiles_with_mba": mba_count,
            "profiles_with_engineering": eng_count,
            "profiles_with_tech_background": tech_count,
            "top_skills": [{"skill": skill, "count": count} for skill, count in top_skills]
        }

    def print_summary_statistics(self):
        """Print summary statistics to console."""
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)

        stats = self.calculate_statistics()

        if not stats:
            print("No statistics available")
            return

        print(f"\nProfile Processing:")
        print(f"  Total profiles: {stats['total_profiles']}")
        print(f"  Successfully processed: {stats['valid_profiles']}")
        print(f"  Errors: {stats['error_profiles']}")

        if stats['valid_profiles'] == 0:
            print("\nNo valid profiles to analyze")
            return

        print(f"\nExperience Overview:")
        print(f"  Average years of experience: {stats['avg_years_of_experience']} years")

        print(f"\nEducation & Background:")
        print(f"  Candidates with MBA: {stats['profiles_with_mba']} ({stats['pct_with_mba']}%)")
        print(f"  Candidates with Engineering degree: {stats['profiles_with_engineering']} ({stats['pct_with_engineering']}%)")
        print(f"  Candidates with tech background: {stats['profiles_with_tech_background']} ({stats['pct_with_tech_background']}%)")

        print(f"\nTop 10 Most Common Skills:")
        for idx, skill_data in enumerate(stats['top_skills'], 1):
            print(f"  {idx:2d}. {skill_data['skill']:<30s} ({skill_data['count']} candidates)")

        # Save statistics to file
        self.save_statistics(stats)

    def save_statistics(self, stats: Dict):
        """
        Save statistics to JSON file.

        Args:
            stats: Statistics dictionary
        """
        output_path = Path("data/processed/analysis_statistics.json")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            print(f"\nStatistics saved to: {output_path}")

        except Exception as e:
            print(f"Warning: Could not save statistics: {str(e)}")

    def run(self):
        """Run the complete analysis pipeline."""
        print("\n" + "=" * 70)
        print(" " * 15 + "RESUME SCREENING ANALYSIS PIPELINE")
        print("=" * 70)

        try:
            # Step 1: Analyze job description
            self.run_jd_analysis()

            # Step 2: Analyze profiles
            self.run_profile_analysis()

            # Step 3: Calculate and display statistics
            self.print_summary_statistics()

            print("\n" + "=" * 70)
            print(" " * 20 + "ANALYSIS COMPLETE!")
            print("=" * 70)
            print("\nOutput files:")
            print("  - data/processed/jd_requirements.json")
            print("  - data/processed/structured_profiles.json")
            print("  - data/processed/analysis_statistics.json")

        except Exception as e:
            print("\n" + "=" * 70)
            print(" " * 20 + "ANALYSIS FAILED")
            print("=" * 70)
            print(f"\nError: {str(e)}")
            exit(1)


def main():
    """Main entry point for the script."""
    runner = AnalysisRunner()
    runner.run()


if __name__ == "__main__":
    main()

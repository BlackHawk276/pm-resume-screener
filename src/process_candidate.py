"""
Process New Candidate
Evaluates a new candidate's LinkedIn PDF against job requirements and good hire patterns.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict
import PyPDF2

from profile_analyzer import ProfileAnalyzer
from scoring_engine import CandidateScorer


class CandidateProcessor:
    """Process and evaluate a new candidate."""

    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the candidate processor.

        Args:
            output_dir: Directory to save evaluation results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.profile_analyzer = ProfileAnalyzer()
        self.scorer = CandidateScorer()

    def extract_pdf_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {str(e)}")

        return text.strip()

    def process_candidate(self, pdf_path: str) -> Dict:
        """
        Process a candidate's LinkedIn PDF.

        Args:
            pdf_path: Path to candidate's LinkedIn PDF

        Returns:
            Evaluation results dictionary
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        print("=" * 70)
        print(" " * 20 + "CANDIDATE EVALUATION")
        print("=" * 70)
        print()

        # Step 1: Extract text from PDF
        print(f"Step 1: Extracting text from {pdf_file.name}...")
        raw_text = self.extract_pdf_text(pdf_file)
        print(f"  ✓ Extracted {len(raw_text)} characters")

        # Step 2: Analyze profile structure
        print(f"\nStep 2: Analyzing profile with AI...")
        profile = self.profile_analyzer.analyze_profile(
            "new_candidate",
            raw_text,
            pdf_file.name
        )

        if "error" in profile:
            raise Exception(f"Profile analysis failed: {profile['error']}")

        print(f"  ✓ Profile analyzed")
        print(f"    Name: {profile.get('name', 'N/A')}")
        print(f"    Experience: {profile.get('years_of_experience', 0)} years")
        print(f"    Current Role: {profile.get('current_role', 'N/A')}")

        # Step 3: Score the candidate
        print(f"\nStep 3: Scoring candidate...")
        evaluation = self.scorer.score_candidate(profile)
        evaluation["processed_date"] = datetime.now().strftime("%Y-%m-%d")
        evaluation["filename"] = pdf_file.name

        print(f"  ✓ Scoring complete")

        return evaluation

    def save_evaluation(self, evaluation: Dict, filename: str = "candidate_evaluation.json"):
        """
        Save evaluation results to JSON file.

        Args:
            evaluation: Evaluation results dictionary
            filename: Output filename
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, indent=2, ensure_ascii=False)

        print(f"\n  ✓ Evaluation saved to: {output_path}")

    def print_summary(self, evaluation: Dict):
        """
        Print evaluation summary to console.

        Args:
            evaluation: Evaluation results dictionary
        """
        print("\n" + "=" * 70)
        print(" " * 25 + "EVALUATION SUMMARY")
        print("=" * 70)

        print(f"\nCandidate: {evaluation['candidate_name']}")
        print(f"Overall Score: {evaluation['overall_score']}/100")
        print(f"Recommendation: {evaluation['recommendation']}")

        print(f"\n{'Component Scores:':<30}")
        print(f"  {'JD Match:':<28} {evaluation['jd_match_score']}/100")
        print(f"  {'Pattern Match:':<28} {evaluation['pattern_match_score']}/100")

        print(f"\n{'Comparison to Good Hires:':<30}")
        print(f"  {evaluation['comparison_to_good_hires']}")

        if evaluation['strengths']:
            print(f"\n{'Strengths:':<30}")
            for strength in evaluation['strengths']:
                print(f"  {strength}")

        if evaluation['weaknesses']:
            print(f"\n{'Areas for Consideration:':<30}")
            for weakness in evaluation['weaknesses']:
                print(f"  {weakness}")

        print(f"\n{'Baseline Context:':<30}")
        stats = evaluation['baseline_stats']
        print(f"  Good hires avg experience: {stats['good_hires_avg_experience']} years")
        print(f"  Good hires with MBA: {stats['good_hires_with_mba']}")
        print(f"  Good hires with Engineering: {stats['good_hires_with_engineering']}")

        print("\n" + "=" * 70)

    def run(self, pdf_path: str):
        """
        Run the complete candidate evaluation pipeline.

        Args:
            pdf_path: Path to candidate's LinkedIn PDF
        """
        try:
            # Process candidate
            evaluation = self.process_candidate(pdf_path)

            # Save results
            self.save_evaluation(evaluation)

            # Print summary
            self.print_summary(evaluation)

            print("\n✓ Candidate evaluation complete!")

        except Exception as e:
            print(f"\n✗ Evaluation failed: {str(e)}")
            raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python process_candidate.py <path_to_linkedin_pdf>")
        print("\nExample:")
        print("  python process_candidate.py data/linkedin_pdfs/john_doe.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    processor = CandidateProcessor()
    processor.run(pdf_path)


if __name__ == "__main__":
    main()

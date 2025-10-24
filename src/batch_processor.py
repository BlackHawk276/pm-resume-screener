"""
Batch Processor for Resume Screening
Processes multiple candidate PDFs and generates comparative analysis.
"""

import sys
import csv
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import PyPDF2

from profile_analyzer import ProfileAnalyzer
from scoring_engine import CandidateScorer


class BatchProcessor:
    """Process multiple candidates in batch and generate comparative reports."""

    def __init__(self, output_dir: str = "outputs/batch_results"):
        """
        Initialize the batch processor.

        Args:
            output_dir: Directory to save batch results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        print("Initializing batch processor...")
        self.profile_analyzer = ProfileAnalyzer()
        self.scorer = CandidateScorer()
        print(f"✓ Loaded scoring baseline from {self.scorer.baseline_patterns['total_profiles']} good hires\n")

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

    def process_single_candidate(self, pdf_path: Path) -> Tuple[Dict, str]:
        """
        Process a single candidate PDF.

        Args:
            pdf_path: Path to candidate PDF

        Returns:
            Tuple of (evaluation dict, error message if any)
        """
        try:
            # Extract text
            raw_text = self.extract_pdf_text(pdf_path)

            # Analyze profile
            profile = self.profile_analyzer.analyze_profile(
                "candidate",
                raw_text,
                pdf_path.name
            )

            if "error" in profile:
                return None, f"Profile analysis failed: {profile['error']}"

            # Score candidate
            evaluation = self.scorer.score_candidate(profile)
            evaluation["processed_date"] = datetime.now().strftime("%Y-%m-%d")
            evaluation["filename"] = pdf_path.name

            return evaluation, None

        except Exception as e:
            return None, str(e)

    def get_pdf_files(self, folder_path: Path) -> List[Path]:
        """
        Get all PDF files from folder.

        Args:
            folder_path: Path to folder containing PDFs

        Returns:
            List of PDF file paths
        """
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        pdf_files = list(folder_path.glob("*.pdf"))
        return sorted(pdf_files)

    def save_individual_result(self, evaluation: Dict):
        """
        Save individual candidate result.

        Args:
            evaluation: Evaluation dictionary
        """
        # Sanitize filename
        candidate_name = evaluation['candidate_name'].replace(" ", "_").replace("/", "_")
        filename = f"{candidate_name}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, indent=2, ensure_ascii=False)

    def generate_csv_summary(self, results: List[Dict]):
        """
        Generate CSV summary file.

        Args:
            results: List of evaluation results
        """
        csv_path = self.output_dir / "batch_summary.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Candidate Name",
                "Overall Score",
                "Recommendation",
                "JD Match Score",
                "Pattern Match Score",
                "Years of Experience",
                "Has MBA",
                "Has Engineering Degree",
                "Top 3 Strengths",
                "Top 3 Weaknesses",
                "Processing Date"
            ])

            # Sort by score (descending)
            sorted_results = sorted(results, key=lambda x: x['overall_score'], reverse=True)

            # Rows
            for result in sorted_results:
                # Get profile info from detailed breakdown or baseline
                has_mba = "Yes" if any("MBA" in s for s in result.get('strengths', [])) else "No"
                has_eng = "Yes" if any("Engineering" in s for s in result.get('strengths', [])) else "No"

                # Get years of experience from strengths/weaknesses text
                years_exp = "N/A"
                for text in result.get('strengths', []) + result.get('weaknesses', []):
                    if "years" in text and "experience" in text:
                        # Try to extract number
                        words = text.split()
                        for i, word in enumerate(words):
                            if word.replace('.', '').isdigit() and i + 1 < len(words) and words[i + 1] == "years":
                                years_exp = word
                                break

                # Top strengths and weaknesses
                top_strengths = "; ".join(result.get('strengths', [])[:3])
                top_weaknesses = "; ".join(result.get('weaknesses', [])[:3]) if result.get('weaknesses') else "None identified"

                writer.writerow([
                    result['candidate_name'],
                    result['overall_score'],
                    result['recommendation'],
                    result['jd_match_score'],
                    result['pattern_match_score'],
                    years_exp,
                    has_mba,
                    has_eng,
                    top_strengths,
                    top_weaknesses,
                    result['processed_date']
                ])

        print(f"✓ CSV summary saved to: {csv_path}")

    def generate_batch_report(self, results: List[Dict], processing_time: float, errors: List[Dict]):
        """
        Generate comprehensive batch report.

        Args:
            results: List of evaluation results
            processing_time: Total processing time in seconds
            errors: List of error information
        """
        # Calculate statistics
        scores = [r['overall_score'] for r in results]
        jd_scores = [r['jd_match_score'] for r in results]
        pattern_scores = [r['pattern_match_score'] for r in results]

        # Score distribution
        score_distribution = {
            "Excellent (85-100)": len([s for s in scores if s >= 85]),
            "Strong (75-84)": len([s for s in scores if 75 <= s < 85]),
            "Good (60-74)": len([s for s in scores if 60 <= s < 75]),
            "Moderate (45-59)": len([s for s in scores if 45 <= s < 60]),
            "Weak (0-44)": len([s for s in scores if s < 45])
        }

        # Sort by score
        sorted_results = sorted(results, key=lambda x: x['overall_score'], reverse=True)

        # Top and bottom candidates
        top_5 = sorted_results[:5]
        bottom_5 = sorted_results[-5:] if len(sorted_results) > 5 else []

        # Create report
        report = {
            "batch_summary": {
                "total_candidates_processed": len(results),
                "total_errors": len(errors),
                "processing_time_seconds": round(processing_time, 2),
                "processing_time_formatted": f"{int(processing_time // 60)}m {int(processing_time % 60)}s",
                "processed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "score_statistics": {
                "average_overall_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "average_jd_match_score": round(sum(jd_scores) / len(jd_scores), 2) if jd_scores else 0,
                "average_pattern_match_score": round(sum(pattern_scores) / len(pattern_scores), 2) if pattern_scores else 0,
                "highest_score": max(scores) if scores else 0,
                "lowest_score": min(scores) if scores else 0,
                "median_score": sorted(scores)[len(scores) // 2] if scores else 0
            },
            "score_distribution": score_distribution,
            "top_5_candidates": [
                {
                    "rank": idx + 1,
                    "name": c['candidate_name'],
                    "overall_score": c['overall_score'],
                    "recommendation": c['recommendation'],
                    "jd_match_score": c['jd_match_score'],
                    "pattern_match_score": c['pattern_match_score']
                }
                for idx, c in enumerate(top_5)
            ],
            "bottom_5_candidates": [
                {
                    "rank": len(sorted_results) - len(bottom_5) + idx + 1,
                    "name": c['candidate_name'],
                    "overall_score": c['overall_score'],
                    "recommendation": c['recommendation']
                }
                for idx, c in enumerate(reversed(bottom_5))
            ] if bottom_5 else [],
            "errors": errors,
            "all_candidates_ranked": [
                {
                    "rank": idx + 1,
                    "name": c['candidate_name'],
                    "overall_score": c['overall_score'],
                    "recommendation": c['recommendation']
                }
                for idx, c in enumerate(sorted_results)
            ]
        }

        # Save report
        report_path = self.output_dir / "batch_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✓ Batch report saved to: {report_path}")

        return report

    def print_summary_table(self, results: List[Dict], min_score: float = 0):
        """
        Print summary table of all candidates.

        Args:
            results: List of evaluation results
            min_score: Minimum score threshold
        """
        print("\n" + "=" * 100)
        print(" " * 35 + "BATCH PROCESSING RESULTS")
        print("=" * 100)

        # Filter by minimum score
        filtered_results = [r for r in results if r['overall_score'] >= min_score]
        sorted_results = sorted(filtered_results, key=lambda x: x['overall_score'], reverse=True)

        if min_score > 0:
            print(f"\nShowing candidates with score >= {min_score} ({len(filtered_results)} of {len(results)} total)")

        print(f"\n{'Rank':<6} {'Candidate Name':<30} {'Score':<8} {'Recommendation':<20} {'JD Match':<10} {'Pattern':<10}")
        print("-" * 100)

        for idx, result in enumerate(sorted_results, 1):
            print(f"{idx:<6} {result['candidate_name']:<30} {result['overall_score']:<8.1f} "
                  f"{result['recommendation']:<20} {result['jd_match_score']:<10.1f} {result['pattern_match_score']:<10.1f}")

        print("=" * 100)

    def process_batch(self, folder_path: str, min_score: float = 0):
        """
        Process all candidates in a folder.

        Args:
            folder_path: Path to folder containing candidate PDFs
            min_score: Minimum score threshold for filtering
        """
        folder = Path(folder_path)

        print("=" * 70)
        print(" " * 20 + "BATCH CANDIDATE PROCESSING")
        print("=" * 70)
        print()

        # Get PDF files
        pdf_files = self.get_pdf_files(folder)

        if not pdf_files:
            print(f"✗ No PDF files found in: {folder}")
            return

        total_files = len(pdf_files)
        print(f"Found {total_files} PDF files to process")
        print(f"Minimum score threshold: {min_score}")
        print()

        # Process each candidate
        results = []
        errors = []
        start_time = time.time()

        for idx, pdf_file in enumerate(pdf_files, 1):
            elapsed = time.time() - start_time
            avg_time_per_file = elapsed / idx if idx > 0 else 0
            remaining_files = total_files - idx
            eta_seconds = avg_time_per_file * remaining_files

            print(f"[{idx}/{total_files}] Processing: {pdf_file.name}")
            print(f"  Progress: {(idx / total_files * 100):.1f}% | "
                  f"Elapsed: {int(elapsed)}s | "
                  f"ETA: {int(eta_seconds)}s")

            evaluation, error = self.process_single_candidate(pdf_file)

            if error:
                print(f"  ✗ Error: {error}")
                errors.append({
                    "filename": pdf_file.name,
                    "error": error
                })
            else:
                print(f"  ✓ {evaluation['candidate_name']}: {evaluation['overall_score']:.1f}/100 ({evaluation['recommendation']})")
                results.append(evaluation)
                self.save_individual_result(evaluation)

            print()

        total_time = time.time() - start_time

        # Generate reports
        print("=" * 70)
        print("Generating reports...")
        print("=" * 70)

        if results:
            self.generate_csv_summary(results)
            report = self.generate_batch_report(results, total_time, errors)
            self.print_summary_table(results, min_score)

            # Print statistics
            print(f"\n{'STATISTICS:':<30}")
            print(f"  Total processed: {len(results)}")
            print(f"  Errors: {len(errors)}")
            print(f"  Average score: {report['score_statistics']['average_overall_score']:.1f}/100")
            print(f"  Processing time: {report['batch_summary']['processing_time_formatted']}")

            print(f"\n{'SCORE DISTRIBUTION:':<30}")
            for category, count in report['score_distribution'].items():
                print(f"  {category:<25} {count} candidates")

            if min_score > 0:
                qualified = len([r for r in results if r['overall_score'] >= min_score])
                print(f"\n{'THRESHOLD FILTER:':<30}")
                print(f"  Candidates >= {min_score}: {qualified}/{len(results)} ({qualified/len(results)*100:.1f}%)")

        else:
            print("\n✗ No candidates successfully processed")

        print("\n" + "=" * 70)
        print("✓ Batch processing complete!")
        print(f"Results saved to: {self.output_dir}")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch process multiple candidate resumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/batch_processor.py data/linkedin_pdfs
  python src/batch_processor.py data/linkedin_pdfs --min-score 60
  python src/batch_processor.py ~/Downloads/candidates --min-score 70
        """
    )

    parser.add_argument(
        "folder",
        help="Path to folder containing candidate PDF files"
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=0,
        help="Minimum score threshold for filtering results (default: 0)"
    )

    parser.add_argument(
        "--output",
        default="outputs/batch_results",
        help="Output directory for results (default: outputs/batch_results)"
    )

    args = parser.parse_args()

    # Validate min_score
    if args.min_score < 0 or args.min_score > 100:
        print("Error: --min-score must be between 0 and 100")
        sys.exit(1)

    # Process batch
    processor = BatchProcessor(output_dir=args.output)
    processor.process_batch(args.folder, min_score=args.min_score)


if __name__ == "__main__":
    main()

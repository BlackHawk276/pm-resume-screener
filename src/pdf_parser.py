"""
PDF Parser for Resume Screening
Extracts text from LinkedIn PDF resumes and saves to JSON format.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import PyPDF2
from typing import Dict, List


class ResumeParser:
    """Parse PDF resumes and extract text content."""

    def __init__(self, pdf_dir: str = "data/linkedin_pdfs",
                 output_dir: str = "data/processed"):
        """
        Initialize the parser.

        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save processed JSON files
        """
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a single PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as a string
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()

        except Exception as e:
            print(f"   Error reading {pdf_path.name}: {str(e)}")
            return ""

        return text.strip()

    def get_pdf_files(self) -> List[Path]:
        """
        Get all PDF files from the input directory.

        Returns:
            List of PDF file paths
        """
        if not self.pdf_dir.exists():
            print(f"Directory not found: {self.pdf_dir}")
            return []

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        return sorted(pdf_files)

    def process_all_pdfs(self) -> Dict:
        """
        Process all PDF files and extract text.

        Returns:
            Dictionary with profile data
        """
        pdf_files = self.get_pdf_files()

        if not pdf_files:
            print(f"No PDF files found in {self.pdf_dir}")
            return {}

        print(f"Found {len(pdf_files)} PDF files to process")
        print("-" * 60)

        profiles = {}
        processed_count = 0
        error_count = 0

        for idx, pdf_path in enumerate(pdf_files, 1):
            profile_id = f"profile_{idx:03d}"

            print(f"[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")

            # Extract text
            raw_text = self.extract_text_from_pdf(pdf_path)

            if raw_text:
                profiles[profile_id] = {
                    "filename": pdf_path.name,
                    "raw_text": raw_text,
                    "processed_date": datetime.now().strftime("%Y-%m-%d"),
                    "char_count": len(raw_text)
                }
                processed_count += 1
                print(f"   Successfully extracted {len(raw_text)} characters")
            else:
                error_count += 1
                print(f"   Failed to extract text")

        print("-" * 60)
        print(f"Processing complete!")
        print(f"  Successfully processed: {processed_count}")
        print(f"  Errors: {error_count}")

        return profiles

    def save_to_json(self, data: Dict, filename: str = "extracted_resumes.json"):
        """
        Save extracted data to JSON file.

        Args:
            data: Dictionary containing profile data
            filename: Output filename
        """
        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\nData saved to: {output_path}")
            print(f"Total profiles: {len(data)}")

        except Exception as e:
            print(f"Error saving JSON: {str(e)}")

    def run(self):
        """Run the complete parsing pipeline."""
        print("=" * 60)
        print("Resume Parser - LinkedIn PDFs")
        print("=" * 60)
        print()

        # Process all PDFs
        profiles = self.process_all_pdfs()

        # Save to JSON
        if profiles:
            self.save_to_json(profiles)
        else:
            print("\nNo profiles to save.")


def main():
    """Main entry point for the script."""
    parser = ResumeParser()
    parser.run()


if __name__ == "__main__":
    main()

"""
Profile Analyzer
Extracts and structures information from resume profiles using OpenAI API.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv


class ProfileAnalyzer:
    """Analyze resume profiles and extract structured information."""

    def __init__(self, input_file: str = "data/processed/extracted_resumes.json",
                 output_dir: str = "data/processed"):
        """
        Initialize the profile analyzer.

        Args:
            input_file: Path to extracted resumes JSON file
            output_dir: Directory to save structured output
        """
        load_dotenv()
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-nano"

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def load_extracted_resumes(self) -> Dict:
        """
        Load extracted resumes from JSON file.

        Returns:
            Dictionary of resume profiles
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        with open(self.input_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_profile(self, profile_id: str, raw_text: str, filename: str) -> Dict:
        """
        Analyze a single resume profile using OpenAI API with retry logic.

        Args:
            profile_id: Profile identifier
            raw_text: Raw resume text
            filename: Original PDF filename

        Returns:
            Structured profile dictionary
        """
        system_prompt = """You are an expert resume analyst. Extract structured information from resumes.
Return valid JSON only with these exact keys:
- name: string (or "Not visible" if not found)
- current_role: string
- current_company: string
- years_of_experience: number (estimate if not explicit)
- education: list of education entries
- has_mba: boolean
- has_engineering_degree: boolean
- skills: list of key skills
- previous_roles: list of objects with 'title', 'company', 'duration'
- achievements: list of notable achievements
- has_tech_background: boolean
- domain_expertise: list of domain areas"""

        user_prompt = f"""Analyze this resume and extract structured information:

{raw_text[:4000]}

Return valid JSON with the required structure."""

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )

                # Parse JSON response
                result = json.loads(response.choices[0].message.content)

                # Add filename to result
                result["filename"] = filename

                return result

            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"   Attempt {attempt + 1} failed: {str(e)}")
                    print(f"   Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"   Failed after {self.max_retries} attempts: {str(e)}")
                    # Return minimal structure on complete failure
                    return {
                        "filename": filename,
                        "name": "Error",
                        "current_role": "Error",
                        "current_company": "Error",
                        "years_of_experience": 0,
                        "education": [],
                        "has_mba": False,
                        "has_engineering_degree": False,
                        "skills": [],
                        "previous_roles": [],
                        "achievements": [],
                        "has_tech_background": False,
                        "domain_expertise": [],
                        "error": str(e)
                    }

    def process_all_profiles(self, profiles: Dict) -> Dict:
        """
        Process all resume profiles.

        Args:
            profiles: Dictionary of raw resume profiles

        Returns:
            Dictionary of structured profiles
        """
        total_profiles = len(profiles)
        structured_profiles = {}
        success_count = 0
        error_count = 0

        print(f"Found {total_profiles} profiles to analyze")
        print("-" * 60)

        for idx, (profile_id, profile_data) in enumerate(profiles.items(), 1):
            print(f"Processing profile {idx} of {total_profiles}...")
            print(f"  File: {profile_data['filename']}")

            # Analyze profile
            structured_profile = self.analyze_profile(
                profile_id,
                profile_data['raw_text'],
                profile_data['filename']
            )

            # Check for errors
            if "error" in structured_profile:
                error_count += 1
                print(f"  ✗ Failed to analyze profile")
            else:
                success_count += 1
                print(f"  ✓ Successfully analyzed")
                print(f"    Name: {structured_profile.get('name', 'N/A')}")
                print(f"    Experience: {structured_profile.get('years_of_experience', 0)} years")

            structured_profiles[profile_id] = structured_profile

            # Rate limiting delay
            if idx < total_profiles:
                time.sleep(1)  # 1 second delay between API calls

        print("-" * 60)
        print(f"Processing complete!")
        print(f"  Successfully analyzed: {success_count}")
        print(f"  Errors: {error_count}")

        return structured_profiles

    def save_structured_profiles(self, profiles: Dict,
                                  filename: str = "structured_profiles.json"):
        """
        Save structured profiles to JSON file.

        Args:
            profiles: Dictionary of structured profiles
            filename: Output filename
        """
        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)

            print(f"\nStructured profiles saved to: {output_path}")
            print(f"Total profiles: {len(profiles)}")

        except Exception as e:
            print(f"Error saving structured profiles: {str(e)}")
            raise

    def run(self) -> Dict:
        """
        Run the complete profile analysis pipeline.

        Returns:
            Dictionary of structured profiles
        """
        print("=" * 60)
        print("Profile Analyzer - Resume Analysis")
        print("=" * 60)
        print()

        # Load extracted resumes
        extracted_profiles = self.load_extracted_resumes()

        # Process all profiles
        structured_profiles = self.process_all_profiles(extracted_profiles)

        # Save results
        self.save_structured_profiles(structured_profiles)

        return structured_profiles


def main():
    """Main entry point for the script."""
    try:
        analyzer = ProfileAnalyzer()
        analyzer.run()
    except Exception as e:
        print(f"\nFailed to analyze profiles: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()

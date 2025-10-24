"""
Job Description Analyzer
Extracts and structures requirements from Product Manager job descriptions using OpenAI API.
"""

import os
import json
from pathlib import Path
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv


class JDAnalyzer:
    """Analyze job descriptions and extract structured requirements."""

    def __init__(self, jd_path: str = "job_description.txt",
                 output_dir: str = "data/processed"):
        """
        Initialize the JD analyzer.

        Args:
            jd_path: Path to job description text file
            output_dir: Directory to save structured output
        """
        load_dotenv()
        self.jd_path = Path(jd_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-nano"

    def read_job_description(self) -> str:
        """
        Read job description from file.

        Returns:
            Job description text
        """
        if not self.jd_path.exists():
            raise FileNotFoundError(f"Job description file not found: {self.jd_path}")

        with open(self.jd_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def analyze_jd(self, jd_text: str) -> Dict:
        """
        Analyze job description using OpenAI API.

        Args:
            jd_text: Job description text

        Returns:
            Structured requirements dictionary
        """
        system_prompt = """You are an expert HR analyst. Extract structured information from job descriptions.
Return valid JSON only with these exact keys:
- required_qualifications: list of required education/certifications
- required_experience: object with 'years' (number) and 'domains' (list)
- key_responsibilities: list of main responsibilities
- must_have_skills: list of required skills
- nice_to_have_skills: list of preferred skills
- key_competencies: list of competencies mentioned"""

        user_prompt = f"""Analyze this Product Manager job description and extract structured requirements:

{jd_text}

Return valid JSON with the required structure."""

        try:
            print("Analyzing job description with OpenAI API...")

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

            print("✓ Job description analysis complete")
            return result

        except Exception as e:
            print(f"Error analyzing job description: {str(e)}")
            raise

    def save_requirements(self, requirements: Dict, filename: str = "jd_requirements.json"):
        """
        Save structured requirements to JSON file.

        Args:
            requirements: Structured requirements dictionary
            filename: Output filename
        """
        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(requirements, f, indent=2, ensure_ascii=False)

            print(f"\nRequirements saved to: {output_path}")

        except Exception as e:
            print(f"Error saving requirements: {str(e)}")
            raise

    def run(self) -> Dict:
        """
        Run the complete JD analysis pipeline.

        Returns:
            Structured requirements dictionary
        """
        print("=" * 60)
        print("Job Description Analyzer")
        print("=" * 60)
        print()

        # Read job description
        jd_text = self.read_job_description()
        print(f"Loaded job description ({len(jd_text)} characters)")

        # Analyze with OpenAI
        requirements = self.analyze_jd(jd_text)

        # Save results
        self.save_requirements(requirements)

        return requirements


def main():
    """Main entry point for the script."""
    try:
        analyzer = JDAnalyzer()
        analyzer.run()
    except Exception as e:
        print(f"\nFailed to analyze job description: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()

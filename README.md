# PM Resume Screener

A Python-based resume screening assistant for Product Manager roles. This tool extracts and analyzes LinkedIn PDF resumes using OpenAI's API.

## Project Structure

```
pm-resume-screener/
├── data/
│   ├── linkedin_pdfs/       # Place your LinkedIn PDFs here
│   └── processed/           # Extracted and analyzed data (JSON)
├── src/
│   ├── pdf_parser.py        # PDF text extraction
│   ├── jd_analyzer.py       # Job description analysis
│   ├── profile_analyzer.py  # Resume profile analysis
│   └── run_analysis.py      # Main analysis orchestrator
├── outputs/                 # Analysis results
├── job_description.txt      # Product Manager job description
├── requirements.txt         # Python dependencies
├── .env.example            # Template for environment variables
└── .gitignore              # Git ignore rules
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and add your key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

### 3. Add Resume PDFs

Place all LinkedIn PDF resumes in the `data/linkedin_pdfs/` directory.

## Usage

### Complete Analysis Pipeline (Recommended)

Run the full analysis pipeline:

```bash
python src/run_analysis.py
```

This will:
1. Analyze the job description from `job_description.txt`
2. Analyze all resume profiles using OpenAI GPT-5 Nano
3. Generate summary statistics including:
   - Average years of experience
   - Percentage with MBA
   - Percentage with Engineering background
   - Top 10 most common skills
   - And more...

Output files:
- `data/processed/jd_requirements.json` - Structured job requirements
- `data/processed/structured_profiles.json` - Analyzed candidate profiles
- `data/processed/analysis_statistics.json` - Summary statistics

### Individual Steps

#### Step 1: Parse PDF Resumes

Extract text from all PDFs:

```bash
python src/pdf_parser.py
```

This reads PDFs from `data/linkedin_pdfs/` and saves to `data/processed/extracted_resumes.json`.

#### Step 2: Analyze Job Description

```bash
python src/jd_analyzer.py
```

Analyzes `job_description.txt` and extracts structured requirements.

#### Step 3: Analyze Resume Profiles

```bash
python src/profile_analyzer.py
```

Processes each resume and extracts structured information using OpenAI API.

## Dependencies

- **pypdf2**: PDF parsing and text extraction
- **openai**: OpenAI API integration
- **pandas**: Data manipulation and analysis
- **python-dotenv**: Environment variable management
- **streamlit**: Web interface (for future features)
- **numpy**: Numerical operations

## Features

- **PDF Text Extraction**: Extracts text from LinkedIn PDF resumes
- **Job Description Analysis**: Uses GPT-5 Nano to structure job requirements
- **Profile Analysis**: Extracts structured information from resumes including:
  - Name, current role, company
  - Years of experience
  - Education (MBA, Engineering degree detection)
  - Skills and competencies
  - Previous roles and achievements
  - Technical background assessment
  - Domain expertise
- **Summary Statistics**: Generates insights across all candidates
- **Retry Logic**: Handles API failures with automatic retries
- **Rate Limiting**: Built-in delays to respect API rate limits

## Future Enhancements

- Score candidates based on job requirements match
- Generate detailed comparison reports
- Build Streamlit dashboard for interactive visualization
- Add candidate ranking and recommendation system

## Security Notes

- Never commit your `.env` file (it's in `.gitignore`)
- The `data/` folder is ignored by git to protect candidate privacy
- Keep your OpenAI API key secure

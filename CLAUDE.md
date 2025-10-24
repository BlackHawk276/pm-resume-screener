# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A comprehensive Python-based resume screening system for Product Manager roles. The system analyzes LinkedIn PDF resumes using OpenAI GPT-5 Nano, scores candidates against job requirements, compares them to successful hire patterns, and provides a full-featured web interface for evaluation.

## Setup

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure OpenAI API key:**
```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

## Common Commands

### Initial Setup and Analysis
```bash
# Run complete pipeline to analyze 52 good hire profiles
python src/run_analysis.py

# Extract text from PDFs only
python src/pdf_parser.py

# Analyze job description only
python src/jd_analyzer.py

# Analyze profiles only (requires extracted_resumes.json)
python src/profile_analyzer.py
```

### Candidate Evaluation
```bash
# Evaluate single candidate
python src/process_candidate.py path/to/resume.pdf

# Batch process multiple candidates
python src/batch_processor.py path/to/folder --min-score 60

# Test scoring system
python src/test_scoring.py --quick  # Quick initialization test
python src/test_scoring.py          # Full test with 3 profiles
```

### Web Interface
```bash
# Launch Streamlit web application
streamlit run app.py
```

## Architecture

This system consists of three main layers: **Data Processing**, **Scoring Engine**, and **User Interfaces**.

### Layer 1: Data Processing Pipeline

The pipeline transforms raw PDFs into structured candidate profiles:

**1. PDF Extraction (`pdf_parser.py`)**
- Input: LinkedIn PDFs in `data/linkedin_pdfs/`
- Uses PyPDF2 to extract text from all pages
- Output: `data/processed/extracted_resumes.json` with raw text + metadata

**2. Job Description Analysis (`jd_analyzer.py`)**
- Input: `job_description.txt` (project root)
- OpenAI GPT-5 Nano extracts structured requirements using JSON mode
- Output: `data/processed/jd_requirements.json`
- Extracted fields: required_qualifications, required_experience, key_responsibilities, must_have_skills, nice_to_have_skills, key_competencies

**3. Profile Analysis (`profile_analyzer.py`)**
- Input: `extracted_resumes.json`
- OpenAI GPT-5 Nano analyzes each resume (1 API call per profile)
- Retry logic: 3 attempts with 2-second delays
- Rate limiting: 1-second delay between profiles
- Text truncation: First 4000 characters per resume
- Output: `data/processed/structured_profiles.json`
- Extracted fields: name, current_role, current_company, years_of_experience, education, has_mba, has_engineering_degree, skills, previous_roles, achievements, has_tech_background, domain_expertise

**4. Statistics Generation (`run_analysis.py`)**
- Orchestrates steps 2-3
- Calculates baseline patterns from good hires
- Output: `data/processed/analysis_statistics.json`

### Layer 2: Scoring Engine

**CandidateScorer (`scoring_engine.py`)**

Evaluates new candidates using two weighted components:

**JD Match Score (40% weight):**
- Required qualifications match (MBA + Engineering): 25%
- Experience level appropriateness: 20%
- Must-have skills match: 30%
- Nice-to-have skills match: 15%
- Domain expertise match: 10%

**Pattern Match Score (60% weight):**
- Experience similarity to good hires: 25%
- Skills overlap with common skills: 30%
- Education pattern match: 20%
- Tech background match: 15%
- Career progression similarity: 10%

Uses semantic similarity via OpenAI API for skill matching (not just exact string matches).

Outputs scores (0-100) with recommendations:
- Excellent (85-100)
- Strong (75-84)
- Good (60-74)
- Moderate (45-59)
- Weak (0-44)

### Layer 3: User Interfaces

**Single Candidate Processor (`process_candidate.py`)**
- CLI tool for evaluating one PDF at a time
- Usage: `python src/process_candidate.py path/to/resume.pdf`
- Output: `outputs/candidate_evaluation.json`

**Batch Processor (`batch_processor.py`)**
- CLI tool for processing multiple PDFs from a folder
- Features: progress tracking, ETA, error handling, score threshold filtering
- Usage: `python src/batch_processor.py folder/ --min-score 60`
- Outputs:
  - Individual JSONs per candidate in `outputs/batch_results/`
  - `batch_summary.csv` - Ranked candidates with scores
  - `batch_report.json` - Comprehensive statistics and rankings

**Web Application (`app.py`)**
- Streamlit-based web interface
- Four main pages:
  1. **Single Evaluation**: Upload PDF, view detailed scores with gauge charts
  2. **Batch Processing**: Upload multiple PDFs, view distribution charts and rankings
  3. **Candidate Comparison**: Side-by-side comparison with radar charts (2-5 candidates)
  4. **Analytics Dashboard**: View statistics from 52 good hires with interactive charts
- Features: session state, caching, Plotly visualizations, CSV/JSON exports

## Key Data Flow

```
LinkedIn PDFs → [pdf_parser.py] → extracted_resumes.json
                                           ↓
job_description.txt → [jd_analyzer.py] → jd_requirements.json
                                           ↓
                    [profile_analyzer.py] → structured_profiles.json
                                           ↓
                    [scoring_engine.py] → evaluation scores
                                           ↓
                    [UI Layer] → CSV/JSON reports or Web UI
```

## Critical Implementation Details

**OpenAI API Configuration:**
- Model: `gpt-5-nano` (hardcoded in all analyzers)
- Response format: `{"type": "json_object"}` for structured outputs
- Temperature: NOT supported by gpt-5-nano (removed from all API calls)
- Cost optimization: Text truncated to 4000 characters in profile_analyzer

**Performance Expectations:**
- Single profile analysis: ~26 seconds (OpenAI API time)
- Batch of 52 profiles: ~23-25 minutes total
- Rate limiting: 1-second delay between profiles to respect API limits

**Error Handling Philosophy:**
- ProfileAnalyzer: Returns minimal structure with "error" field on failure (continues processing)
- JDAnalyzer: Raises exceptions (expects valid input)
- BatchProcessor: Skips corrupted PDFs, continues with rest
- All components log progress to console

**Baseline Calculation:**
- System loads 52 good hire profiles from `structured_profiles.json`
- Calculates: avg experience (10.1 years), MBA % (48%), Engineering % (65%), Tech background % (98%)
- Top skills frequency distribution used for pattern matching

## Dependencies

Core packages in `requirements.txt`:
- `pypdf2==3.0.1` - PDF text extraction
- `openai==1.54.0` - OpenAI API client
- `python-dotenv==1.0.0` - Environment variable management
- `streamlit==1.39.0` - Web application framework
- `plotly==5.18.0` - Interactive charts in Streamlit
- `pandas==2.2.0` - Data manipulation for CSVs
- `numpy==1.26.3` - Numerical operations

## File Locations and Outputs

**Input Files:**
- LinkedIn PDFs: `data/linkedin_pdfs/` (gitignored)
- Job Description: `job_description.txt` (project root)
- Environment: `.env` (gitignored, use `.env.example` as template)

**Processed Data (all in `data/processed/`, gitignored):**
- `extracted_resumes.json` - Raw text from PDFs
- `jd_requirements.json` - Structured job requirements
- `structured_profiles.json` - Analyzed candidate profiles (52 good hires)
- `analysis_statistics.json` - Baseline statistics

**Output Files (all in `outputs/`, gitignored):**
- `candidate_evaluation.json` - Single candidate result
- `batch_results/` - Batch processing folder
  - Individual candidate JSONs: `{name}_evaluation.json`
  - `batch_summary.csv` - Ranked candidates table
  - `batch_report.json` - Statistics and top/bottom performers

## Troubleshooting

**"Temperature parameter not supported" error:**
- The `gpt-5-nano` model does NOT support the temperature parameter
- All API calls in this codebase have had temperature removed
- If adding new OpenAI calls, omit the `temperature` parameter

**Slow processing times:**
- Expected: ~26 seconds per profile for OpenAI API calls
- Batch of 52 profiles takes ~23-25 minutes
- This is normal behavior for the gpt-5-nano model

**Missing baseline data for Streamlit app:**
- Run `python src/run_analysis.py` first to create baseline files
- The web app requires `data/processed/structured_profiles.json` and `jd_requirements.json`

**API rate limit errors:**
- The system includes 1-second delays between profiles
- Retry logic attempts 3 times with 2-second delays
- If errors persist, check your OpenAI account rate limits

## Security and Privacy

- `.env` file contains OPENAI_API_KEY (never commit)
- `data/` directory gitignored to protect candidate privacy
- `outputs/` directory gitignored to protect evaluation results
- Resume text handled in memory, not permanently stored beyond JSON outputs

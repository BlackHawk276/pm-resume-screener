# Streamlit Web Application Guide

## Quick Start

Run the Streamlit web application:

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Features

### 📋 Single Candidate Evaluation
- Upload a LinkedIn PDF
- Get instant AI-powered evaluation
- View detailed score breakdown
- Download JSON report

### 📦 Batch Processing
- Upload multiple PDFs (up to 50)
- Set minimum score threshold
- View score distribution charts
- Export results as CSV or JSON

### ⚖️ Candidate Comparison
- Compare 2-5 candidates side-by-side
- Visual radar charts
- Detailed strengths/weaknesses comparison

### 📈 Analytics Dashboard
- View statistics from 52 good hires
- Education and skill distributions
- Interactive charts and visualizations

## Navigation

Use the sidebar to switch between pages and view your evaluated candidates.

## Tips

- The app caches the scoring engine for faster subsequent evaluations
- All evaluated candidates are stored in session state for comparison
- Use the "Clear All Data" button to reset

## Requirements

Make sure you have run the analysis pipeline first:

```bash
python src/run_analysis.py
```

This creates the necessary baseline data files in `data/processed/`.

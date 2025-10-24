"""
PM Resume Screener - Streamlit Web Application
A comprehensive web interface for evaluating Product Manager candidates.
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import tempfile
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from profile_analyzer import ProfileAnalyzer
from scoring_engine import CandidateScorer
import PyPDF2


# Page configuration
st.set_page_config(
    page_title="PM Resume Screener",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .score-excellent {
        color: #28a745;
        font-weight: bold;
    }
    .score-strong {
        color: #5cb85c;
        font-weight: bold;
    }
    .score-good {
        color: #17a2b8;
        font-weight: bold;
    }
    .score-moderate {
        color: #ffc107;
        font-weight: bold;
    }
    .score-weak {
        color: #dc3545;
        font-weight: bold;
    }
    .strength-item {
        color: #28a745;
        margin: 0.3rem 0;
    }
    .weakness-item {
        color: #dc3545;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'evaluated_candidates' not in st.session_state:
    st.session_state.evaluated_candidates = []
if 'scorer' not in st.session_state:
    st.session_state.scorer = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None


@st.cache_data
def load_good_hires_data():
    """Load and cache good hires data."""
    try:
        with open('data/processed/structured_profiles.json', 'r') as f:
            profiles = json.load(f)

        with open('data/processed/jd_requirements.json', 'r') as f:
            jd_requirements = json.load(f)

        return profiles, jd_requirements
    except FileNotFoundError:
        return None, None


@st.cache_resource
def get_scorer():
    """Get cached scorer instance."""
    return CandidateScorer()


@st.cache_resource
def get_analyzer():
    """Get cached analyzer instance."""
    return ProfileAnalyzer()


def get_score_color(score):
    """Get color based on score."""
    if score >= 85:
        return "#28a745"
    elif score >= 75:
        return "#5cb85c"
    elif score >= 60:
        return "#17a2b8"
    elif score >= 45:
        return "#ffc107"
    else:
        return "#dc3545"


def get_recommendation_class(recommendation):
    """Get CSS class for recommendation."""
    if "Excellent" in recommendation or "Strong" in recommendation:
        return "score-excellent"
    elif "Good" in recommendation:
        return "score-good"
    elif "Moderate" in recommendation:
        return "score-moderate"
    else:
        return "score-weak"


def extract_pdf_text(uploaded_file):
    """Extract text from uploaded PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting PDF: {str(e)}")
        return None


def evaluate_candidate(uploaded_file):
    """Evaluate a single candidate."""
    # Initialize components
    if st.session_state.scorer is None:
        with st.spinner("Initializing scoring engine..."):
            st.session_state.scorer = get_scorer()
            st.session_state.analyzer = get_analyzer()

    # Extract text
    with st.spinner("Extracting text from PDF..."):
        raw_text = extract_pdf_text(uploaded_file)
        if not raw_text:
            return None

    # Analyze profile
    with st.spinner("Analyzing profile with AI..."):
        profile = st.session_state.analyzer.analyze_profile(
            "candidate",
            raw_text,
            uploaded_file.name
        )

        if "error" in profile:
            st.error(f"Profile analysis failed: {profile['error']}")
            return None

    # Score candidate
    with st.spinner("Scoring candidate..."):
        evaluation = st.session_state.scorer.score_candidate(profile)
        evaluation["processed_date"] = datetime.now().strftime("%Y-%m-%d")
        evaluation["filename"] = uploaded_file.name

    return evaluation


def display_single_evaluation(evaluation):
    """Display detailed candidate evaluation."""
    # Header with name and overall score
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"<h1>{evaluation['candidate_name']}</h1>", unsafe_allow_html=True)

    with col2:
        score_color = get_score_color(evaluation['overall_score'])
        st.markdown(f"<h2 style='color: {score_color};'>{evaluation['overall_score']}/100</h2>", unsafe_allow_html=True)

    with col3:
        rec_class = get_recommendation_class(evaluation['recommendation'])
        st.markdown(f"<h3 class='{rec_class}'>{evaluation['recommendation']}</h3>", unsafe_allow_html=True)

    # Score gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=evaluation['overall_score'],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Score"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': score_color},
            'steps': [
                {'range': [0, 45], 'color': "lightgray"},
                {'range': [45, 60], 'color': "lightyellow"},
                {'range': [60, 75], 'color': "lightblue"},
                {'range': [75, 85], 'color': "lightgreen"},
                {'range': [85, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Component scores
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 JD Match Score")
        st.metric("Score", f"{evaluation['jd_match_score']}/100")

        with st.expander("Breakdown"):
            breakdown = evaluation['detailed_breakdown']['jd_components']
            for component, score in breakdown.items():
                st.write(f"**{component.replace('_', ' ').title()}:** {score:.1f}")

    with col2:
        st.subheader("🎯 Pattern Match Score")
        st.metric("Score", f"{evaluation['pattern_match_score']}/100")

        with st.expander("Breakdown"):
            breakdown = evaluation['detailed_breakdown']['pattern_components']
            for component, score in breakdown.items():
                st.write(f"**{component.replace('_', ' ').title()}:** {score:.1f}")

    # Strengths and Weaknesses
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Strengths")
        if evaluation['strengths']:
            for strength in evaluation['strengths']:
                st.markdown(f"<p class='strength-item'>✓ {strength.replace('✓', '').strip()}</p>", unsafe_allow_html=True)
        else:
            st.write("No specific strengths identified")

    with col2:
        st.subheader("⚠️ Areas for Consideration")
        if evaluation['weaknesses']:
            for weakness in evaluation['weaknesses']:
                st.markdown(f"<p class='weakness-item'>⚠ {weakness.replace('⚠', '').strip()}</p>", unsafe_allow_html=True)
        else:
            st.success("No specific weaknesses identified")

    # Comparison to good hires
    st.subheader("📊 Comparison to Good Hires")
    st.info(evaluation['comparison_to_good_hires'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Good Hires Avg Experience", evaluation['baseline_stats']['good_hires_avg_experience'])
    with col2:
        st.metric("Good Hires with MBA", evaluation['baseline_stats']['good_hires_with_mba'])
    with col3:
        st.metric("Good Hires with Engineering", evaluation['baseline_stats']['good_hires_with_engineering'])

    # Download button
    st.download_button(
        label="📥 Download JSON Report",
        data=json.dumps(evaluation, indent=2),
        file_name=f"{evaluation['candidate_name'].replace(' ', '_')}_evaluation.json",
        mime="application/json"
    )


def page_single_evaluation():
    """Single candidate evaluation page."""
    st.markdown("<h1 class='main-header'>📋 Single Candidate Evaluation</h1>", unsafe_allow_html=True)
    st.write("Upload a LinkedIn PDF to evaluate a Product Manager candidate.")

    uploaded_file = st.file_uploader("Choose a LinkedIn PDF", type=['pdf'])

    if uploaded_file:
        if st.button("🚀 Evaluate Candidate", type="primary"):
            evaluation = evaluate_candidate(uploaded_file)

            if evaluation:
                st.success("✅ Evaluation complete!")
                st.session_state.evaluated_candidates.append(evaluation)
                display_single_evaluation(evaluation)
            else:
                st.error("Failed to evaluate candidate. Please try again.")


def page_batch_processing():
    """Batch processing page."""
    st.markdown("<h1 class='main-header'>📦 Batch Processing</h1>", unsafe_allow_html=True)
    st.write("Upload multiple LinkedIn PDFs to evaluate several candidates at once.")

    uploaded_files = st.file_uploader(
        "Choose LinkedIn PDFs (up to 50 files)",
        type=['pdf'],
        accept_multiple_files=True
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        min_score = st.slider("Minimum Score Threshold", 0, 100, 60, 5)

    with col2:
        st.metric("Files Selected", len(uploaded_files) if uploaded_files else 0)

    if uploaded_files and len(uploaded_files) > 0:
        if len(uploaded_files) > 50:
            st.warning("⚠️ Maximum 50 files allowed. Only first 50 will be processed.")
            uploaded_files = uploaded_files[:50]

        if st.button("🚀 Process Batch", type="primary"):
            # Initialize components
            if st.session_state.scorer is None:
                with st.spinner("Initializing scoring engine..."):
                    st.session_state.scorer = get_scorer()
                    st.session_state.analyzer = get_analyzer()

            # Process candidates
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")

                evaluation = evaluate_candidate(uploaded_file)
                if evaluation:
                    results.append(evaluation)
                    st.session_state.evaluated_candidates.append(evaluation)

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("✅ Batch processing complete!")

            if results:
                # Summary statistics
                st.subheader("📊 Summary Statistics")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Processed", len(results))
                with col2:
                    avg_score = sum(r['overall_score'] for r in results) / len(results)
                    st.metric("Average Score", f"{avg_score:.1f}")
                with col3:
                    qualified = len([r for r in results if r['overall_score'] >= min_score])
                    st.metric(f"Score >= {min_score}", qualified)
                with col4:
                    top_score = max(r['overall_score'] for r in results)
                    st.metric("Top Score", f"{top_score:.1f}")

                # Score distribution chart
                scores = [r['overall_score'] for r in results]
                score_ranges = {
                    "Excellent (85-100)": len([s for s in scores if s >= 85]),
                    "Strong (75-84)": len([s for s in scores if 75 <= s < 85]),
                    "Good (60-74)": len([s for s in scores if 60 <= s < 75]),
                    "Moderate (45-59)": len([s for s in scores if 45 <= s < 60]),
                    "Weak (0-44)": len([s for s in scores if s < 45])
                }

                fig = px.bar(
                    x=list(score_ranges.keys()),
                    y=list(score_ranges.values()),
                    labels={'x': 'Score Range', 'y': 'Number of Candidates'},
                    title="Score Distribution",
                    color=list(score_ranges.values()),
                    color_continuous_scale=['red', 'yellow', 'lightblue', 'lightgreen', 'green']
                )
                st.plotly_chart(fig, use_container_width=True)

                # Candidates table
                st.subheader("🎯 Candidate Rankings")

                # Filter by minimum score
                filtered_results = [r for r in results if r['overall_score'] >= min_score]
                sorted_results = sorted(filtered_results, key=lambda x: x['overall_score'], reverse=True)

                # Create DataFrame
                df = pd.DataFrame([
                    {
                        "Rank": idx + 1,
                        "Name": r['candidate_name'],
                        "Score": r['overall_score'],
                        "Recommendation": r['recommendation'],
                        "JD Match": r['jd_match_score'],
                        "Pattern Match": r['pattern_match_score']
                    }
                    for idx, r in enumerate(sorted_results)
                ])

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                # Download options
                st.subheader("📥 Download Results")

                col1, col2 = st.columns(2)

                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV Summary",
                        data=csv_data,
                        file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    json_data = json.dumps(results, indent=2)
                    st.download_button(
                        label="Download JSON Report",
                        data=json_data,
                        file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )


def page_comparison():
    """Candidate comparison page."""
    st.markdown("<h1 class='main-header'>⚖️ Candidate Comparison</h1>", unsafe_allow_html=True)

    if len(st.session_state.evaluated_candidates) < 2:
        st.warning("⚠️ You need to evaluate at least 2 candidates to use the comparison feature.")
        st.info("Go to 'Single Evaluation' or 'Batch Processing' to evaluate candidates first.")
        return

    st.write("Compare multiple candidates side-by-side.")

    # Select candidates
    candidate_names = [c['candidate_name'] for c in st.session_state.evaluated_candidates]
    selected_names = st.multiselect(
        "Select 2-5 candidates to compare",
        candidate_names,
        max_selections=5
    )

    if len(selected_names) >= 2:
        selected_candidates = [
            c for c in st.session_state.evaluated_candidates
            if c['candidate_name'] in selected_names
        ]

        # Comparison table
        st.subheader("📊 Score Comparison")

        comparison_data = []
        for candidate in selected_candidates:
            comparison_data.append({
                "Name": candidate['candidate_name'],
                "Overall Score": candidate['overall_score'],
                "JD Match": candidate['jd_match_score'],
                "Pattern Match": candidate['pattern_match_score'],
                "Recommendation": candidate['recommendation']
            })

        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Radar chart
        st.subheader("🎯 Visual Comparison")

        categories = ['Overall', 'JD Match', 'Pattern Match']

        fig = go.Figure()

        for candidate in selected_candidates:
            fig.add_trace(go.Scatterpolar(
                r=[
                    candidate['overall_score'],
                    candidate['jd_match_score'],
                    candidate['pattern_match_score']
                ],
                theta=categories,
                fill='toself',
                name=candidate['candidate_name']
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=True,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed comparison
        st.subheader("🔍 Detailed Comparison")

        for candidate in selected_candidates:
            with st.expander(f"📋 {candidate['candidate_name']} - {candidate['overall_score']}/100"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Strengths:**")
                    for strength in candidate.get('strengths', [])[:3]:
                        st.write(f"✓ {strength}")

                with col2:
                    st.write("**Weaknesses:**")
                    weaknesses = candidate.get('weaknesses', [])
                    if weaknesses:
                        for weakness in weaknesses[:3]:
                            st.write(f"⚠ {weakness}")
                    else:
                        st.write("None identified")


def page_analytics():
    """Analytics dashboard page."""
    st.markdown("<h1 class='main-header'>📈 Analytics Dashboard</h1>", unsafe_allow_html=True)

    profiles, jd_requirements = load_good_hires_data()

    if profiles is None:
        st.error("❌ Could not load good hires data. Please run the analysis pipeline first.")
        return

    # JD Requirements
    st.subheader("📋 Job Requirements")

    with st.expander("View Job Description Requirements"):
        if jd_requirements:
            st.write("**Required Qualifications:**")
            for qual in jd_requirements.get('required_qualifications', []):
                st.write(f"• {qual}")

            st.write("**Must-Have Skills:**")
            for skill in jd_requirements.get('must_have_skills', []):
                st.write(f"• {skill}")

    # Good hires statistics
    st.subheader("👥 Good Hires Profile (52 candidates)")

    valid_profiles = [p for p in profiles.values() if "error" not in p]

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_exp = sum(p.get('years_of_experience', 0) for p in valid_profiles) / len(valid_profiles)
        st.metric("Avg Experience", f"{avg_exp:.1f} years")

    with col2:
        mba_count = sum(1 for p in valid_profiles if p.get('has_mba', False))
        st.metric("With MBA", f"{mba_count/len(valid_profiles)*100:.0f}%")

    with col3:
        eng_count = sum(1 for p in valid_profiles if p.get('has_engineering_degree', False))
        st.metric("With Engineering", f"{eng_count/len(valid_profiles)*100:.0f}%")

    with col4:
        tech_count = sum(1 for p in valid_profiles if p.get('has_tech_background', False))
        st.metric("Tech Background", f"{tech_count/len(valid_profiles)*100:.0f}%")

    # Education distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎓 Education Distribution")
        education_data = {
            "MBA": mba_count,
            "Engineering": eng_count,
            "Other": len(valid_profiles) - max(mba_count, eng_count)
        }
        fig = px.pie(
            values=list(education_data.values()),
            names=list(education_data.keys()),
            title="Education Background"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💼 Tech vs Non-Tech")
        tech_data = {
            "Tech Background": tech_count,
            "Non-Tech": len(valid_profiles) - tech_count
        }
        fig = px.pie(
            values=list(tech_data.values()),
            names=list(tech_data.keys()),
            title="Technical Background"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Most common skills
    st.subheader("🎯 Most Common Skills")

    all_skills = []
    for p in valid_profiles:
        skills = p.get('skills', [])
        if isinstance(skills, list):
            all_skills.extend(skills)

    from collections import Counter
    skill_counts = Counter(all_skills).most_common(10)

    if skill_counts:
        fig = px.bar(
            x=[count for skill, count in skill_counts],
            y=[skill for skill, count in skill_counts],
            orientation='h',
            labels={'x': 'Number of Candidates', 'y': 'Skill'},
            title="Top 10 Skills Among Good Hires"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)


# Sidebar
with st.sidebar:
    st.markdown("# 📋 PM Resume Screener")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Single Evaluation", "Batch Processing", "Comparison", "Analytics Dashboard"]
    )

    st.markdown("---")

    st.markdown("### ℹ️ About")
    st.markdown("""
    This application evaluates Product Manager candidates by:
    - Analyzing LinkedIn PDF resumes
    - Scoring against job requirements
    - Comparing to successful hire patterns

    **Powered by OpenAI GPT-5 Nano**
    """)

    st.markdown("---")

    if st.session_state.evaluated_candidates:
        st.success(f"✅ {len(st.session_state.evaluated_candidates)} candidates evaluated")

    if st.button("🗑️ Clear All Data"):
        st.session_state.evaluated_candidates = []
        st.success("Data cleared!")
        st.rerun()


# Main content
if page == "Single Evaluation":
    page_single_evaluation()
elif page == "Batch Processing":
    page_batch_processing()
elif page == "Comparison":
    page_comparison()
elif page == "Analytics Dashboard":
    page_analytics()

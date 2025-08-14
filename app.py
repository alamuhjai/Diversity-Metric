import streamlit as st
import pandas as pd
import json

# Load The Cleaned Dataset
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("institutional_diversity_metric.csv")
        
        # Verify required columns exist
        required_columns = [
            'unitid', 'institution', 'city', 'state', 'level',
            'male_students', 'female_students', 'total_students',
            'gender_proportions', 'race_proportions',
            'descriptive_gender', 'descriptive_race', 'descriptive_joint',
            'representative_gender', 'representative_race', 'representative_joint',
            'compensatory_gender', 'compensatory_race', 'compensatory_joint',
            'blaus_gender', 'blaus_race',
            'R1', 'R2', 'D/PU', 'Masters', 'Baccalaureate', 'BacAssoc', 'Associates',
            'SpecialFocus', 'Tribal', 'HBCU', 'FaithRelated', 'MedicalHealth',
            'EngineeringTech', 'Business', 'Arts', 'Law'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                st.stop()

        # Convert JSON strings to dictionaries
        if isinstance(df.loc[0, "gender_proportions"], str):
            df["gender_proportions"] = df["gender_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))
            df["race_proportions"] = df["race_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))

        # Calculate percentages
        df["percent_female"] = df["gender_proportions"].apply(lambda x: round(x.get("female", 0.0) * 100, 2))
        df["percent_of_color"] = df["race_proportions"].apply(lambda x: round((1.0 - x.get("white_nh", 0.0)) * 100, 2))

        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

# Carnegie Classification Options
def get_carnegie_filters():
    return {
        "R1: Doctoral Universities – Very high research": "R1",
        "R2: Doctoral Universities – High research": "R2",
        "D/PU: Doctoral/Professional Universities": "D/PU",
        "Master's Colleges and Universities": "Masters",
        "Baccalaureate Colleges": "Baccalaureate",
        "Baccalaureate/Associate's Colleges": "BacAssoc",
        "Associate's Colleges": "Associates",
        "Special Focus Institutions": "SpecialFocus",
        "Tribal Colleges and Universities": "Tribal",
        "HBCU (Historically Black Colleges)": "HBCU",
        "Faith-Related Institutions": "FaithRelated",
        "Medical Schools & Centers": "MedicalHealth",
        "Engineering and Technology Schools": "EngineeringTech",
        "Business & Management Schools": "Business",
        "Arts, Music & Design Schools": "Arts",
        "Law Schools": "Law"
    }

def main():
    st.set_page_config(layout="wide", page_title="Institutional Diversity Dashboard")
    st.title("🏛️ Institutional Diversity Ranking Tool")
    
    # Load data with error handling
    df = load_data()
    carnegie_options = get_carnegie_filters()

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filter Options")
        
        # Program Level Filters
        st.subheader("🎓 Program Levels")
        level_options = ["All Levels", "Undergraduate", "Graduate", "Other"]  # Added "Other" option
        selected_level = st.radio(
            "Select Program Level",
            options=level_options,
            index=0
        )
        
        # State filter
        selected_states = st.multiselect(
            "Select States (optional)",
            options=sorted(df["state"].unique())
        )
        
        # Metric selector - with verification
        metric_options = {
            "Descriptive (Gender)": "descriptive_gender",
            "Descriptive (Race)": "descriptive_race",
            "Descriptive (Joint)": "descriptive_joint",
            "Representative (Gender)": "representative_gender",
            "Representative (Race)": "representative_race",
            "Representative (Joint)": "representative_joint",
            "Compensatory (Gender)": "compensatory_gender",
            "Compensatory (Race)": "compensatory_race",
            "Compensatory (Joint)": "compensatory_joint",
            "Blau Index (Gender)": "blaus_gender",
            "Blau Index (Race)": "blaus_race"
        }
        
        # Verify metrics exist in data
        available_metrics = {k: v for k, v in metric_options.items() if v in df.columns}
        if not available_metrics:
            st.error("No valid diversity metrics found in the data")
            st.stop()
            
        selected_metric_label = st.selectbox(
            "Select Diversity Metric", 
            list(available_metrics.keys())
        )
        selected_metric = available_metrics[selected_metric_label]
        
        # Carnegie Classification filter
        st.subheader("🏫 Institution Types")
        st.caption("Select institution classifications to include")
        
        # Only show checkboxes for columns that exist in data
        carnegie_selections = {}
        for label, col in carnegie_options.items():
            if col in df.columns:
                carnegie_selections[col] = st.checkbox(label, value=True)
            else:
                st.warning(f"Column '{col}' not found in data")

    # Apply filters
    filtered_df = df.copy()
    
    # Program Level Filter - updated to include "Other"
    if selected_level == "Undergraduate":
        filtered_df = filtered_df[filtered_df["level"] == "undergraduate"]
    elif selected_level == "Graduate":
        filtered_df = filtered_df[filtered_df["level"] == "graduate"]
    elif selected_level == "Other":
        filtered_df = filtered_df[~filtered_df["level"].isin(["undergraduate", "graduate"])]
    
    # State filter
    if selected_states:
        filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
    
    # Carnegie classification filter
    active_filters = [col for col, selected in carnegie_selections.items() if selected]
    if active_filters:
        mask = filtered_df[active_filters].any(axis=1)
        filtered_df = filtered_df[mask]

    # Check if we have data after filtering
    if filtered_df.empty:
        st.warning("No institutions match your filters. Please adjust your criteria.")
        st.stop()

    # Sorting and ranking
    filtered_df = filtered_df.sort_values(
        by=[selected_metric, "institution"], 
        ascending=[False, True]
    )
    filtered_df["rank"] = range(1, len(filtered_df) + 1)

    # Display results
    st.header(f"📊 Ranking by {selected_metric_label}")
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Institutions", len(filtered_df))
    with col2:
        avg_score = filtered_df[selected_metric].mean()
        st.metric("Average Score", f"{avg_score:.3f}")
    with col3:
        st.metric("Top Score", f"{filtered_df[selected_metric].max():.3f}")

    # Main dataframe display
    display_columns = [
        "rank", "institution", "city", "state",
        selected_metric, "percent_female", "percent_of_color",
        "total_students"
    ]
    
    display_df = filtered_df[display_columns].rename(columns={
        selected_metric: "diversity_score"
    })

    # Format the display
    st.dataframe(
        display_df,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "institution": st.column_config.TextColumn("Institution"),
            "city": st.column_config.TextColumn("City"),
            "state": st.column_config.TextColumn("State"),
            "diversity_score": st.column_config.NumberColumn(
                "Score",
                help="Diversity metric score (higher is better)",
                format="%.3f",
                width="small"
            ),
            "percent_female": st.column_config.NumberColumn(
                "% Female",
                format="%.1f%%",
                width="small"
            ),
            "percent_of_color": st.column_config.NumberColumn(
                "% Students of Color",
                format="%.1f%%",
                width="small"
            ),
            "total_students": st.column_config.NumberColumn(
                "Total Students",
                format="%,d",
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True,
        height=600
    )

    # Download option
    csv = display_df.to_csv(index=False)
    st.download_button(
        "💾 Download Results as CSV",
        data=csv,
        file_name=f"{selected_metric_label.lower().replace(' ', '_')}_rankings.csv",
        mime="text/csv",
        use_container_width=True
    )

    # Institution details expander
    with st.expander("🔍 View Detailed Institution Information"):
        selected_institution = st.selectbox(
            "Select Institution to View Details",
            options=sorted(filtered_df["institution"].unique())
        )
        
        inst_data = filtered_df[filtered_df["institution"] == selected_institution].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Demographic Information")
            st.metric("Total Students", f"{inst_data['total_students']:,}")
            st.metric("Male Students", f"{inst_data['male_students']:,} ({100-inst_data['percent_female']:.1f}%)")
            st.metric("Female Students", f"{inst_data['female_students']:,} ({inst_data['percent_female']:.1f}%)")
            st.metric("Students of Color", f"{inst_data['percent_of_color']:.1f}%")
            
        with col2:
            st.subheader("Institution Characteristics")
            categories = []
            for label, col in carnegie_options.items():
                if col in inst_data and inst_data[col] == 1:
                    categories.append(label.split(":")[0].strip())
            
            if categories:
                st.write("**Institution Classifications:**")
                for cat in categories:
                    st.write(f"- {cat}")
            else:
                st.write("No special classifications")
            
            st.write("**Diversity Scores:**")
            st.write(f"- Descriptive Gender: {inst_data['descriptive_gender']:.3f}")
            st.write(f"- Descriptive Race: {inst_data['descriptive_race']:.3f}")
            st.write(f"- Blau Gender Index: {inst_data['blaus_gender']:.3f}")
            st.write(f"- Blau Race Index: {inst_data['blaus_race']:.3f}")

    # Footer
    st.markdown(
        """
        <hr>
        <p style="text-align: center; font-size: 0.8em; color: gray;">
        <strong>© University of Connecticut</strong>
        </p>
        """,
        unsafe_allow_html=True
    )

    # Logo with dark background
    st.markdown(
        """
        <div style="background-color:#0a0a0a; padding:20px; text-align:center;">
            <img src="https://publicpolicy.media.uconn.edu/wp-content/uploads/sites/3091/2022/04/public-policy-stacked_white.png" 
                 alt="UConn Public Policy" style="max-width:300px;">
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()


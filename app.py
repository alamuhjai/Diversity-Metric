import streamlit as st
import pandas as pd
import json

# Load The Cleaned Dataset
@st.cache_data
def load_data():
    df = pd.read_csv("institutional_diversity_metric.csv")

    # Convert JSON strings to dictionaries
    if isinstance(df.loc[0, "gender_proportions"], str):
        df["gender_proportions"] = df["gender_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))
        df["race_proportions"] = df["race_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))

    # Calculate percentages
    df["percent_female"] = df["gender_proportions"].apply(lambda x: round(x.get("female", 0.0) * 100, 2))
    df["percent_of_color"] = df["race_proportions"].apply(lambda x: round((1.0 - x.get("white_nh", 0.0)) * 100, 2))

    return df

def main():
    st.set_page_config(layout="wide")
    st.title("🏛️ Institutional Diversity Ranking Tool")
    
    df = load_data()

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filter Options")
        
        # Program Level Filters
        st.subheader("🎓 Program Levels")
        show_total = st.checkbox("All Students (Total)", value=True)
        show_undergrad = st.checkbox("Undergraduate Programs", value=True)
        show_graduate = st.checkbox("Graduate Programs", value=True)
        show_doctoral = st.checkbox("Doctoral Programs (R2)", value=True)
        
        # State filter
        selected_states = st.multiselect(
            "Select States (optional)",
            options=sorted(df["state"].unique())
        )
        
        # Metric selector
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
        selected_metric_label = st.selectbox(
            "Diversity Metric to Rank By", 
            list(metric_options.keys())
        )
        selected_metric = metric_options[selected_metric_label]
        
        # Institution Type Filters
        st.subheader("🏫 Institution Types")
        inst_type_options = {
            "D/PU: Doctoral/Professional Universities": "D/PU",
            "Master's Colleges and Universities": "Masters",
            "Baccalaureate Colleges": "Baccalaureate",
            "Associate's Colleges": "Associates",
            "Special Focus Institutions": "SpecialFocus",
            "HBCUs": "HBCU"
        }
        
        inst_type_selections = {}
        for label, col in inst_type_options.items():
            inst_type_selections[col] = st.checkbox(label, value=True)

    # Apply filters
    filtered_df = df.copy()
    
    # Program Level Filters
    level_conditions = []
    if show_total:
        level_conditions.append(filtered_df["level"] == "total")
    if show_undergrad:
        level_conditions.append(filtered_df["level"] == "undergraduate")
    if show_graduate:
        level_conditions.append(filtered_df["level"] == "graduate")
    
    if level_conditions:
        filtered_df = filtered_df[pd.concat(level_conditions, axis=1).any(axis=1)]
    
    # Doctoral programs filter (R2)
    if show_doctoral:
        filtered_df = filtered_df[filtered_df["R2"] == 1]
    
    # State filter
    if selected_states:
        filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
    
    # Institution type filters
    active_inst_filters = [col for col, selected in inst_type_selections.items() if selected]
    if active_inst_filters:
        filtered_df = filtered_df[filtered_df[active_inst_filters].any(axis=1)]

    # Ensure selected metric exists
    if selected_metric not in filtered_df.columns:
        st.error(f"Error: The selected metric '{selected_metric}' is not available in the filtered data.")
        st.stop()

    # Drop rows with missing values for the selected metric
    filtered_df = filtered_df.dropna(subset=[selected_metric])

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
        "rank", "institution", "city", "state", "level",
        selected_metric, "percent_female", "percent_of_color",
        "total_students"
    ]
    
    display_df = filtered_df[display_columns].rename(columns={
        selected_metric: "diversity_score",
        "level": "program_level"
    })

    # Format the display
    st.dataframe(
        display_df,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "institution": st.column_config.TextColumn("Institution"),
            "city": st.column_config.TextColumn("City"),
            "state": st.column_config.TextColumn("State"),
            "program_level": st.column_config.TextColumn("Program Level"),
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
        file_name="diversity_rankings.csv",
        mime="text/csv",
        use_container_width=True
    )

if __name__ == "__main__":
    main()

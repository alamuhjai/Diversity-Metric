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

# Carnegie Classification Options
def get_carnegie_filters():
    return {
        "R1: Doctoral Universities – Very high research activity": "R1",
        "R2: Doctoral Universities – High research activity": "R2",
        "D/PU: Doctoral/Professional Universities": "D/PU",
        "Master's Colleges and Universities": "Masters",
        "Baccalaureate Colleges": "Baccalaureate",
        "Baccalaureate/Associate's Colleges": "BacAssoc",
        "Associate's Colleges": "Associates",
        "Special Focus Institutions": "SpecialFocus",
        "Tribal Colleges and Universities": "Tribal",
        "HBCU (Historically Black Colleges and Universities)": "HBCU",
        "Faith-Related Institutions": "FaithRelated",
        "Medical Schools & Centers": "MedicalHealth",
        "Engineering and Technology Schools": "EngineeringTech",
        "Business & Management Schools": "Business",
        "Arts, Music & Design Schools": "Arts",
        "Law Schools": "Law"
    }

# The Main App
def main():
    st.title("INSTITUTIONAL DIVERSITY RANKING")

    df = load_data()
    carnegie_options = get_carnegie_filters()

    st.sidebar.header("Filter & Ranking Options")

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

    selected_metric_label = st.sidebar.selectbox("Select Diversity Metric", list(metric_options.keys()))
    selected_metric = metric_options[selected_metric_label]

    # State filter
    selected_states = st.sidebar.multiselect(
        "Select States", options=sorted(df["state"].unique()), default=[])

    # Carnegie Classification filter
    st.sidebar.markdown("### Carnegie Classification Filters")
    carnegie_selections = {}
    
    for label, col in carnegie_options.items():
        carnegie_selections[col] = st.sidebar.checkbox(label, value=True)

    # Apply filters
    filtered_df = df.copy()
    
    # State filter
    if selected_states:
        filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]
    
    # Carnegie classification filter
    active_filters = [col for col, selected in carnegie_selections.items() if selected]
    if active_filters:
        # Create a condition where at least one of the selected classifications is True (1)
        condition = filtered_df[active_filters].any(axis=1)
        filtered_df = filtered_df[condition]

    # Drop missing metrics
    filtered_df = filtered_df.dropna(subset=[selected_metric])

    # Sorting and ranking
    filtered_df = filtered_df.sort_values(by=[selected_metric, "institution"], ascending=[False, True])
    filtered_df["rank"] = range(1, len(filtered_df) + 1)

    # Display table
    display_df = filtered_df[[
        "rank", "institution", "city", "state", selected_metric, 
        "percent_female", "percent_of_color", "level"
    ]].rename(columns={selected_metric: "diversity_score"})

    st.markdown(f"Top Institutions by {selected_metric_label}")
    st.dataframe(
        display_df.reset_index(drop=True),
        column_config={
            "diversity_score": st.column_config.NumberColumn(format="%.3f"),
            "percent_female": st.column_config.NumberColumn("% Female", format="%.1f%%"),
            "percent_of_color": st.column_config.NumberColumn("% Students of Color", format="%.1f%%")
        },
        use_container_width=True
    )

    # Download option
    csv = display_df.to_csv(index=False)
    st.download_button(
        "Download CSV", 
        csv, 
        file_name="diversity_rankings.csv", 
        mime="text/csv"
    )

if __name__ == "__main__":
    main()

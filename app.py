import streamlit as st
import pandas as pd
import json

# Load The Cleaned Dataset
@st.cache_data
def load_data():
    df = pd.read_csv("institutional_diversity_metric.csv")

    # Now working on the gender_proportions and race_proportions in actual dicts
    if isinstance(df.loc[0, "gender_proportions"], str):
        df["gender_proportions"] = df["gender_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))
        df["race_proportions"] = df["race_proportions"].apply(lambda x: json.loads(x.replace("'", '"')))

    # Now parsing the Female percentage and percentage Of Color (different types of colored people)
    df["percent_female"] = df["gender_proportions"].apply(lambda x: round(x.get("female", 0.0) * 100, 2))
    df["percent_of_color"] = df["race_proportions"].apply(lambda x: round((1.0 - x.get("white_nh", 0.0)) * 100, 2))

    return df

# The Main App
def main():
    st.title("INSTITUTIONAL DIVERSITY RANKING")

    df = load_data()

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

    # Filtering by state
    selected_states = st.sidebar.multiselect(
        "Select States ", options=sorted(df["state"].unique()), default=[])

    # Now applying the filtering
    filtered_df = df.copy()
    if selected_states:
        filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]

    # Dropping any missing metric
    filtered_df = filtered_df.dropna(subset=[selected_metric])

    # Sorting and ranking based on institution
    filtered_df = filtered_df.sort_values(by=[selected_metric, "institution"], ascending=[False, True])
    filtered_df["rank"] = range(1, len(filtered_df) + 1)

    # Table for displaying the results
    display_df = filtered_df[[
        "rank", "institution", "city", "state", selected_metric, "percent_female", "percent_of_color"
    ]].rename(columns={selected_metric: "diversity_score"})

    st.markdown(f"Top Institutions by {selected_metric_label}")
    st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

    # Option for downloading. you can remove if you
    # don't users to download results
    csv = display_df.to_csv(index=False)
    st.download_button("Download CSV", csv, file_name="diversity_rankings.csv", mime="text/csv")


if __name__ == "__main__":
    main()

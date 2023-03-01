import altair as alt
import pandas as pd
import streamlit as st

from views.cancer_view import generate_cancer_view
from views.chromosome_view import generate_chromosome_view
from views.protein_view import generate_protein_view


site_configuration = {
    "page_title": "GCapricorn",
    "page_icon": "res/favicon.ico",
    "layout": "wide"
}

# TODO: Add all available protein protein_classes, sorted by priority.
# The class with the highest priority will be the one chosen for the protein as its class.
protein_class_priority = [
    "Enzymes",
    "Transporters"
]

with open("stylesheet.css") as stylesheet:
    site_style = f"<style>{stylesheet.read()}</style>"


def generate_prognostic_data(row: pd.Series, prognostic_type: str) -> str:
    """
    Generate a prognostics value for a given protein.
    :param row: A Human Protein Atlas entry. Must contain prognostics information in different cancer columns.
    :param prognostic_type: one of "favorable" or "unfavorable".
    :return: A comma-separated string containing all the cancer types for
    which the protein has a prognostic_type prognostic.
    """
    prognostic_fields = row[pd.Series(row.index).apply(lambda x: "Pathology prognostics" in x).values]
    prognostics_row = row[prognostic_fields.index]
    prognostics = prognostics_row[prognostics_row.apply(lambda x: prognostic_type in str(x).lower().split())].index
    return ",".join(map(lambda x: x.split("-")[1].strip(), prognostics))


def prioritize_protein_class(protein_classes: str, priority_list: list[str] = None) -> list[str]:
    """
    Get a list of prioritized protein classes from a comma-separated string of protein classes.
    :param protein_classes: Protein classes in a comma-separated format.
    :param priority_list: list of prioritized protein classes.
    :return: The primary protein class as a string.
    """

    if priority_list is None:
        priority_list = protein_class_priority

    class_list = [x.strip() for x in protein_classes.split(",")]
    prioritized_protein_classes = [x for x in priority_list if x in class_list]
    if prioritized_protein_classes:
        return prioritized_protein_classes
    return class_list


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load the Human Protein Atlas (HPA) DataFrame and prepare the data.
    :return: the tidy DataFrame containing HPA data
    """
    data = pd.read_csv("https://www.proteinatlas.org/download/proteinatlas.tsv.zip", compression="zip", sep="\t")
    data["Favorable prognostics"] = data.apply(lambda row: generate_prognostic_data(row, prognostic_type="favorable"), axis=1)
    data["Unfavorable prognostics"] = data.apply(lambda row: generate_prognostic_data(row, prognostic_type="unfavorable"), axis=1)
    data.dropna(subset=["Uniprot"], inplace=True)
    data["Prioritized Protein Class"] = data["Protein class"].apply(prioritize_protein_class)
    return data


def main():

    st.set_page_config(**site_configuration)
    st.markdown(site_style, unsafe_allow_html=True)

    alt.themes.enable("urbaninstitute")

    st.title("GCapricorn")

    data = load_data()
    st.session_state["unfiltered_data"] = data
    st.session_state["data"] = data

    protein_classes = [x.split(", ") for x in data["Protein class"]]
    protein_classes = [item for sublist in protein_classes for item in sublist]
    protein_classes = list(set(protein_classes))

    left, right = st.columns(2)
    protein_selection = right.multiselect(label="Select Protein Classes", options=protein_classes, default=["Enzymes"])
    st.session_state["protein_selection"] = protein_selection
    cancer_types = map(lambda x: x.split("-")[1].strip(),
                       filter(lambda x: "Pathology prognostics" in x, data.columns))
    cancer_selection = left.selectbox(label="Select Cancer Type", options=cancer_types, index=0)
    st.session_state["cancer_selection"] = cancer_selection

    # Horizontal 2 + 1 layout
    top_panel = st.container()
    view1, view2 = top_panel.columns(2)
    view3 = st.container()

    with view1:
        generate_cancer_view()

    with view2:
        generate_chromosome_view()

    with view3:
        generate_protein_view()


if __name__ == "__main__":
    main()

import os
import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from annotated_text import annotated_text

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="NER Knowledge Base", layout="wide")

st.title("Zero-Shot NER & Knowledge Base System")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Dashboard", "Inference", "Knowledge Base", "Settings"]
)


def get_categories():
    try:
        response = requests.get(f"{API_URL}/categories/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return []


def get_entities():
    try:
        response = requests.get(f"{API_URL}/entities/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return []


with tab1:
    st.header("Dashboard & Overview")
    categories = get_categories()
    cat_names = [c["name"] for c in categories]

    if not cat_names:
        st.info("No categories found. Please add them in Settings.")
    else:
        selected_cat = st.selectbox("Select Category for Word Cloud", cat_names)

        if selected_cat:
            cat_obj = next(c for c in categories if c["name"] == selected_cat)
            entities = get_entities()
            cat_entities = [e for e in entities if e["category_id"] == cat_obj["id"]]

            if not cat_entities:
                st.info(f"No entities found for category '{selected_cat}'.")
            else:
                freq_dict = {}
                for e in cat_entities:
                    try:
                        overview = requests.get(
                            f"{API_URL}/entities/{e['id']}/overview"
                        ).json()
                        count = overview.get("documents_count", 0)
                        freq_dict[e["text"]] = count if count > 0 else 1
                    except Exception:
                        freq_dict[e["text"]] = 1

                wordcloud = WordCloud(
                    width=800, height=400, background_color="white"
                ).generate_from_frequencies(freq_dict)

                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

with tab2:
    st.header("Text Inference")
    input_text = st.text_area("Enter text to analyze", height=200)
    if st.button("Analyze"):
        if input_text.strip():
            with st.spinner("Extracting entities..."):
                try:
                    res = requests.post(
                        f"{API_URL}/analyze/", json={"text": input_text}
                    )
                    res.raise_for_status()
                    data = res.json()
                    extracted = data.get("extracted_entities", [])
                    predictions = data.get("predictions", [])

                    st.subheader("Highlighted Text")

                    annotations = []
                    last_idx = 0
                    for p in sorted(predictions, key=lambda x: x["start"]):
                        if p["start"] >= last_idx:
                            annotations.append(input_text[last_idx : p["start"]])
                            annotations.append((p["text"], p["label"], "#8ef"))
                            last_idx = p["end"]
                    annotations.append(input_text[last_idx:])
                    if annotations:
                        annotated_text(*annotations)
                    else:
                        st.write(input_text)

                    st.subheader("Extracted Entities")
                    if extracted:
                        df_ext = pd.DataFrame(
                            [
                                {"Text": e["text"], "Category": e["category"]}
                                for e in extracted
                            ]
                        )
                        st.dataframe(df_ext)

                        st.success(
                            f"Found {len(extracted)} entities and saved text to database."
                        )
                    else:
                        st.info("No entities found.")
                except Exception as e:
                    st.error(f"Error analyzing text: {e}")
        else:
            st.warning("Please enter some text.")

with tab3:
    st.header("Knowledge Base")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Search Entity")
        all_entities = get_entities()
        entity_texts = [e["text"] for e in all_entities]
        search_q = st.selectbox("Select or type an entity", [""] + entity_texts)

        if search_q:
            ent = next((e for e in all_entities if e["text"] == search_q), None)
            if ent:
                try:
                    info = requests.get(
                        f"{API_URL}/entities/{ent['id']}/overview?generate_explanation=true"
                    ).json()
                    st.write(f"**Category:** {info.get('category')}")
                    st.write(f"**Explanation:** {info.get('explanation')}")
                    st.write(
                        f"**Appears in {info.get('documents_count', 0)} documents.**"
                    )
                    with st.expander("View Related Documents"):
                        for d in info.get("documents", []):
                            st.markdown(f"> {d}")
                except Exception as e:
                    st.error(f"Error fetching entity overview: {e}")

    with col2:
        st.subheader("Manage Entities")
        with st.form("add_entity_form"):
            new_ent_text = st.text_input("Entity Text")
            categories = get_categories()
            cat_names = [c["name"] for c in categories]
            if not cat_names:
                cat_names = ["Default"]

            new_ent_cat = st.selectbox("Category", cat_names)
            new_ent_exp = st.text_area("Explanation (optional)")
            submitted = st.form_submit_button("Add Entity")

            if submitted and new_ent_text.strip():
                try:
                    res = requests.post(
                        f"{API_URL}/entities/",
                        json={
                            "text": new_ent_text,
                            "category_name": new_ent_cat,
                            "explanation": new_ent_exp,
                        },
                    )
                    res.raise_for_status()
                    st.success(f"Added '{new_ent_text}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding entity: {e}")

        st.divider()
        st.write("Delete Entity")
        del_ent = st.selectbox(
            "Select entity to delete", [""] + entity_texts, key="del_ent"
        )
        if st.button("Delete"):
            if del_ent:
                ent_to_del = next(
                    (e for e in all_entities if e["text"] == del_ent), None
                )
                if ent_to_del:
                    try:
                        requests.delete(f"{API_URL}/entities/{ent_to_del['id']}")
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting entity: {e}")

with tab4:
    st.header("Settings & Categories")

    categories = get_categories()
    cat_names = [c["name"] for c in categories]

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Existing Categories")
        if categories:
            for c in categories:
                st.write(f"- {c['name']}")
        else:
            st.write("None")

        st.divider()

        st.write("### Delete Category")
        del_cat = st.selectbox(
            "Select category to delete", [""] + cat_names, key="del_cat"
        )
        if st.button("Delete Category"):
            if del_cat:
                cat_to_del = next((c for c in categories if c["name"] == del_cat), None)
                if cat_to_del:
                    try:
                        requests.delete(f"{API_URL}/categories/{cat_to_del['id']}")
                        st.success(f"Deleted category '{del_cat}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting category: {e}")
            else:
                st.warning("Please select a category to delete.")

    with col2:
        st.write("### Add New Category")
        with st.form("add_cat_form"):
            new_cat_name = st.text_input("Category Name")
            auto_scan = st.checkbox("Auto-scan existing texts for this new category")
            cat_submitted = st.form_submit_button("Add Category")

            if cat_submitted and new_cat_name.strip():
                try:
                    res = requests.post(
                        f"{API_URL}/categories/", json={"name": new_cat_name.strip()}
                    )
                    res.raise_for_status()
                    new_cat = res.json()
                    st.success(f"Category '{new_cat['name']}' added.")

                    if auto_scan:
                        with st.spinner(
                            f"Scanning existing texts for '{new_cat['name']}' in the background..."
                        ):
                            scan_res = requests.post(
                                f"{API_URL}/categories/rescan",
                                json={"category_id": new_cat["id"]},
                            )
                            scan_res.raise_for_status()
                            msg = scan_res.json().get("message", "Scan started.")
                        st.success(f"Scan initiated: {msg}")

                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding category: {e}")

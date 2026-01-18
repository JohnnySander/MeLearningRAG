
import streamlit as st

import site_scraper as scraper


def run_ui():
    st.title("Scraper Runner")

    st.write("Enter site details and call `scraper.main()`.")

    site = st.text_input("Site name (required)")
    url = st.text_input("URL (required)")
    pattern = st.text_input("Search pattern (optional)")

    if st.button("Run scraper"):
        # Check if site and URL are provided on button click
        if not site or not url:
            st.error("Both Site name and URL are required to run the scraper.")
            return

        with st.spinner("Loading scraper and running... This can take a while."):
            try:
                # If user left pattern empty, let scraper use its default behavior
                call_pattern = pattern if pattern and pattern.strip() else "*"
                scraper.main(site, url, call_pattern)
                st.success("Scraper finished successfully.")
            except Exception as e:
                st.error("Scraper raised an exception. See details below.")
                st.exception(e)


if __name__ == "__main__":
    run_ui()

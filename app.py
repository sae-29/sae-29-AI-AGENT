import streamlit as st
import pandas as pd
import requests
from typing import List, Dict
import time
import json
from openai import OpenAI
from groq import Groq
import anthropic
import backoff
import os
from error_handlers import ErrorHandler

# Constants
SERPAPI_KEY = '0a4b79c3eb006497669c6d0a6dd825c7dfa2939f8f8ed9f901607ff2aa2ff5fb'
GROQ_API_KEY = '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'
ANTHROPIC_API_KEY = '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'

# LLM Providers
class LLMProvider:
    def __init__(self, api_key: str, provider: str):
        self.provider = provider
        self.api_key = api_key
        self.setup_client()

    def setup_client(self):
        try:
            if self.provider == "groq":
                self.client = Groq(api_key=self.api_key)
            elif self.provider == "anthropic":
                self.client = anthropic.Client(api_key=self.api_key)
        except Exception as e:
            st.error(f"Failed to initialize {self.provider} client: {str(e)}")
            raise

    @ErrorHandler.handle_api_error
    @ErrorHandler.retry_with_backoff(max_retries=3, initial_delay=1.0)
    def get_completion(self, prompt: str) -> str:
        if self.provider == "groq":
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are a precise information extractor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-instant-1p1-small-v2",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            if response and response.content:
                return response.content[0].text
            else:
                print("Empty API response")
                return None

# Entity Search Extractor
class EntitySearchExtractor:
    def __init__(self, serpapi_key: str, llm_provider: LLMProvider):
        self.serpapi_key = serpapi_key
        self.llm_provider = llm_provider
        self.search_delay = 1

    @ErrorHandler.handle_api_error
    @ErrorHandler.retry_with_backoff(max_retries=3, initial_delay=1.0)
    def search_entity(self, entity: str, search_prompt: str) -> Dict:
        url = "https://serpapi.com/search"
        params = {
            "api_key": self.serpapi_key,
            "q": search_prompt.format(entity=entity),
            "engine": "google",
            "num": 5
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        search_results = response.json()
        organic_results = search_results.get("organic_results", [])
        processed_results = []

        for result in organic_results:
            processed_results.append({
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "link": result.get("link", ""),
            })

        return {
            "entity": entity,
            "results": processed_results
        }

    @ErrorHandler.handle_api_error
    def extract_information(self, search_results: Dict, extraction_prompt: str) -> Dict:
        context = "\n\n".join([
            f"Title: {result['title']}\nSnippet: {result['snippet']}\nURL: {result['link']}"
            for result in search_results["results"]
        ])

        prompt = f"""
        {extraction_prompt}

        Entity: {search_results['entity']}

        Search Results:
        {context}

        Please extract the requested information. If the information is not found, respond with "Not found".
        Format the response as a concise, direct answer without explanations.
        """

        extracted_info = self.llm_provider.get_completion(prompt)

        return {
            "entity": search_results["entity"],
            "extracted_info": extracted_info,
            "source_urls": [result["link"] for result in search_results["results"]]
        }

def main():
    st.set_page_config(page_title="AI Agent", layout="wide")

    # Page Layout
    col1, col2 = st.columns((2, 1))
    with col1:
        st.title("🤖 AI AGENT")
        st.subheader("Entity Information Extractor")
    with col2:
        st.image("https://example.com/ai-agent-logo.png", width=100)

    # Main Interface
    with st.container():
        llm_provider_option = st.selectbox(
            "🔧 Select LLM Provider:",
            ["Groq", "Anthropic"],
            help="Choose your preferred LLM provider"
        )

        uploaded_file = st.file_uploader("📁 Upload CSV file", type="csv")

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)

                st.subheader("📊 Data Preview")
                st.dataframe(df.head(), use_container_width=True)

                main_column = st.selectbox("🎯 Select the column containing entities:", df.columns)

                with st.expander("🔍 Advanced Settings"):
                    search_prompt = st.text_input(
                        "Search Prompt Template:",
                        "Contact information for {entity} company",
                        help="Use {entity} as a placeholder for the entity name"
                    )

                    extraction_prompt = st.text_area(
                        "Extraction Prompt:",
                        "Extract the email address and phone number for this company."
                    )

                # Initialize LLM Provider
                if llm_provider_option == "Groq":
                    llm_api_key = GROQ_API_KEY
                    provider = "groq"
                else:
                    llm_api_key = ANTHROPIC_API_KEY
                    provider = "Anthropic"

                llm_provider = LLMProvider(llm_api_key, provider)
                extractor = EntitySearchExtractor(SERPAPI_KEY, llm_provider)

                if st.button("🚀 Extract Information"):
                    try:
                        # Progress tracking
                        progress_col, metrics_col = st.columns(2)
                        with progress_col:
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                        results_container = st.container()

                        all_results = []
                        entities = df[main_column].unique()
                        total_entities = len(entities)
                        successful_extractions = 0

                        with st.spinner("🔄 Processing entities..."):
                            for idx, entity in enumerate(entities):
                                progress = (idx + 1) / total_entities
                                progress_bar.progress(progress)
                                status_text.text(f"Processing {entity} ({idx + 1}/{total_entities})")

                                try:
                                    search_results = extractor.search_entity(entity, search_prompt)
                                    time.sleep(extractor.search_delay)

                                    if search_results["results"]:
                                        extraction_results = extractor.extract_information(
                                            search_results,
                                            extraction_prompt
                                        )
                                        all_results.append(extraction_results)

                                        if "Error" not in extraction_results["extracted_info"]:
                                            successful_extractions += 1

                                except Exception as e:
                                    ErrorHandler.display_error(
                                        st.empty(),
                                        f"Error processing {entity}: {str(e)}",
                                        "warning"
                                    )
                                    continue

                        if all_results:
                            st.markdown("""
                                <div class="success-message">
                                    ✅ Processing completed successfully!
                                </div>
                            """, unsafe_allow_html=True)

                            results_df = pd.DataFrame(all_results)

                            # Display results in tabs
                            tab1, tab2 = st.tabs(["📊 Results Table", "📈 Analytics"])

                            with tab1:
                                st.dataframe(results_df, use_container_width=True)

                                csv = results_df.to_csv(index=False)
                                st.download_button(
                                    "⬇️ Download Results CSV",
                                    csv,
                                    "extracted_information.csv",
                                    "text/csv",
                                    key='download-csv'
                                )

                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")

            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

if __name__ == "__main__":
    main()
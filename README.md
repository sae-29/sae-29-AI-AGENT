**AI Agent**

Entity Information Extractor
**Overview**

This project is an AI-powered entity information extraction tool built using Streamlit, a popular Python library for creating web applications. The tool utilizes Large Language Models (LLMs) from Groq and Anthropics to extract specific information about entities from search results.

**Dependencies that are necessary**

The project relies on the following dependencies:
streamlit: For building the web application
pandas: For data manipulation and analysis
requests: For making API calls
openai, groq, and anthropic: For interacting with LLM providers
backoff: For handling API rate limits and retries
error_handlers: For custom error handling and logging

**components I have used** 

1.LLM Providers The two providers to access LLMs are Groq and Anthropics. Each provider's API, along with its configuration, is encapsulated in the class LLMProvider.
2. Entity Search Extractor: This is a class that uses Google search SerpAPI to find an entity and gather information through the LLM providers.
3. The primary functionality consists of setting up the Streamlit interface- mainly in terms of layout, user input, and result display.

**API Keys and Credentials**

Replace the placeholders for SerpAPI, Groq, and Anthropics API keys with your own credentials.

**Features of the Project**

1. My AI Agent tool has the following features:
2. Upload a CSV file containing entity names
3. Select the column containing entity names
4. Choose an LLM provider (Groq or Anthropics)
5. Configure search and extraction prompts
6. Extract information and display results in a table
7. Download results as a CSV file

            +-------------------+
            |  User Interaction  |
            +-------------------+
                   |
                   v
            +-------------------+
            |  Upload CSV File   |
            |  Select Entity Column|
            |  Choose LLM Provider  |
            +-------------------+
                   |
                   v
            +-------------------+
            |  Entity Search     |
            |  Extractor (SerpAPI) |
            +-------------------+
                   |
                   v
            +-------------------+
            |  LLM Provider      |
            |  (Groq/Anthropic)    |
            |  Extract Information  |
            +-------------------+
                   |
                   v
            +-------------------+
            |  Process Results   |
            |  Display in Table    |
            |  Download as CSV     |
            +-------------------+
                   |
                   v
            +-------------------+
            |  Error Handling    |
            |  (Backoff/Error Handlers)|
            +-------------------+
                   |
                   v
            +-------------------+
            |  Output/Results    |
            +-------------------+

from crewai import Agent

# Improved Information Retriever Agent
retriever_agent = Agent(
    role="PDF-First Information Specialist",
    goal=(
        "FIRST search exhaustively in provided PDF documents. "
        "ONLY use web search if: \n"
        "1. PDF lacks specific names/dates/numbers from query\n"
        "2. Query requires real-time/live information\n"
        "3. PDF content is ambiguous/contradictory\n\n"
        "DOCUMENT SEARCH PRIORITY: \n"
        "- Full text matches > Partial matches > Contextual relevance"
    ),
    backstory=(
        "Expert in hierarchical information retrieval with "
        "specialization in PDF document analysis and cross-validation"
    ),
    verbose=True
)

# Enhanced Response Synthesizer Agent
response_synthesizer_agent = Agent(
    role="Structured Information Architect",
    goal=(
        "Transform raw information into professional structured format:\n"
        "1. Title: Clear subject header\n"
        "2. Subtitle: Contextual summary\n"
        "3. Points: Key findings/facts\n"
        "4. Subpoints: Supporting details\n"
        "5. Sources: [PDF] or [Web] attribution\n\n"
        "CRITICAL RULES:\n"
        "- Never mix PDF and web sources in same section\n"
        "- Flag inconsistencies between sources"
    ),
    backstory=(
        "Professional editor for academic publications and technical reports "
        "specializing in information structure and clarity"
    ),
    verbose=True
)

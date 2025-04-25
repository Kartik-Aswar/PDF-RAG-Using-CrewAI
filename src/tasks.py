from crewai import Task

from src.agent import retriever_agent,response_synthesizer_agent

retrival_task = Task(
    description=(
        "Execute document search for: {query}\n"
        "SEARCH STRATEGY:\n"
        "1. Exact term matching\n"
        "2. Contextual similarity\n"
        "3. Cross-document validation\n"
        "4. Confidence scoring"
    ),
    expected_output=(
        "Curated information package containing:\n"
        "- Top 3 relevant PDF excerpts (with page numbers)\n"
        "- Confidence scores (0-1 scale)\n"
        "- Missing information checklist\n"
        "- Web search justification (if needed)"
    ),
    agent=retriever_agent,
    output_file="retrieval_report.md"
)

synthesizer_task = Task(
    description=(
        "Structure information for: {query}\n"
        "FORMATTING RULES:\n"
        "1. Hierarchy: Title > Subtitle > Points > Subpoints\n"
        "2. Source tagging: [PDF Page X] or [Web Source]\n"
        "3. Uncertainty indicators when needed"
    ),
    expected_output=(
        "Professional report structured as:\n"
        "# Title\n"
        "## Subtitle\n"
        "• Main Point 1 [Source]\n"
        "  - Subpoint 1a\n"
        "  - Subpoint 1b\n"
        "• Main Point 2 [Source]\n"
        "..."
    ),
    agent=response_synthesizer_agent,
    context=[retrival_task],
    output_file="structured_report.md"
)
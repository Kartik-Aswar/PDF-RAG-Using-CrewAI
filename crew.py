from crewai import Crew, Agent, Task, Process

from src.agent import retriever_agent, response_synthesizer_agent
from src.tasks import synthesizer_task, retrival_task 
import os
from crewai import LLM



llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7
    )

class Agentic_rag:
    def __init__(self,pdf_tool, web_search_tool):
        self.pdf_tool = pdf_tool
        
        self.web_search_tool = web_search_tool
        self.tasks = [retrival_task, synthesizer_task]

    def crew(self, llm=None) -> Crew:
        # Assign LLM dynamically
        retriever_agent.llm = llm
        response_synthesizer_agent.llm = llm

        # Attach tools
        retriever_agent.tools = [self.pdf_tool, self.web_search_tool]

        return Crew(
            agents=[retriever_agent, response_synthesizer_agent],
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            llm=llm  
        )


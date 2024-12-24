from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
###fix this
llm = ChatOpenAI(temperature=0)

class GradeHallucinations(BaseModel):
    """assessment for hallucinations in the analysis."""
    grounded: bool = Field(description="Whether the analysis is grounded in the provided data.")
    explanation: str = Field(description="Reason for the decision.")

structured_llm_grader = llm.with_structured_output(GradeHallucinations)

system_message = """You are a financial manager assessing whether an LLM generation is grounded in and supported by a set of provided facts and context. 
Consider the junior datasets, the team's focus area, and the senior's expected output when deciding.
Provide an explanation of your decision."""

grading_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        (
            "human",
            """Context:
Focus Area: {focus_area}
Expected Output: {expected_output}

Junior Datasets:
{junior_datasets}

Team Outputs:
{team_outputs}

LLM Generation:
{generation}

Is the generation grounded in facts?""",
        ),
    ]
)

hallucination_grader_chain: RunnableSequence = grading_prompt | structured_llm_grader






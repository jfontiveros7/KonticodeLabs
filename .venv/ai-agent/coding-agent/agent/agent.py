import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

# Initialize the language model
llm = ChatOpenAI(
    temperature=0.7,
    api_key=openai_api_key,
    model="gpt-4o-mini"
)

def generate_code(description):
    """Generate Python code based on description."""
    prompt = f"Write Python code for the following requirement:\n{description}"
    message = llm.invoke([{"role": "user", "content": prompt}])
    return message.content

def explain_code(code):
    """Explain what the given code does."""
    prompt = f"Explain the following code in detail:\n{code}"
    message = llm.invoke([{"role": "user", "content": prompt}])
    return message.content

def refactor_code(code):
    """Refactor code to improve readability and efficiency."""
    prompt = f"Refactor the following code to improve readability and efficiency:\n{code}"
    message = llm.invoke([{"role": "user", "content": prompt}])
    return message.content

def run_agent(user_input, task_type="generate"):
    """Run the coding agent with user input and task type."""
    if task_type == "generate":
        return generate_code(user_input)
    elif task_type == "explain":
        return explain_code(user_input)
    elif task_type == "refactor":
        return refactor_code(user_input)
    else:
        return generate_code(user_input)
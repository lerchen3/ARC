import json
from openai import OpenAI
from dotenv import load_dotenv
from FSP_DATA.observation_questioning import FSP_RAW
import re
load_dotenv()

QUESTIONING_GEN_TEMP = 0.7

def generate_questioning_prompt(observation: str) -> list[dict]:
    """
    Generate a prompt for creating questions about an observation.
    
    Parameters:
    ----------
    observation: str
        The observation to generate questions about
        
    Returns:
    -------
        An OpenAI message history.
    """
    content = (
        "Given this observation about a grid transformation, generate specific questions "
        "that would help verify or refute different aspects of the observation. Focus on "
        "questions that can lead to concrete, verifiable patterns.\n\n"
        f"Observation: {observation}\n\n"
        "Generate questions that break down the observation into testable components. "
        "Each question should focus on a specific aspect that could be verified through "
        "examination of the grid transformations."
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(fsp_data: list[dict]) -> list[dict]:
    """Generate FSP context for questioning observations."""
    system_prompt = (
        "You are an expert at analyzing grid transformations and breaking down "
        "observations into specific, testable questions. Your goal is to generate "
        "questions that help verify or refute different aspects of an observation "
        "and lead to concrete, verifiable patterns."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_questioning_prompt(example['observation'])
        )
        messages.append({
            "role": "assistant",
            "content": json.dumps(example['questions'])
        })
    
    return messages

FSP_CONTEXT = generate_fsp_context(FSP_RAW)

def generate_questions(
    client: OpenAI,
    observation: str,
    num_questions: int = 5,
    verbose: bool = False
) -> list[str]:
    """Generate questions for an observation."""
    messages = []
    messages.extend(FSP_CONTEXT)
    messages.extend(generate_questioning_prompt(observation))

    if verbose:
        print("Messages:")
        from pprint import pprint
        pprint(messages)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=QUESTIONING_GEN_TEMP
    )

    questions = []
    if verbose:
        print("Responses:")
    for response in completion.choices:
        response_content = response.message.content
        if verbose:
            print(response_content)
        for line in response_content.split('\n'):
            # Match numbered questions (e.g., "1. What is...?" or "1) What is...?")
            match = re.match(r'^\s*(\d+)[\.\)]\s*(.+)$', line)
            if match:
                questions.append(match.group(2))

    if verbose:
        print("\nExtracted Questions:")
        pprint(questions)
        
    return questions[:num_questions]

def main():
    """Test the questioning system."""
    client = OpenAI()
    
    test_observation = (
        "**Pattern Consistency**: The final pattern in each sequence preserves some "
        "spatial characteristics of the initial pattern. This suggests that the "
        "transformation rule might involve a local duplication or scaling within "
        "each block of the original grid."
    )
    
    questions = generate_questions(
        client=client,
        observation=test_observation,
        verbose=True
    )
    
    print("\nGenerated Questions:")
    print("-------------------")
    for i, question in enumerate(questions, 1):
        print(f"{i}. {question}")

if __name__ == "__main__":
    main()
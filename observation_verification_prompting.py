import json
from openai import OpenAI
from typing import List, Dict, Union
from dotenv import load_dotenv
from prompting_utils import grid_to_python_literal

load_dotenv()

CODE_VERIFIER_GEN_TEMP = 0.8

# Example FSP data for verification
FSP_RAW = [
    {
        "file_path": "arc-agi_training_challenges.json",
        "task_id": "007bbfb7",
        "input_grid": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        "output_grid": [[0, 2, 0], [2, 0, 2], [0, 2, 0]],
        "observation": "All blue pixels (color 1) are replaced with red pixels (color 2)",
        "verification_code": """
def verify(input_grid, output_grid):
    import numpy as np
    input_arr = np.array(input_grid)
    output_arr = np.array(output_grid)
    return np.all((input_arr == 1) == (output_arr == 2))
"""
    }
]

def generate_verification_prompt(
    observation: str,
    input_grid: List[List[int]],
    output_grid: List[List[int]]
) -> list[dict]:
    """Generate a prompt for creating verification code."""
    content = (
        "Generate Python code to verify this observation about a grid transformation:\n"
        f"Observation: {observation}\n\n"
        f"Input grid:\n{grid_to_python_literal(input_grid)}\n\n"
        f"Output grid:\n{grid_to_python_literal(output_grid)}\n\n"
        "Write a function named 'verify' that takes input_grid and output_grid as parameters "
        "and returns True if the observation holds, False otherwise. Use numpy if needed."
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(fsp_data: list[dict]) -> list[dict]:
    system_prompt = (
        "You are an expert Python programmer specializing in grid transformation verification. "
        "Your task is to write precise verification functions that test specific observations "
        "about grid transformations."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_verification_prompt(
                example['observation'],
                example['input_grid'],
                example['output_grid']
            )
        )
        messages.append({
            "role": "assistant",
            "content": example['verification_code']
        })
    
    return messages

FSP_CONTEXT = generate_fsp_context(FSP_RAW)

def generate_verification_code(
    client: OpenAI,
    observation: str,
    input_grid: List[List[int]],
    output_grid: List[List[int]],
    verbose: bool = False
) -> str:
    """Generate verification code for an observation."""
    messages = []
    messages.extend(FSP_CONTEXT)
    messages.extend(generate_verification_prompt(observation, input_grid, output_grid))

    if verbose:
        print("Messages:")
        from pprint import pprint
        pprint(messages)

    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        max_tokens=1024,
        temperature=CODE_VERIFIER_GEN_TEMP
    )

    return completion.choices[0].message.content

def verify_observation(
    verification_code: str,
    input_grid: List[List[int]],
    output_grid: List[List[int]]
) -> bool:
    """Execute verification code and return result."""
    try:
        local_vars = {}
        exec(verification_code, {}, local_vars)
        verify_func = local_vars['verify']
        return verify_func(input_grid, output_grid)
    except Exception as e:
        print(f"Error executing verification code: {e}")
        return False

def process_and_verify_observations(
    client: OpenAI,
    observations: List[str],
    input_grid: List[List[int]],
    output_grid: List[List[int]],
    verbose: bool = False
) -> Dict[str, bool]:
    """Process and verify multiple observations."""
    results = {}
    for observation in observations:
        verification_code = generate_verification_code(
            client, observation, input_grid, output_grid, verbose
        )
        result = verify_observation(verification_code, input_grid, output_grid)
        results[observation] = result
    return results

def main():
    """Test the verification system with task 00d62c1b."""
    from task import get_task
    
    client = OpenAI()
    task = get_task('arc-agi_training_challenges.json', '00d62c1b')
    
    input_grid = task.train[0]['input']
    output_grid = task.train[0]['output']
    
    test_observations = [
        "The grid dimensions double in both width and height",
        "Each 2x2 block in the output contains exactly one colored cell"
    ]
    
    results = process_and_verify_observations(
        client=client,
        observations=test_observations,
        input_grid=input_grid,
        output_grid=output_grid,
        verbose=True
    )
    
    print("\nVerification Results:")
    print("--------------------")
    for obs, result in results.items():
        print(f"Observation: {obs}")
        print(f"Verified: {'✓' if result else '✗'}\n")

if __name__ == "__main__":
    main()

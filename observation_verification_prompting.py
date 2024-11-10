import json
from openai import OpenAI
from typing import List, Dict, Union
from dotenv import load_dotenv
from prompting_utils import grid_to_python_literal
from FSP_DATA.verification_regular import FSP_RAW_REGULAR
from FSP_DATA.verification_difficult import FSP_RAW_DIFFICULT

load_dotenv()

VERIFICATION_GEN_TEMP = 1.0

def generate_verification_prompt(
    observation: str,
    input_grid: List[List[int]],
    output_grid: List[List[int]],
    difficult_to_verify: bool = False
) -> list[dict]:
    """Generate a prompt for creating verification code."""
    base_content = (
        "Generate Python code to verify this observation about a grid transformation:\n"
        f"Observation: {observation}\n\n"
        f"Input grid:\n{grid_to_python_literal(input_grid)}\n\n"
        f"Output grid:\n{grid_to_python_literal(output_grid)}\n\n"
    )
    
    if difficult_to_verify:
        content = (
            "This observation is particularly complex and challenging to verify. "
            "As a top-tier Python expert, I need you to implement a robust and precise "
            "verification function that handles all edge cases.\n\n"
        ) + base_content
    else:
        content = base_content
        
    content += (
        "Write a function named 'verify' that takes input_grid and output_grid as parameters "
        "and returns True if the observation holds, False otherwise. Use numpy if needed."
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(
    fsp_data_regular: list[dict],
    fsp_data_difficult: list[dict],
    difficult_to_verify: bool = False
) -> list[dict]:
    system_prompt = (
        "You are an expert Python programmer specializing in grid transformation verification. "
    )
    
    if difficult_to_verify:
        system_prompt += (
            "You excel at implementing complex verification logic for challenging "
            "observations that require sophisticated algorithmic approaches. "
            "Your code should be both precise and comprehensive."
        )
        fsp_data = fsp_data_difficult
    else:
        fsp_data = fsp_data_regular
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_verification_prompt(
                example['observation'],
                example['input_grid'],
                example['output_grid'],
                difficult_to_verify
            )
        )
        messages.append({
            "role": "assistant",
            "content": example['verification_code']
        })
    
    return messages

def generate_verification_code(
    client: OpenAI,
    observation: str,
    input_grid: List[List[int]],
    output_grid: List[List[int]],
    difficult_to_verify: bool = False,
    verbose: bool = False
) -> str:
    """Generate verification code for an observation."""
    messages = []
    messages.extend(generate_fsp_context(
        fsp_data_regular=FSP_RAW_REGULAR,
        fsp_data_difficult=FSP_RAW_DIFFICULT,
        difficult_to_verify=difficult_to_verify
    ))
    messages.extend(
        generate_verification_prompt(
            observation,
            input_grid,
            output_grid,
            difficult_to_verify
        )
    )

    if verbose:
        print("Messages:")
        from pprint import pprint
        pprint(messages)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=VERIFICATION_GEN_TEMP
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

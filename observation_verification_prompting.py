# CURRENTLY WORKING

import json
from openai import OpenAI
from typing import List, Dict, Union
from dotenv import load_dotenv
from prompting_utils import grid_to_python_literal
from FSP_DATA.observation_verification import FSP_RAW

load_dotenv()

VERIFICATION_GEN_TEMP = 0.0

def generate_verification_prompt(
    observation: str,
) -> list[dict]:
    """Generate a prompt for creating verification code."""
    content = (
        "Generate Python code to verify this observation about a grid transformation:\n"
        f"Observation: {observation}\n\n"
        "Write a function named 'verify' that takes input_grid and output_grid as parameters "
        "and returns True if the observation holds, False otherwise. Use standard python libraries "
        "like numpy if needed." 
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(fsp_data_regular: list[dict]) -> list[dict]:
    system_prompt = (
        "You are an expert Python programmer specializing in grid transformation verification. "
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data_regular:
        messages.extend(
            generate_verification_prompt(
                example['observation']
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
    verbose: bool = False
) -> str:
    """Generate verification code for an observation."""
    messages = []
    messages.extend(generate_fsp_context(fsp_data_regular=FSP_RAW))
    messages.extend(
        generate_verification_prompt(
            observation,
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

    response = completion.choices[0].message.content
    
    if verbose:
        print(f"Response: {response}")
    # Extract code from the response
    code = extract_code_from_response(response)
    
    if verbose:
        print(f"Verification code: {code}")
    
    return code

def extract_code_from_response(response: str) -> str:
    """Extract Python code from a response that may contain markdown or explanations."""
    # Look for code between Python code fence markers
    import re
    code_pattern = r"```(?:python)?\s*(.*?)```"
    matches = re.findall(code_pattern, response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Fallback: If no code blocks found, return the whole response
    return response.strip()

def verify_observation(
    verification_code: str,
    examples: List[Dict]
) -> bool:
    """Execute verification code and return result."""
    try:
        local_vars = {}
        exec(verification_code, {}, local_vars)
        verify_func = local_vars['verify']
        
        # Check if observation holds for all examples
        for example in examples:
            if not verify_func(example['input'], example['output']):
                return False
        return True
    except Exception as e:
        print(f"Error executing verification code: {e}")
        return False

def process_and_verify_observations(
    client: OpenAI,
    observations: List[str],
    examples: List[Dict],
    verbose: bool = False
) -> Dict[str, bool]:
    """Process and verify multiple observations."""
    results = {}
    for observation in observations:
        verification_code = generate_verification_code(
            client, observation, verbose
        )
        result = verify_observation(verification_code, examples)
        print(f"result of {observation}: {result}")
        results[observation] = result
    return results

def main():
    """Test the verification system."""
    from task import get_task
    
    client = OpenAI()
    task = get_task('arc-agi_evaluation_challenges.json', '212895b5')
    
    examples = task['train']
    
    test_observations = [
        "The grid dimensions remain the same in the input and output grids",
        "There is always a 3x3 block of blue (represented by 8) cells in the input grid and output grid, in the same position in both grids."
    ]
    
    results = process_and_verify_observations(
        client=client,
        observations=test_observations,
        examples=examples,
        verbose=True
    )
    
    print("\nVerification Results:")
    print("--------------------")
    for obs, result in results.items():
        print(f"Observation: {obs}")
        print(f"Verified: {'YES' if result else 'no'}\n")

if __name__ == "__main__":
    main()

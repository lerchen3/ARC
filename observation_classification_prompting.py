# CURRENTLY WORKING
# Possible future: Literally just look for keywords and classify by that  
# or use a classification neural network or whatever, 
# I don't think this step is actually that hard.
# (then again, gpt-4o-mini is minimal compute anyway)

import json
from openai import OpenAI
from dotenv import load_dotenv
from FSP_DATA.observation_classification import FSP_RAW
load_dotenv()

CLASSIFICATION_GEN_TEMP = 0.0

def generate_classification_prompt(observations: list[str]) -> list[dict]:
    """Generate a prompt for classifying observations with reasoning."""
    content = (
        "Given these observations about grid transformations, determine which ones "
        "could be easily verified with code, i.e. having a clear, well-defined criteria "
        "(answer 'Yes'), and which ones would be difficult to verify, i.e. abstract and "
        "challenging to algorithmically verify (answer 'No'). For each observation, "
        "provide a brief explanation of why it can or cannot be easily verified. "
        "Return a Python dictionary with 'response' containing both the classifications "
        "and their reasoning.\n\n"
        f"Observations:\n{json.dumps(observations, indent=2)}"
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(fsp_data: list[dict]) -> list[dict]:
    system_prompt = (
        "You are an expert at analyzing and classifying observations about grid "
        "transformations. Your task is to determine which observations can be "
        "easily verified through code and which ones require more complex analysis."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_classification_prompt(example['observations'])
        )
        messages.append({
            "role": "assistant",
            "content": json.dumps(example['response'])
        })
    
    return messages

FSP_CONTEXT = generate_fsp_context(FSP_RAW)

def classify_observations(
    client: OpenAI,
    observations: list[str],
    verbose: bool = False,
    max_observations_per_call: int = 10
) -> tuple[list[str], list[str]]:
    """Main function to classify observations with reasoning."""
    all_yes_observations = []
    all_no_observations = []
    
    # Split observations into batches
    for i in range(0, len(observations), max_observations_per_call):
        batch = observations[i:min(i + max_observations_per_call, len(observations))]
        
        messages = []
        messages.extend(FSP_CONTEXT)
        messages.extend(generate_classification_prompt(batch))

        if verbose:
            print(f"\nProcessing batch {i//max_observations_per_call + 1}")
            print("Messages:")
            from pprint import pprint
            pprint(messages)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            temperature=CLASSIFICATION_GEN_TEMP
        )

        try:
            response_content = completion.choices[0].message.content
            if verbose:
                print(f"Batch {i//max_observations_per_call + 1} response_content:")
                print(response_content)
            
            # Clean the response before parsing
            cleaned_response = clean_response(response_content)
            response_dict = json.loads(cleaned_response)
            
            # Extract just the observation strings from the dictionaries
            batch_yes = [obs['observation'] for obs in response_dict.get('response', {}).get('yes_observations', [])]
            batch_no = [obs['observation'] for obs in response_dict.get('response', {}).get('no_observations', [])]
            
            all_yes_observations.extend(batch_yes)
            all_no_observations.extend(batch_no)
            
        except Exception as e:
            print(f"Error processing batch {i//max_observations_per_call + 1}: {e}")
            # Add the failed batch to no_observations
            all_no_observations.extend(batch)

    if verbose:
        print(f"\nTotal observations processed: {len(all_yes_observations) + len(all_no_observations)}")
        print(f"Expected observations: {len(observations)}")

    return all_yes_observations, all_no_observations

def main():
    """Test the classification system with task 00d62c1b."""
    from task import get_task
    
    client = OpenAI()
    task = get_task('arc-agi_training_challenges.json', '00d62c1b')
    
    test_observations = [
        "The grid dimensions double in both width and height",
        "All cells maintain their original colors",
        "The pattern shows aesthetic balance",
        "Each 2x2 block in the output contains exactly one colored cell"
    ]
    
    yes_observations, no_observations = classify_observations(
        client=client,
        observations=test_observations,
        verbose=True
    )
    
    print("\nClassification Results:")
    print("----------------------")
    print("\nEasily Verifiable Observations:")
    for obs in yes_observations:
        print(f"- {obs}")
    
    print("\nNot Easily Verifiable Observations:")
    for obs in no_observations:
        print(f"- {obs}")

def clean_response(response_content: str) -> str:
    """Extract just the JSON content we need."""
    start = response_content.find('"response": {')
    if start == -1:
        raise ValueError("Could not find 'response': { in API response")
    end = response_content.rfind('}')
    return '{' + response_content[start:end+1]

if __name__ == "__main__":
    main()

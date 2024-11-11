# CURRENTLY WORKING
# Possible future: Literally just look for keywords and classify by that  
# or use a classification neural network or whatever, 
# I don't think this step is actually that hard.
# (then again, gpt-4o-mini is minimal compute anyway)
# OR: Tell 4o-mini to actually generate a reason for its classification, and pass
# that on to verification context (probably not necessary though).

import json
from openai import OpenAI
from dotenv import load_dotenv
from FSP_DATA.observation_classification import FSP_RAW
load_dotenv()

CLASSIFICATION_GEN_TEMP = 0.0

def generate_classification_prompt(observations: list[str]) -> list[dict]:
    """
    Generate a prompt for classifying observations.
    
    Parameters:
    ----------
    observations: list[str]
        List of observations to classify
        
    Returns:
    -------
        An OpenAI message history.
    """
    content = (
        "Given these observations about grid transformations, determine which ones "
        "could be easily verified with code (answer 'Yes') and which ones would be "
        "difficult to verify (answer 'No'). Return two Python lists: 'yes_observations' "
        "and 'no_observations'.\n\n"
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
            "content": json.dumps(example['classification'])
        })
    
    return messages

FSP_CONTEXT = generate_fsp_context(FSP_RAW)

def classify_observations(
    client: OpenAI,
    observations: list[str],
    verbose: bool = False
) -> tuple[list[str], list[str]]:
    """Main function to classify observations into verifiable and non-verifiable."""
    messages = []
    messages.extend(FSP_CONTEXT)
    messages.extend(generate_classification_prompt(observations))

    if verbose:
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
            print("Response:")
            print(response_content)
            
        response_dict = json.loads(response_content)
        return (
            response_dict.get('yes_observations', []),
            response_dict.get('no_observations', [])
        )
    except Exception as e:
        print(f"Error processing response: {e}")
        return [], []

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

if __name__ == "__main__":
    main()

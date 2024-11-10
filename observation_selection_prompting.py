import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from FSP_DATA.observation_selection import FSP_RAW

OBSERVATION_SELECT_TEMP = 0.2


def generate_selection_prompt(
    observations: list[str],
    num_best: int,
    context: str
) -> list[dict]:
    """Generate a prompt for selecting the best observations."""
    content = (
        f"Given these observations {context}, select the {num_best} most important "
        f"and relevant ones. Return them as a Python list of strings.\n\n"
        f"Observations:\n{json.dumps(observations, indent=2)}"
    )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(fsp_data: list[dict]) -> list[dict]:
    system_prompt = (
        "You are an expert at analyzing and selecting the most relevant observations "
        "about grid transformations. Your task is to identify the most important "
        "observations that best describe the transformation pattern."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_selection_prompt(
                example['observations'],
                example['num_best'],
                example['context']
            )
        )
        messages.append({
            "role": "assistant",
            "content": json.dumps(example['selected_observations'])
        })
    
    return messages

FSP_CONTEXT = generate_fsp_context(FSP_RAW)

def select_best_observations(
    client: OpenAI,
    observations: list[str],
    num_best: int,
    context: str = "",
    verbose: bool = False
) -> list[str]:
    """Main function to select the best observations."""
    messages = []
    messages.extend(FSP_CONTEXT)
    messages.extend(generate_selection_prompt(observations, num_best, context))

    if verbose:
        print("Messages:")
        from pprint import pprint
        pprint(messages)

    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        max_tokens=1024,
        temperature=OBSERVATION_SELECT_TEMP
    )

    try:
        response_content = completion.choices[0].message.content
        if verbose:
            print("Response:")
            print(response_content)
            
        selected = json.loads(response_content)
        return selected[:num_best]
    except Exception as e:
        print(f"Error processing response: {e}")
        return []

def main():
    """Test the selection system with task 00d62c1b."""
    from task import get_task
    
    client = OpenAI()
    task = get_task('arc-agi_training_challenges.json', '00d62c1b')
    
    test_observations = [
        "The grid dimensions double in both width and height",
        "All cells maintain their original colors",
        "The pattern shows aesthetic balance",
        "Each 2x2 block in the output contains exactly one colored cell",
        "The transformation preserves color ratios",
        "The output grid has a checkerboard-like structure"
    ]
    
    context = "about grid expansion patterns"
    num_best = 3
    
    best_observations = select_best_observations(
        client=client,
        observations=test_observations,
        num_best=num_best,
        context=context,
        verbose=True
    )
    
    print("\nBest Selected Observations:")
    print("-------------------------")
    for i, obs in enumerate(best_observations, 1):
        print(f"{i}. {obs}")

if __name__ == "__main__":
    main() 
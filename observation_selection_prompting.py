# CURRENTLY WORKING

import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from FSP_DATA.observation_selection_regular import FSP_RAW_REGULAR
from FSP_DATA.observation_selection_difficult import FSP_RAW_DIFFICULT

SELECTION_GEN_TEMP = 0.0

def generate_selection_prompt(
    observations: list[str],
    num_best: int,
    easy_to_verify: bool = True
) -> list[dict]:
    """Generate a prompt for selecting the best observations."""
    if easy_to_verify:
        content = (
            f"From these observations, select the {num_best} that provide the most "
            f"concrete and verifiable features of the transformation. Focus on "
            f"observations that describe specific, measurable features.\n\n"
            f"Observations:\n{json.dumps(observations, indent=2)}"
        )
    else:
        content = (
            f"From these observations, select the {num_best} that, if refined further, "
            f"could reveal the most important concrete patterns about the transformation. "
            f"Focus on observations that hint at deeper, systematic rules.\n\n"
            f"Observations:\n{json.dumps(observations, indent=2)}"
        )
    
    return [{"role": "user", "content": content}]

def generate_fsp_context(
    fsp_data_regular: list[dict],
    fsp_data_difficult: list[dict],
    easy_to_verify: bool = True
) -> list[dict]:
    system_prompt = (
        "You are an expert at analyzing and selecting the most valuable observations "
        "about grid transformations. "
    )
    
    if easy_to_verify:
        system_prompt += (
            "You excel at identifying observations that describe concrete, "
            "measurable features of transformations."
        )
        fsp_data = fsp_data_regular
    else:
        system_prompt += (
            "You excel at identifying observations that, while currently abstract, "
            "have the potential to reveal concrete transformation rules when refined."
        )
        fsp_data = fsp_data_difficult
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for example in fsp_data:
        messages.extend(
            generate_selection_prompt(
                example['observations'],
                example['num_best'],
                easy_to_verify
            )
        )
        messages.append({
            "role": "assistant",
            "content": json.dumps(example['selected_observations'])
        })
    
    return messages

def select_best_observations(
    client: OpenAI,
    observations: list[str],
    num_best: int,
    easy_to_verify: bool,
    verbose: bool = False
) -> list[str]:
    """Main function to select the best observations."""
    messages = []
    messages.extend(generate_fsp_context(
        fsp_data_regular=FSP_RAW_REGULAR,
        fsp_data_difficult=FSP_RAW_DIFFICULT,
        easy_to_verify=easy_to_verify
    ))
    messages.extend(generate_selection_prompt(
        observations=observations,
        num_best=num_best,
        easy_to_verify=easy_to_verify
    ))

    if verbose:
        print("\nMessages:")
        from pprint import pprint
        pprint(messages)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1024,
        temperature=SELECTION_GEN_TEMP
    )

    try:
        response_content = completion.choices[0].message.content
        if verbose:
            print("Response:")
            print(response_content)
            
        selected = eval(response_content)
        return selected[:num_best]
    except Exception as e:
        print(f"Error processing response: {e}")
        return observations[:num_best]  # Return first num_best observations as fallback

def main():
    """Test the observation selection system."""
    client = OpenAI()
    
    test_observations = [
        "**Pattern Consistency**: The final pattern in each sequence preserves some "
        "spatial characteristics of the initial pattern. This suggests that the "
        "transformation rule might involve a local duplication or scaling within "
        "each block of the original grid.",
        "**Color Retention**: The transformation maintains consistent color usage "
        "throughout each sequence. Each color present in the initial pattern remains "
        "consistent in the final pattern.",
        "**Spatial Connectivity**: Some colored regions maintain relative proximity "
        "to their positions in the input grids, forming linked patterns in the output grids."
    ]
    
    selected = select_best_observations(
        client=client,
        observations=test_observations,
        num_best=1,
        verbose=True,
        easy_to_verify=True
    )
    
    print("\nSelected Observations:")
    print("---------------------")
    for i, observation in enumerate(selected, 1):
        print(f"{i}. {observation}")

if __name__ == "__main__":
    main()
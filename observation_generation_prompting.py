# CURRENTLY WORKING
# TODO: Add guidance here to not have overlap between rollouts.

import re
from pprint import pprint
from dotenv import load_dotenv
load_dotenv() 
from openai import OpenAI
from prompting_utils import grid_to_python_literal, format_additional_context
from task import Task, TaskDataset, get_task
from FSP_DATA.observation_gen_regular import FSP_RAW_OBSERVATION_GEN
from FSP_DATA.observation_gen_refinement import FSP_RAW_REFINEMENT

OBSERVATION_GEN_TEMP = 0.8

def generate_observation_prompt(
        num_observations: int,
        task: Task,
        questions: list[str],
        original_observation: str = ""
) -> list[dict]:
    """
    Generate a prompt for generating observations about a task.

    Parameters:
    ----------
    num_observations: int
        The number of observations to generate.
    task: Task
        The task to generate observations about.
    questions: list[str], optional
        Questions about base observation
    
    Returns:
    -------
        An OpenAI message history.
    """
    base_prompt = (
        f"Please provide {num_observations} observations about "
        f"the nature of the transformations, the input grids, or "
        f"the output grids. Output your observations as a numbered "
        f"list."
    )

    if questions:
        base_prompt += format_additional_context(
            questions=questions,
            original_observation=original_observation
        )

    content = [
        {
            "type": "text",
            "text": base_prompt
        }
    ]

    for example in task.examples_with_images:
        base64_image = example['base64_image']
        input_literal = grid_to_python_literal(example['input'])
        output_literal = grid_to_python_literal(example['output'])

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        )
        content.append(
            {
                "type": "text",
                "text": (
                    f"Python Representation:\n"
                    f"Input Grid:\n{input_literal}\n"
                    f"Output Grid:\n{output_literal}"
                )
            }
        )
    return [
        {
            "role": "user",
            "content": content
        }
    ]


def generate_fsp_context(
    fsp_data_regular: list[dict],
    fsp_data_refinement: list[dict],
    is_refinement: bool = False
) -> list[dict]:
    """Generate FSP context based on whether we're doing refinement or regular observation generation."""
    system_prompt = (
        "You are an expert at analyzing transformations between grids. "
        "Your goal is to be very, very, very, very, very insightful! "
        "Here's what color each number corresponds to: "
        "0: Black, 1: Blue, 2: Red, 3: Green, 4: Yellow, 5: Gray, "
        "6: Magenta, 7: Orange, 8: Cyan, 9: Brown. "
    )

    if is_refinement:
        system_prompt += (
            "You excel at refining and deeply exploring existing transformation ideas, "
            "building upon initial observations to uncover more nuanced patterns and relationships."
        )
        fsp_data = fsp_data_refinement
    else:
        system_prompt += (
            "You specialize in generating fresh observations about grid transformations, "
            "focusing on patterns, relationships, and underlying rules."
        )
        fsp_data = fsp_data_regular

    messages = [{"role": "system", "content": system_prompt}]

    for example in fsp_data:
        num_observations = example.get('observations_to_generate', 10)
        messages.extend(
            generate_observation_prompt(
                num_observations=num_observations,
                task=get_task(example['file_path'], example['task_id']),
                questions=example.get('questions', ''),
                original_observation=example.get('original_observation', '')
            )
        )
        messages.append({
            "role": "assistant",
            "content": example['observation']
        })

    return messages


def generate_observations(
        client: OpenAI,
        num_observations: int,
        task: Task,
        verbose: bool = False,
        max_observations_per_call: int = 10,
        questions: str = "",
        original_observation: str = ""
) -> list[str]:
    """
    Generate observations about a task.

    Implementation note:
     - First off, OpenAI should do prefix caching for the massive FSP context.
     - Second, we only make one call to GPT-4o-mini, and let it generate
       as many observations as it can given the token limit. We set a high
       n so that the prefix is used in all n rollouts.
     - Adjust num_observations to stay within token limits.
     - Decrease max_observations_per_call so the model doesn't behave badly.

    Future idea: include things that we are "currently interested in"
    to guide the generation of observations. The current generation method
    probably yields many overlapping observations between rollouts.

    Parameters:
    ----------
    client: OpenAI
        The OpenAI client to use to generate observations.
    num_observations: int
        The number of observations to generate.
    task: Task
        The task to generate observations about.
    questions: str, optional
        Additional context or instructions to guide the observation generation; used when refining observations.
    """

    # Construct the prompt
    messages = []

    messages.extend(generate_fsp_context(
        fsp_data_regular=FSP_RAW_OBSERVATION_GEN,
        fsp_data_refinement=FSP_RAW_REFINEMENT,
        is_refinement=bool(questions)
    ))

    messages.extend(
        generate_observation_prompt(
            num_observations=max_observations_per_call,
            task=task,
            questions=questions,
            original_observation=original_observation
        )
    )

    if verbose:
        print("Messages:")
        pprint(messages)

    # Make the API call using the OpenAI client
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=2048,
        n=num_observations // max_observations_per_call + 1,
        temperature=OBSERVATION_GEN_TEMP
    )

    observations = []
    if verbose:
        print("Responses:")
    for response in completion.choices:
        response_content = response.message.content
        if verbose:
            print(response_content)
        for observation in response_content.split('\n'):
            match = re.match(r'^\s*(\d+)\.\s*(.*)$', observation)
            if match:
                observations.append(match.group(2))

    observations = observations[:num_observations]
    
    if verbose:
        print("Observations:")
        pprint(observations)
    return observations


def main():
    """
    Test the functions.
    """

    task = get_task('arc-agi_training_challenges.json', '00d62c1b')

    client = OpenAI()
    generate_observations(
        client=client,
        num_observations=256,
        task=task,
        verbose=True
    )


if __name__ == "__main__":
    main()

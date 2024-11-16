import os
from openai import OpenAI
from dotenv import load_dotenv
from task import TaskDataset, get_task
from observation_generation_prompting import generate_observations
from observation_verification_prompting import process_and_verify_observations
from observation_classification_prompting import classify_observations
from observation_selection_prompting import select_best_observations
from observation_questioning_prompting import generate_questions
import random
from prompting_utils import extract_code_from_response
from vision_prompting import create_transformation_image

MAX_SEARCH_DEPTH = 5

load_dotenv() 

# Initialize OpenAI client
client = OpenAI()


all_task_ids = TaskDataset('arc-agi_evaluation_challenges.json').tasks.keys()
random.shuffle(all_task_ids)
all_task_ids = all_task_ids[:10]

for task_id in all_task_ids:
    # Get task using the factory function
    task = get_task('arc-agi_evaluation_challenges.json', all_task_ids[0])
    print(f"Processing task {task['task_id']}")

    # Generate initial observations
    try:
        observations = generate_observations(
            client=client,
            num_observations=256,
            task=task)
        print(f"Generated {len(observations)} initial observations")
    except Exception as e:
        print(f"Error generating observations: {e}")
        observations = []

    # Classify observations into 'yes' and 'no'
    try:
        yes_observations, no_observations = classify_observations(
            client=client,
            observations=observations,
            verbose=True
        )
        print(f"Classified {len(yes_observations)} yes observations and {len(no_observations)} no observations")
    except Exception as e:
        print(f"Error classifying observations: {e}")

    random.shuffle(yes_observations)
    random.shuffle(no_observations)

    # Split into 16 roughly equal batches
    batch_size = len(yes_observations) // 16
    yes_batches = [yes_observations[i*batch_size:(i+1)*batch_size] for i in range(0, 16)]
    # Select best from each batch
    best_yes_observations = []
    for batch in yes_batches:
        selected = select_best_observations(
            client=client,
            observations=batch,
            num_best=1,  # Select 1 from each batch
            easy_to_verify=True,
            verbose=False
        )
        print(f"from yes batch: {batch} selected: {selected}")
        best_yes_observations.extend(selected)

    # Do the same for no_observations
    batch_size = len(no_observations) // 16
    no_batches = [no_observations[i*batch_size:(i+1)*batch_size] for i in range(0, 16)]
    best_no_observations = []
    for batch in no_batches:
        selected = select_best_observations(
            client=client,
            observations=batch,
            num_best=1,
            easy_to_verify=False,
            verbose=False
        )
        best_no_observations.extend(selected)

    # Initialize observations and 'no's lists
    observations_list = best_yes_observations
    nos_list = best_no_observations

    # Now, for search_depth in range(1, max_search_depth+1)
    for search_depth in range(1, MAX_SEARCH_DEPTH+1):
        print(f"Search Depth: {search_depth}")
        if not nos_list:
            print("No more 'no' observations to expand upon")
            break
        new_observations = []
        for no_observation in nos_list:
            # Generate questions for this observation
            questions = generate_questions(
                client=client,
                observation=no_observation,
                num_questions=5
            )
            print(f"questions: {questions}")
            # Create additional context combining the original observation and questions
            observations = generate_observations(
                client=client,
                num_observations=5,
                task=task,
                verbose=False,
                questions = questions,
                original_observation=no_observation
            )
            print(f"observations: {observations}")
            new_observations.extend(observations)
        
        # Classify observations
        yes_obs, no_obs = classify_observations(
            client=client,
            observations=new_observations,
            max_observations_per_call = 5,
            verbose=False
        )
        print(f"yes_obs: {yes_obs}")
        print(f"no_obs: {no_obs}")  
        # Select best observations
        best_yes_obs = select_best_observations(
            client=client,
            observations=yes_obs,
            num_best=4,
            easy_to_verify=True,
            verbose=False
        )
        best_no_obs = select_best_observations(
            client=client,
            observations=no_obs,
            num_best=16,
            easy_to_verify=False,
            verbose=False
        )
        
        # Add to lists
        observations_list.extend(best_yes_obs)
        nos_list = best_no_obs

    verified_observations = process_and_verify_observations(
        client=client,
        observations=observations_list,
        examples=task['train'],
        verbose=False
    )

    all_information = []
    for observation, is_valid in verified_observations.items():
        if is_valid: 
            all_information.append(observation)


    #================================

    # Format the information into a numbered list
    numbered_info = "\n".join(f"{i+1}. {info}" for i, info in enumerate(all_information))

    # Create the message content
    content = [
        {
            "type": "text",
            "text": (
                "Given these verified observations about the grid transformation:\n\n"
                f"{numbered_info}\n\n"
                "Please generate Python code that implements this transformation. "
                "The code should take an input grid (represented as a 2D list of integers) "
                "and return the transformed output grid.\n\n"
                "Python representation of example grids:\n"
            )
        }
    ]

    # Add image and grid representations for each example
    for example in task['train']:
        content.extend([
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{example['base64_image']}"
                }
            },
            {
                "type": "text",
                "text": (
                    f"Input Grid:\n{example['input']}\n"
                    f"Output Grid:\n{example['output']}\n"
                )
            }
        ])

    # Make the API call
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": content}],
        max_tokens=2048,
        temperature=0.0
    )

    # Extract code
    response = completion.choices[0].message.content
    code = extract_code_from_response(response)

    try:
        # Test the code on all training examples
        local_vars = {}
        exec(code, {}, local_vars)
        transform_func = local_vars['transform']
        
        for example in task['train']:
            result = transform_func(example['input'])
            if result != example['output']:
                print("Code failed validation on training examples")
                exit()
        
        # If we get here, apply to test input
        test_input = task['test'][0]['input']
        test_output = transform_func(test_input)
        print(f"Generated test output: {test_output}")
        
        # Create and display the transformation image
        create_transformation_image(
            input_grid=test_input,
            output_grid=test_output,
            save_location=f"answer_images/ANSWER_IMAGE_{task['task_id']}.png"
        )
        print(f"\nTransformation image saved as 'answer_images/ANSWER_IMAGE_{task['task_id']}.png'")
        
    except Exception as e:
        print(f"Error executing transformation code: {e}")


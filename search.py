import os
from openai import OpenAI
from dotenv import load_dotenv
from task import TaskDataset
from vision_prompting import create_transformation_image
from observation_generation_prompting import generate_observations
from observation_verification_prompting import process_and_verify_observations
from observation_classification_prompting import classify_observations
from observation_selection_prompting import select_best_observations
from observation_questioning_prompting import generate_questions

MAX_SEARCH_DEPTH = 100

load_dotenv() 

# Initialize OpenAI client
client = OpenAI()

arc_tasks = TaskDataset('arc-agi_evaluation_challenges.json')

task_ids = arc_tasks.keys()
task_id = task_ids[57]
print(task_id)
task = arc_tasks.get_task(task_id)
print(f"Processing task {task_id}")
num_examples = task['num_examples']

# Now, generate observations
# List to store examples with images
examples_with_images = []

# Ensure the 'task_images' directory exists
os.makedirs('task_images', exist_ok=True)

# Create images for each example and collect them
for idx, example in enumerate(task['train']):
    input_grid = example['input']
    output_grid = example['output']

    # Create the image representing the transformation
    image_filename = f"task_images/{task_id}_{idx+1}.png"

    base64_image = create_transformation_image(
        input_grid, output_grid, save_location=image_filename,
        cache=True, return_base64=True)

    # Add the base64 image to the example
    example_with_image = {
        'input': input_grid,
        'output': output_grid,
        'base64_image': base64_image
    }
    examples_with_images.append(example_with_image)

observations = generate_observations(
    client=client,
    num_observations=256,
    task=task,
    verbose=False,
    additional_context=""
)

# Classify observations into 'yes' and 'no'
yes_observations, no_observations = classify_observations(
    client=client,
    observations=observations,
    verbose=False
)

# Select the 16 best 'yes' observations
best_yes_observations = select_best_observations(
    client=client,
    observations=yes_observations,
    num_best=16,
    easy_to_verify=True,
    verbose=False
)

# Select the 16 best 'no' observations
best_no_observations = select_best_observations(
    client=client,
    observations=no_observations,
    num_best=16,
    easy_to_verify=False,
    verbose=False
)

# Initialize observations and 'no's lists
observations_list = best_yes_observations
nos_list = best_no_observations

# Now, for search_depth in range(1, max_search_depth+1)
for search_depth in range(1, MAX_SEARCH_DEPTH+1):
    print(f"Search Depth: {search_depth}")
    if not nos_list:
        break  # No more 'no' observations to expand upon
    new_observations = []
    new_nos = []
    for no_observation in nos_list:
        # Generate questions for this observation
        questions = generate_questions(
            client=client,
            observation=no_observation,
            num_questions=5
        )
        
        # Create additional context combining the original observation and questions
        questions_context = "\n".join([f"- {q}" for q in questions])
        additional_context = (
            f"Here's an observation I made. For all of the observations "
            f"you give, please address these specific questions about the observation:\n"
            f"{questions_context}\n\n"
            f"Original observation:\n{no_observation}"
        )
        
        # Generate observations with the enhanced context
        observations = generate_observations(
            client=client,
            num_observations=16,
            task=task,
            verbose=False,
            additional_context=additional_context
        )
        
        # Classify observations
        yes_obs, no_obs = classify_observations(
            client=client,
            observations=observations,
            verbose=False
        )
        
        # Select best observations
        best_yes_obs = select_best_observations(
            client=client,
            observations=yes_obs,
            num_best=16,
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
        new_nos.extend(best_no_obs)
    nos_list = new_nos

# Process and verify regular observations
valid_observations = process_and_verify_observations(
    client=client,
    observations=observations_list,
    examples=examples_with_images,
    task=task,
    is_difficult=False
)

# Process and verify difficult observations
print("\nProcessing difficult observations:")
valid_difficult_observations = process_and_verify_observations(
    client=client,
    observations=nos_list,
    examples=examples_with_images,
    task=task,
    is_difficult=True
)

# Combine all valid observations
all_valid_observations = valid_observations + valid_difficult_observations

# Print the valid observations with code verifiers
print("\nValid Observations:")
for observation, code_dict in all_valid_observations:
    print(f"\nObservation: {observation}")
    for code_verifier_name, code_str in code_dict.items():
        print(f"{code_verifier_name}:\n{code_str}\n")
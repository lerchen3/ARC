import os
from openai import OpenAI
from dotenv import load_dotenv
from task import TaskDataset, get_task
from observation_generation_prompting import generate_observations
from observation_verification_prompting import process_and_verify_observations
from observation_classification_prompting import classify_observations
from observation_selection_prompting import select_best_observations
from observation_questioning_prompting import generate_questions

MAX_SEARCH_DEPTH = 100

load_dotenv() 

# Initialize OpenAI client
client = OpenAI()

# Get task using the factory function
task = get_task('arc-agi_evaluation_challenges.json', '212895b5')
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
    yes_observations, no_observations = [], []

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

# Process and verify observations
verified_observations = process_and_verify_observations(
    client=client,
    observations=observations_list,
    examples=task['train'],
    verbose=False
)

# Print the valid observations with code verifiers
print("\nVerified Observations:")
for observation, is_valid in verified_observations.items():
    print(f"\nObservation: {observation}")
    print(f"Valid: {is_valid}")
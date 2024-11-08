# Controls
import base64
import json
import os

from openai import OpenAI

from prompting_utils import grid_to_python_literal
from vision_prompting import create_transformation_image

max_search_depth = 100
observation_gen_temp = 1.1
observation_classify_temp = 0.5
observation_select_temp = 0.5
code_verifier_gen_temp = 0.8


# Initialize OpenAI client
client = OpenAI()

# Load the JSON file
with open('arc-agi_evaluation_challenges.json', 'r') as f:
    arc_tasks = json.load(f)

# Function to generate observations


def generate_observations(num_observations, examples, additional_context=None):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 50  # Adjusted for token limits
    total_observations = []
    observations_remaining = num_observations

    while observations_remaining > 0:
        observations_to_request = min(
            observations_remaining, max_observations_per_call)
        # Construct the prompt
        content_text = (
            f"Please analyze the transformations shown in the following examples and provide {observations_to_request} observations about the nature of the transformations, the input grids, or the output grids. "
            "Bottom line, help me understand the input, the output, and the transformation from just natural language. "
            "Try to be very, very, very, very, very insightful! "
            "Return only the list of observations in valid JSON format."
        )
        if additional_context:
            content_text += additional_context

        # Prepare the messages for the API
        messages = [
            {
                "role": "user",
                "content": content_text
            }
        ]

        # Add examples
        for idx, example in enumerate(examples):
            input_grid = example['input']
            output_grid = example['output']
            input_literal = grid_to_python_literal(input_grid)
            output_literal = grid_to_python_literal(output_grid)
            base64_image = example.get('base64_image', None)
            messages.append(
                {
                    "role": "user",
                    "content": f"Example {idx+1}:"
                }
            )
            if base64_image:
                messages.append(
                    {
                        "role": "user",
                        "content": f"![Example {idx+1}](data:image/png;base64,{base64_image})"
                    }
                )
            messages.append(
                {
                    "role": "user",
                    "content": f"Python Representation:\nInput Grid:\n{input_literal}\nOutput Grid:\n{output_literal}\nHere's what color each number corresponds to. 0: Black, 1: Blue, 2: Red, 3: Green, 4: Yellow, 5: Gray, 6: Magenta, 7: Orange, 8: Cyan, 9: Brown."
                }
            )

        # Make the API call using the OpenAI client
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2048,
            n=1,
            temperature=observation_gen_temp
        )

        observations = []

        # Process the response
        try:
            response_content = completion.choices[0].message.content
            response_content = response_content.strip()
            # Find the first '[' and last ']' to extract the JSON array
            start_index = response_content.find('[')
            end_index = response_content.rfind(']') + 1

            if start_index == -1 or end_index == -1:
                print("Could not find JSON array in the response.")
                return total_observations

            json_str = response_content[start_index:end_index]
            observations = json.loads(json_str)
            total_observations.extend(observations)
        except Exception as e:
            print(f"Error processing GPT-4 response: {e}")
            return total_observations

        observations_remaining -= observations_to_request

    return total_observations

# Function to classify observations into 'yes' and 'no'


def classify_observations(observations):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 50  # Adjusted for token limits
    yes_observations = []
    no_observations = []
    for i in range(0, len(observations), max_observations_per_call):
        batch = observations[i:i+max_observations_per_call]
        content_text = (
            "Given the following observations about the transformations, please determine whether one could easily make "
            "very, very well-defined and correct code that could verify that these observations are indeed true for the given examples "
            "(make sure you say no for at least a quarter of these observations - if you run out of things to say no to, say no to the observations that would be really tedious to implement). "
            "For each observation, answer 'Yes' if code could easily verify it, or 'No' if not. "
            "Create a compilation of the 'Yes's into a Python list called 'yes_observations', and the 'No's into a Python list called 'no_observations'. Return only these lists."
        )

        messages = [
            {
                "role": "user",
                "content": content_text
            },
            {
                "role": "user",
                "content": "Observations:\n" + json.dumps(batch, indent=2)
            }
        ]

        # Make the API call using the OpenAI client
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            n=1,
            temperature=observation_classify_temp
        )

        # Process the response
        try:
            response_content = completion.choices[0].message.content
            local_vars = {}
            exec(response_content, {}, local_vars)
            yes_batch = local_vars.get('yes_observations', [])
            no_batch = local_vars.get('no_observations', [])
            yes_observations.extend(yes_batch)
            no_observations.extend(no_batch)
        except Exception as e:
            print(f"Error processing GPT-4 response: {e}")

    return yes_observations, no_observations

# Function to select best observations


def select_best_observations(observations, num_best, context):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 50  # Adjusted for token limits
    selected_observations = []
    for i in range(0, len(observations), max_observations_per_call):
        batch = observations[i:i+max_observations_per_call]
        content_text = (
            f"Given the following observations that are {context}, please select up to {num_best} best observations that would be most crucial to a complete understanding of the input, output, and transformation. "
            f"Include somewhere a Python list of these observations called 'best_observations'. Return only this list."
        )

        messages = [
            {
                "role": "user",
                "content": content_text
            },
            {
                "role": "user",
                "content": "Observations:\n" + json.dumps(batch, indent=2)
            }
        ]

        # Make the API call using the OpenAI client
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1024,
            n=1,
            temperature=observation_select_temp
        )

        # Process the response
        try:
            response_content = completion.choices[0].message.content
            local_vars = {}
            exec(response_content, {}, local_vars)
            best_batch = local_vars.get('best_observations', [])
            selected_observations.extend(best_batch)
            if len(selected_observations) >= num_best:
                return selected_observations[:num_best]
        except Exception as e:
            print(f"Error processing GPT-4 response: {e}")

    return selected_observations[:num_best]

# Function to generate code verifiers for observations


def generate_code_verifiers_for_block(observations_block, examples):
    observations_with_code = {}
    # Adjusted number of observations per call to stay within token limits
    max_observations_per_call = 20  # Adjusted for token limits

    for i in range(0, len(observations_block), max_observations_per_call):
        batch = observations_block[i:i+max_observations_per_call]
        content_text = (
            "Please write code that verifies each of the following observations for given input and output grids. "
            "For each observation, the code should be of the form 'def check_observation(input_grid, output_grid): ...'. "
            "Be careful that the code verifies exactly the natural language description. "
            "Implement a soundproof code. "
            "Provide 4 different implementations for each observation."
        )
        # Prepare the messages
        messages = [
            {
                "role": "user",
                "content": content_text
            },
            {
                "role": "user",
                "content": "Observations:\n" + json.dumps(batch, indent=2)
            }
        ]

        # Make the API call using the OpenAI client
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2048,
            n=1,
            temperature=code_verifier_gen_temp
        )

        # Process the response
        try:
            response_content = completion.choices[0].message.content
            # Parse the response to extract code verifiers for each observation
            # Assuming the response is a JSON object mapping observations to code implementations
            code_verifiers = json.loads(response_content)
            for observation in batch:
                if observation in code_verifiers:
                    observations_with_code[observation] = code_verifiers[observation]
        except Exception as e:
            print(f"Error processing GPT-4 response: {e}")

    return observations_with_code

# Function to generate code for difficult observations


def generate_code_for_difficult_observations(no_observations, examples):
    # Function to generate code verifiers for difficult observations
    observations_with_code = {}
    for observation in no_observations:
        content_text = (
            "Please write code that verifies the following observation for "
            "given input and output grids. The observation may be challenging "
            "to implement, so please try very hard to write correct and efficient "
            "code. You might need to implement complex algorithms like floodfill, "
            "recursion, or other advanced techniques. For the observation, the code "
            "should be of the form 'def check_observation(input_grid, output_grid): ...'. "
            "Be careful that the code verifies exactly the natural language description. "
            "Implement sound and robust code."
        )
        # Prepare the messages
        messages = [
            {
                "role": "user",
                "content": content_text
            },
            {
                "role": "user",
                "content": f"Observation:\n{observation}"
            }
        ]

        # Include examples
        examples_text = ""
        for idx, example in enumerate(examples):
            input_grid = example['input']
            output_grid = example['output']
            input_literal = grid_to_python_literal(input_grid)
            output_literal = grid_to_python_literal(output_grid)
            examples_text += (
                f"\nExample {idx+1}:\nInput Grid:\n{input_literal}\n"
                f"Output Grid:\n{output_literal}\n"
            )
        messages.append(
            {
                "role": "user",
                "content": f"Examples:{examples_text}"
            }
        )

        # Make the API call using the OpenAI client
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2048,
            n=1,
            temperature=code_verifier_gen_temp
        )

        # Process the response
        try:
            response_content = completion.choices[0].message.content
            code_str = response_content.strip()
            observations_with_code[observation] = code_str
        except Exception as e:
            print(f"Error processing GPT-4 response: {e}")

    return observations_with_code


# Main processing code
cnt = 0
for task_id, task in arc_tasks.items():
    cnt += 1
    # For demonstration purposes, limit to one task
    if cnt < 57:
        continue
    if cnt > 57:
        break
    print(f"Processing task {task_id}")
    num_examples = len(task['train'])

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
        num_observations=256,
        examples=examples_with_images
    )

    # Classify observations into 'yes' and 'no'
    yes_observations, no_observations = classify_observations(observations)

    # Select the 16 best 'yes' observations
    best_yes_observations = select_best_observations(
        yes_observations,
        16,
        'crucial to understanding the transformation'
    )

    # Select the 16 best 'no' observations
    best_no_observations = select_best_observations(
        no_observations,
        16,
        ('not easily verifiable by code but, if explored further, '
         'could provide valuable insights')
    )

    # Initialize observations and 'no's lists
    observations_list = best_yes_observations
    nos_list = best_no_observations

    # Now, for search_depth in range(1, max_search_depth+1)
    for search_depth in range(1, max_search_depth+1):
        print(f"Search Depth: {search_depth}")
        if not nos_list:
            break  # No more 'no' observations to expand upon
        new_observations = []
        new_nos = []
        for no_observation in nos_list:
            # Generate observations branching from this 'no' observation
            additional_context = (
                f"\nHere's an observation I made. For all of the observations "
                f"you give, please refine this observation in some way, whether "
                f"by elaboration, correction, or modification:\n{no_observation}"
            )
            observations = generate_observations(
                num_observations=16,
                examples=examples_with_images,
                additional_context=additional_context
            )
            # Classify observations
            yes_obs, no_obs = classify_observations(observations)
            # Select best observations
            best_yes_obs = select_best_observations(
                yes_obs, 16,
                ('easily verifiable by code and crucial to understanding '
                 'the transformation')
            )
            best_no_obs = select_best_observations(
                no_obs, 16,
                ('not easily verifiable by code but, if explored further, '
                 'could provide valuable insights')
            )
            # Add to lists
            observations_list.extend(best_yes_obs)
            new_nos.extend(best_no_obs)
        nos_list = new_nos

    # Now, generate code verifiers for observations_list
    observations_with_code = generate_code_verifiers_for_block(
        observations_list,
        examples_with_images
    )

    # Validate the observations
    valid_observations = []
    for observation, code_dict in observations_with_code.items():
        all_codes_valid = True
        for code_verifier_name, code_str in code_dict.items():
            code_str = code_str.strip()
            if not code_str.startswith(
                "def check_observation(input_grid, output_grid):"
            ):
                print(
                    f"Invalid function definition in {code_verifier_name} "
                    f"of observation '{observation}'."
                )
                all_codes_valid = False
                break
            local_vars = {}
            try:
                exec(code_str, globals(), local_vars)
                check_observation = local_vars['check_observation']
                all_hold = True
                for example in task['train']:
                    input_grid = example['input']
                    output_grid = example['output']
                    result = check_observation(input_grid, output_grid)
                    if not result:
                        all_hold = False
                        break
                if not all_hold:
                    all_codes_valid = False
                    break
            except Exception as e:
                print(
                    f"Error executing code for observation '{observation}': {e}"
                )
                all_codes_valid = False
                break
        if all_codes_valid:
            valid_observations.append((observation, code_dict))

    # Now, process the remaining 'no_observations' in nos_list
    print("\nProcessing difficult observations:")
    difficult_observations_with_code = generate_code_for_difficult_observations(
        nos_list,
        examples_with_images
    )

    # Validate the difficult observations
    for observation, code_str in difficult_observations_with_code.items():
        code_str = code_str.strip()
        if not code_str.startswith(
            "def check_observation(input_grid, output_grid):"
        ):
            print(
                f"Invalid function definition for observation '{observation}'."
            )
            continue
        local_vars = {}
        try:
            exec(code_str, globals(), local_vars)
            check_observation = local_vars['check_observation']
            all_hold = True
            for example in task['train']:
                input_grid = example['input']
                output_grid = example['output']
                result = check_observation(input_grid, output_grid)
                if not result:
                    all_hold = False
                    break
            if all_hold:
                valid_observations.append(
                    (observation, {'code_verifier': code_str})
                )
        except Exception as e:
            print(
                f"Error executing code for observation '{observation}': {e}"
            )
            continue

    # Print the valid observations with code verifiers
    print("\nValid Observations:")
    for observation, code_dict in valid_observations:
        print(f"\nObservation: {observation}")
        for code_verifier_name, code_str in code_dict.items():
            print(f"{code_verifier_name}:\n{code_str}\n")

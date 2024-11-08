#Controls!
max_search_depth = 100
observation_gen_temp = 1.1
observation_classify_temp = 0.5
observation_select_temp = 0.5
code_verifier_gen_temp = 0.8

import os
import json
import base64
import requests
from PIL import Image, ImageDraw
from dotenv import load_dotenv
load_dotenv()  # Make sure this comes before accessing the environment variable.

# Set your OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')

if api_key is None:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Load the JSON file
with open('arc-agi_evaluation_challenges.json', 'r') as f:
    arc_tasks = json.load(f)

# Color mapping, including color 10 for the arrow
arc_agi_colors = {
    0: "#000000",  # Black
    1: "#0074D9",  # Blue
    2: "#FF4136",  # Red
    3: "#2ECC40",  # Green
    4: "#FFDC00",  # Yellow
    5: "#AAAAAA",  # Gray
    6: "#F012BE",  # Magenta
    7: "#FF851B",  # Orange
    8: "#7FDBFF",  # Cyan
    9: "#B10DC9",  # Brown
    10: "#FFFFFF"  # White for arrow
}

# Function to create the transformation image
def create_transformation_image(input_grid, output_grid, scaling_factor=10):
    # Scale up the grids
    w_in = len(input_grid[0]) * scaling_factor
    h_in = len(input_grid) * scaling_factor

    w_out = len(output_grid[0]) * scaling_factor
    h_out = len(output_grid) * scaling_factor

    # Compute dimensions based on the instructions
    arrow_width = (w_in + w_out) // 2
    total_width = w_in + w_out + 20 + arrow_width
    total_height = max(h_in, h_out)

    # Create a new image with the computed dimensions
    img = Image.new('RGB', (total_width, total_height), color=arc_agi_colors[0])
    draw = ImageDraw.Draw(img)

    # Draw the input grid centered on the left side
    x_in = 0
    y_in = (total_height - h_in) // 2
    for i, row in enumerate(input_grid):
        for j, cell in enumerate(row):
            color = arc_agi_colors[cell]
            x0 = x_in + j * scaling_factor
            y0 = y_in + i * scaling_factor
            x1 = x0 + scaling_factor
            y1 = y0 + scaling_factor
            draw.rectangle([x0, y0, x1, y1], fill=color)

    # Draw the output grid centered on the right side
    x_out = w_in + 20 + arrow_width
    y_out = (total_height - h_out) // 2
    for i, row in enumerate(output_grid):
        for j, cell in enumerate(row):
            color = arc_agi_colors[cell]
            x0 = x_out + j * scaling_factor
            y0 = y_out + i * scaling_factor
            x1 = x0 + scaling_factor
            y1 = y0 + scaling_factor
            draw.rectangle([x0, y0, x1, y1], fill=color)

    # Draw the arrow between input and output grids
    x_arrow_start = w_in + 10
    x_arrow_end = x_out - 10
    y_arrow = total_height // 2
    arrow_height = 2  # 2 blocks thick (w/o scaling by 10)
    arrowhead_depth = (w_in + w_out) // 4

    # Draw the arrow shaft
    draw.rectangle(
        [x_arrow_start, y_arrow - arrow_height // 2, x_arrow_end, y_arrow + arrow_height // 2],
        fill=arc_agi_colors[10]
    )

    # Draw the arrowhead
    arrowhead = [
        (x_arrow_end, y_arrow),
        (3 + x_arrow_end - arrowhead_depth//2, y_arrow - arrowhead_depth//2),
        (3 + x_arrow_end - arrowhead_depth//2, y_arrow + arrowhead_depth//2)
    ]
    draw.polygon(arrowhead, fill=arc_agi_colors[10])

    return img

# Function to convert grids to their literal Python representation
def grid_to_python_literal(grid):
    return repr(grid)

# Function to generate observations
def generate_observations(num_observations, examples, additional_context=None):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 50  # Adjusted to ensure we stay within 8192 tokens
    total_observations = []
    observations_remaining = num_observations

    while observations_remaining > 0:
        observations_to_request = min(observations_remaining, max_observations_per_call)
        # Construct the prompt
        content_text = (
            f"Please analyze the transformations shown in the following examples and provide {observations_to_request} observations about the nature of the transformations, the input grids, or the output grids. "
            "Bottom line, help me understand the input, the output, and the transformation from just natural language. "
            "Try to be very, very, very, very, very insightful! "
            "Return only the list of observations in valid JSON format."
        )
        if additional_context:
            content_text += "\n Here's an observation I made. For all all of the observations you give, please give a refining of this observation in some way, whether by elaboration, correction, or modification:\n" + additional_context

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
            messages.append(
                {
                    "role": "user",
                    "content": f"Example {idx+1}:"
                }
            )
            messages.append(
                {
                    "role": "user",
                    "content": f"Python Representation:\nInput Grid:\n{input_literal}\nOutput Grid:\n{output_literal}\n Here's what color each number corresponds to. 0: Black, 1: Blue, 2: Red, 3: Green, 4: Yellow, 5: Gray, 6: Magenta, 7: Orange, 8: Cyan, 9: Brown. "
                }
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 2048,
            "n": 1,
            "temperature": observation_gen_temp
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        observations = []

        # Process the response
        if response.status_code == 200:
            completion = response.json()
            response_content = completion['choices'][0]['message']['content']
            try:
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
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return total_observations

        observations_remaining -= observations_to_request

    return total_observations

# Function to classify observations into 'yes' and 'no'
def classify_observations(observations):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 100  # Adjusted to ensure we stay within 8192 tokens
    yes_observations = []
    no_observations = []
    for i in range(0, len(observations), max_observations_per_call):
        batch = observations[i:i+max_observations_per_call]
        content_text = ( #for some reason this guy does not wanna say no. like, to anything. bro literally said yes to every single one of the 256 ones even though hes trash at implementing. ig we're making him say no. smh my head LOL
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

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 1024,
            "n": 1,
            "temperature": observation_classify_temp
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        # Process the response
        if response.status_code == 200:
            completion = response.json()
            response_content = completion['choices'][0]['message']['content']
            try:
                # Execute the response to extract the lists
                local_vars = {}
                exec(response_content, {}, local_vars)
                yes_batch = local_vars.get('yes_observations', [])
                no_batch = local_vars.get('no_observations', [])
                yes_observations.extend(yes_batch)
                no_observations.extend(no_batch)
            except Exception as e:
                print(f"Error processing GPT-4 response: {e}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    return yes_observations, no_observations

# Function to select best observations
def select_best_observations(observations, num_best, context):
    # Adjust the number of observations per call to stay within token limits
    max_observations_per_call = 100  # Adjusted to ensure we stay within 8192 tokens
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

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 1024,
            "n": 1,
            "temperature": observation_select_temp
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        # Process the response
        if response.status_code == 200:
            completion = response.json()
            response_content = completion['choices'][0]['message']['content']
            try:
                # Execute the response to extract the list
                local_vars = {}
                exec(response_content, {}, local_vars)
                best_batch = local_vars.get('best_observations', [])
                selected_observations.extend(best_batch)
                if len(selected_observations) >= num_best:
                    return selected_observations[:num_best]
            except Exception as e:
                print(f"Error processing GPT-4 response: {e}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    return selected_observations[:num_best]

# Function to generate code verifiers for observations
def generate_code_verifiers_for_block(observations_block, examples):
    # observations_block: list of observations
    # Returns: observations_with_code: dict mapping observation to dict of code verifiers
    observations_with_code = {}
    # Adjusted number of observations per call to stay within token limits
    max_observations_per_call = 5  # Adjusted to ensure we stay within 8192 tokens

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

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 2048,
            "n": 1,
            "temperature": code_verifier_gen_temp
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        # Process the response
        if response.status_code == 200:
            completion = response.json()
            response_content = completion['choices'][0]['message']['content']
            try:
                # Parse the response to extract code verifiers for each observation
                # This parsing logic may need to be adjusted based on the response format
                # For simplicity, we assume the response is a JSON object
                code_verifiers = json.loads(response_content)
                for observation in batch:
                    if observation in code_verifiers:
                        observations_with_code[observation] = code_verifiers[observation]
            except Exception as e:
                print(f"Error processing GPT-4 response: {e}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

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

    # List to store base64 encoded images
    image_contents = []

    # Create images for each example and collect them
    for idx, example in enumerate(task['train']):
        input_grid = example['input']
        output_grid = example['output']

        # Create the image representing the transformation
        img = create_transformation_image(input_grid, output_grid)

        # Save the image as a .png file
        image_filename = f"{task_id}_{idx+1}.png"
        img.save(image_filename)

        # Encode the image in base64
        with open(image_filename, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Collect the base64 image
        image_contents.append(base64_image)

    # Now, generate 256 observations in multiple calls
    observations = generate_observations(num_observations=256, examples=task['train'])

    # Classify observations into 'yes' and 'no'
    yes_observations, no_observations = classify_observations(observations)

    # Select the 16 best 'yes' observations
    best_yes_observations = select_best_observations(yes_observations, 16, 'easily verifiable by code and crucial to understanding the transformation')

    # Select the 16 best 'no' observations
    best_no_observations = select_best_observations(no_observations, 16, 'not easily verifiable by code but, if explored further, could provide valuable insights')

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
            # Generate 16 observations branching from this 'no' observation
            additional_context = f"Observation to expand upon:\n{no_observation}"
            observations = generate_observations(num_observations=16, examples=task['train'], additional_context=additional_context)
            # Classify observations
            yes_observations, no_observations = classify_observations(observations)
            # Select best observations
            best_yes_observations = select_best_observations(yes_observations, 16, 'easily verifiable by code and crucial to understanding the transformation')
            best_no_observations = select_best_observations(no_observations, 16, 'not easily verifiable by code but, if explored further, could provide valuable insights')
            # Add to lists
            observations_list.extend(best_yes_observations)
            new_nos.extend(best_no_observations)
        nos_list = new_nos

    # Now, break observations_list into blocks and generate code verifiers
    observations_with_code = generate_code_verifiers_for_block(observations_list, task['train'])

    # Validate the observations
    valid_observations = []
    for observation, code_dict in observations_with_code.items():
        all_codes_valid = True
        for code_verifier_name, code_str in code_dict.items():
            # Prepare the function definition
            code_str = code_str.strip()
            # Ensure that the function is defined
            if not code_str.startswith("def check_observation(input_grid, output_grid):"):
                print(f"Invalid function definition in {code_verifier_name} of observation '{observation}'.")
                all_codes_valid = False
                break
            # Execute the code to define the function
            local_vars = {}
            try:
                exec(code_str, globals(), local_vars)
                check_observation = local_vars['check_observation']
                all_hold = True
                # Test the observation on all training examples
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
                print(f"Error executing code for observation '{observation}': {e}")
                all_codes_valid = False
                break
        if all_codes_valid:
            valid_observations.append((observation, code_dict))

    # Print the valid observations with code verifiers
    print("\nValid Observations:")
    for observation, code_dict in valid_observations:
        print(f"\nObservation: {observation}")
        for code_verifier_name, code_str in code_dict.items():
            print(f"{code_verifier_name}:\n{code_str}\n")
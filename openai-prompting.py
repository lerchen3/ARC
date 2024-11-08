import os
os.environ['OPENAI_API_KEY'] = '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'  # Replace with your actual API key

import json
import base64
import requests
from PIL import Image, ImageDraw

api_key = os.environ['OPENAI_API_KEY']

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

# Now, process each task
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

    # Build the content list for the API call
    content_text = (
        "Please analyze the transformations shown in the following examples and provide 10 concrete observations about the nature of the transformations, the input grids, or the output grids. "
        "For example, a possible observation is that \"The input and output grid sizes are the same.\". "
        "Another example is that \"The input grid has contains many blue-colored three-block objects.\". "
        "Bottom line, help me understand the input, the output, and the transformation from just natural language. "
        "Be assertive and specific. For example, don't say \"There are multiple yellow objects in the input grid.\"; instead, a better and more assertive and specific observation would be to mention exactly how many objects there are."
        "Try to be very, very, very insighftul!"
        "Each observation should be a dictionary with keys \"NL Description\" and \"Observation code\". "
        "The \"Observation code\" should be code that takes in two grids and returns True if the description is indeed correct about the input-output pair. "
        "Be careful that the observation code verifies exactly the natural language description."
        "The observation code should be of the form \"def check_observation(input_grid, output_grid): ...\". "
        "Return only the list of observations in valid JSON format."
    )

    # Prepare the messages for the API
    messages = [
        {
            "role": "user",
            "content": content_text
        }
    ]

    # Add literal Python representations of the grids along with images
    for idx, (base64_image, example) in enumerate(zip(image_contents, task['train'])):
        input_grid = example['input']
        output_grid = example['output']

        # Convert grids to their literal Python representation
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
                "content": f"![](data:image/png;base64,{base64_image})"
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
        "max_tokens": 5000,  # Adjust as needed
        "n": 16,             # Generate 16 completions
        "temperature": 1.1   # Set temperature to 1.1 for diversity
    }

    # Send the request to the GPT-4 API
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )

    # Initialize the observations list
    observations = []

    # Process the response
    if response.status_code == 200:
        completion = response.json()

        # Iterate over each completion
        for choice in completion['choices']:
            # Extract the assistant's reply
            response_content = choice['message']['content']
            try:
                # Remove any leading/trailing text before and after the JSON array
                response_content = response_content.strip()

                # Find the first '[' and last ']' to extract the JSON array
                start_index = response_content.find('[')
                end_index = response_content.rfind(']') + 1

                if start_index == -1 or end_index == -1:
                    print("Could not find JSON array in the response.")
                    continue

                json_str = response_content[start_index:end_index]

                # Parse the JSON array
                parsed_list = json.loads(json_str)

                # Append observations to the list
                for item in parsed_list:
                    nl_description = item['NL Description']
                    observation_code = item['Observation code']
                    observations.append((nl_description, observation_code))

            except Exception as e:
                print(f"Error processing GPT-4 response: {e}")

        # Validate the observations
        valid_observations = []
        for description, code in observations:
            # Prepare the function definition
            code_str = code.strip()
            # Ensure that the function is defined
            if not code_str.startswith("def check_observation(input_grid, output_grid):"):
                print(f"Invalid function definition in observation code:\n{code_str}")
                continue

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

                if all_hold:
                    valid_observations.append((description, code))
            except Exception as e:
                print(f"Error executing code for observation '{description}': {e}")

        # Print the valid observations
        print("\nValid Observations:")
        for description, code in valid_observations:
            print(f"\nDescription: {description}\nCode:\n{code}")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)
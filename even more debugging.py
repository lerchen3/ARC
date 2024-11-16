best_yes_observations = ['**Color Addition**: The transformation introduces additional colors (yellow and red) not present in the input grid, indicating that the output grid incorporates new elements or rules that allow for color expansion.', '**Volume Increase**: The number of colored cells increases in the transformation, suggesting a process that not only redistributes but also amplifies the presence of colored elements.', '**Boundary Consistency**: The external grid dimensions remain unchanged throughout the transformation process, emphasizing that all changes occur internally. This boundary integrity suggests a contained transformation methodology rather than a chaotic expansion.', '**Structural Consistency**: While the patterns change, the overall structure of the grid remains intact, with cells remaining in their original positions but changing colors. This indicates that the transformation operates within the existing grid framework without altering cell positions.', '**Introduction of New Colors**: The output grid introduces new colors (red, yellow, and light blue), which are not present in the input grid, suggesting that the transformation applies rules that generate new states or colors based on existing patterns.', '**Retained Elements**: Certain elements from the input grid (like the green and red) are retained in their original positions or slightly modified, indicating a preservation of structural elements through the transformation.', '**Central Transformation Point**: The input grids consistently feature a central blue square that acts as a focal point for transformation, indicating that changes radiate outwards from this area.', '**Addition of New Colors**: New colors are introduced in the output grid (e.g., red, yellow) that do not appear in the input grid, suggesting that the transformation rules allow for the creation of new elements.', '**Spatial Integrity**: Despite the addition of new colors and shapes, the overall dimensions of the grid remain unchanged, which implies the transformation operates within the confines of the existing structure.', '**Reduction of Gray Areas**: The output grid has fewer gray areas compared to the input grid, which implies that the transformation is focused on enriching the grid with more defined color structures.', '**Color Introduction**: New colors (red, yellow, green) are introduced in the output grid, which were not present in the input grid, indicating that the transformation not only rearranges existing colors but also adds new elements.', '**Shift from Sparse to Dense**: The input grid is relatively sparse in color, while the output grid is dense with color presence, indicating a transformation that increases the overall saturation and complexity of the grid.', '**Consistency in Grid Size**: The dimensions of the grids remain unchanged throughout the transformation, indicating that the transformations are confined within the original boundaries without expanding or contracting the grid.', '**Color Transformation**: The transformation introduces new colors (like red, yellow, and blue) that were absent in the input grid, indicating that the transformation process involves both color change and addition.', '**Color Introduction**: New colors (such as yellow and red) emerge in the output grid that were not present in the input grid, suggesting that the transformation process includes color generation or alteration rules beyond mere replication.', '**Retention of Structure**: Some elements from the input grid (like the gray cells) remain unchanged in the output grid, showing that the transformation selectively enhances certain areas while leaving others intact.']
best_no_observations = ['**Central Focus Transformation**: The central blue square in the input grid acts as a focal point, from which colors are expanded outward in the output grid, suggesting a radial or diffusion-like transformation.', '**Central Element Expansion**: The blue cell in the center of the input grid serves as the catalyst for transformation, expanding outward into more complex patterns in the output grid.', '**Color Introduction**: New colors (such as red, yellow, and green) appear in the output grid that were not present in the input grid, indicating that the transformation rules allow for color generation based on existing patterns.', '**Color Connectivity**: In the output grid, colored areas tend to be connected, forming clusters rather than isolated cells. This suggests a rule that promotes adjacent cells sharing the same color.', '**Centralized Transformation**: The transformations are centered around a blue region in the input grid, which expands and evolves into a more complex pattern in the output grid, indicating a focus on that area during the transformation.', '**Central Transformation**: The transformation process begins with a small, centralized blue area, which serves as the focal point for the subsequent changes in the output grid.', '**Central Activation**: The transformation appears to initiate from a central point where the blue square is located, indicating that the transformation rules may radiate outward from this core.', '**Directional Growth**: The patterns emerging in the output suggest a directional growth, with colors branching out from the center to the edges of the grid. This could imply rules about how colors spread or influence their surroundings.', '**Spatial Influence**: The transformation may follow a rule where the color of a cell influences its neighbors, as seen by the spread of color from the center to the surrounding areas.', '**Central Expansion**: The transformation originates from a central blue square in the input grid, which expands into a more complex structure in the output grid, indicating a focus on the central elements in the transformation process.', '**Directional Expansion**: The transformation often extends in diagonal directions, creating a sense of movement or flow from the center. This indicates a directional influence in the transformation rules.', '**Local Interactions**: The transformation process appears to affect adjacent cells, with changes in one cell influencing nearby cells, creating a ripple effect that expands outwards from the original blue square.', '**Centrality of Blue**: The transformation begins with a prominent blue square in the center of the input grid, which serves as a focal point for the expansion of colors in the output grid.', '**Emergence of New Relationships**: The transformation establishes new relationships between colors, as seen in the way colors interact (e.g., red and yellow creating a cross-like structure) in the output grid, suggesting that the transformation rules promote interaction and connectivity among colors.', '**Color Proximity Effect**: The transformations seem to propagate colors from the center to surrounding areas, as seen with the blue influencing neighboring cells toward red and yellow, indicating a possible rule of color influence based on proximity.', '**Centralized Transformation**: The transformation appears to radiate from a central blue square in the input grid, indicating that the rules governing the transformation may prioritize central elements.']
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

MAX_SEARCH_DEPTH = 2

load_dotenv() 

# Initialize OpenAI client
client = OpenAI()

# Get task using the factory function
task = get_task('arc-agi_evaluation_challenges.json', '212895b5')
print(f"Processing task {task['task_id']}")


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


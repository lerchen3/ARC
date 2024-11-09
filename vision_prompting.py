import base64
import hashlib
import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Color mapping, including color 10 for the arrow
ARC_AGI_COLORS = [
    "#000000",  # Black
    "#0074D9",  # Blue
    "#FF4136",  # Red
    "#2ECC40",  # Green
    "#FFDC00",  # Yellow
    "#AAAAAA",  # Gray
    "#F012BE",  # Magenta
    "#FF851B",  # Orange
    "#7FDBFF",  # Cyan
    "#B10DC9",  # Brown
]

ARC_AGI_BACKGROUND_COLOR = "#000000"
ARC_AGI_GRID_COLOR = "#888888"
ARC_AGI_ARROW_COLOR = "#FFFFFF"


def create_transformation_image(
    input_grid: list[list[int]],
    output_grid: list[list[int]],
    save_location: Optional[str] = None,
    cache: bool = True,
    return_base64: bool = True,
) -> Optional[str]:
    """
    Given two grids, create a matplotlib figure showing the transformation between them.

    Parameters:
    ----------
    input_grid: list[list[int]]
        The input grid.
    output_grid: list[list[int]]
        The output grid.
    save_location: Optional[str]
        The location to save the figure. If not provided, the figure
        will be saved to a unique filename based on the input and output grids.
    cache: bool
        Whether to use cached figures. Defaults to True.
    return_base64: bool
        Whether to return the figure as a base64 string. Defaults to False.
    """
    os.makedirs("task_images", exist_ok=True)
    if save_location is None:
        # hash the input and output grids to create a unique filename
        save_location = f"task_images/{hashlib.md5((str(input_grid) + str(output_grid)).encode('utf-8')).hexdigest()}.png"

    if cache:
        if not os.path.exists(save_location):
            fig = _create_transformation_image(input_grid, output_grid)
            fig.savefig(save_location, dpi=300, bbox_inches='tight')
    else:
        fig = _create_transformation_image(input_grid, output_grid)
        fig.savefig(save_location, dpi=300, bbox_inches='tight')

    if return_base64:
        with open(save_location, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_image


def _create_transformation_image(
    input_grid: list[list[int]],
    output_grid: list[list[int]],
) -> plt.Figure:
    # Convert grids to numpy arrays for easier handling
    input_arr = np.array(input_grid)
    output_arr = np.array(output_grid)

    # Create figure with two subplots. Do not share y axis.
    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=False, figsize=(12, 4))
    fig.patch.set_facecolor(ARC_AGI_BACKGROUND_COLOR)  # Set figure background

    # Create custom colormap from ARC_AGI_COLORS
    custom_cmap = ListedColormap(ARC_AGI_COLORS)

    # Plot input grid on left subplot
    ax1.imshow(input_arr, cmap=custom_cmap, vmin=0, vmax=10)
    ax1.set_xticks(np.arange(-0.5, input_arr.shape[1], 1))
    ax1.set_yticks(np.arange(-0.5, input_arr.shape[0], 1))
    ax1.grid(True, color=ARC_AGI_GRID_COLOR, linewidth=2)
    ax1.set_xticklabels([])
    ax1.set_yticklabels([])
    ax1.set_facecolor(ARC_AGI_BACKGROUND_COLOR)
    # Add border
    for spine in ax1.spines.values():
        spine.set_color(ARC_AGI_GRID_COLOR)
        spine.set_linewidth(2)
        spine.set_visible(True)

    # Plot output grid on right subplot
    ax2.imshow(output_arr, cmap=custom_cmap, vmin=0, vmax=10)
    ax2.set_xticks(np.arange(-0.5, output_arr.shape[1], 1))
    ax2.set_yticks(np.arange(-0.5, output_arr.shape[0], 1))
    ax2.grid(True, color=ARC_AGI_GRID_COLOR, linewidth=1)
    ax2.set_xticklabels([])
    ax2.set_yticklabels([])
    ax2.set_facecolor(ARC_AGI_BACKGROUND_COLOR)
    # Add border
    for spine in ax2.spines.values():
        spine.set_color(ARC_AGI_GRID_COLOR)
        spine.set_linewidth(2)
        spine.set_visible(True)

    # Add arrow between subplots
    fig.canvas.draw()  # This is needed to get the correct transform coordinates

    # Get the coordinates for the arrow
    bbox1 = ax1.get_position()
    bbox2 = ax2.get_position()

    # Add arrow in figure coordinates
    arrow_x = bbox1.x1 + (bbox2.x0 - bbox1.x1) / 2
    arrow_y = (bbox1.y0 + bbox1.y1) / 2
    plt.figtext(arrow_x, arrow_y, '→', ha='center',
                va='center', fontsize=20, color=ARC_AGI_ARROW_COLOR)

    # Remove spacing between subplots
    plt.subplots_adjust(wspace=0.1)

    return fig


def main():
    """
    Test the functions.
    """
    from task import get_task
    task = get_task('arc-agi_training_challenges.json',
                    '007bbfb7', generate_images=False)
    test_input = task.train_examples[0]['input']
    test_output = task.train_examples[0]['output']
    create_transformation_image(test_input, test_output,
                                save_location='test_image.png')


if __name__ == "__main__":
    main()

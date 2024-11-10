FSP_RAW_REGULAR = [
    {
        "file_path": "arc-agi_training_challenges.json",
        "task_id": "007bbfb7",
        "input_grid": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        "output_grid": [[0, 2, 0], [2, 0, 2], [0, 2, 0]],
        "observation": "All blue pixels (color 1) are replaced with red pixels (color 2)",
        "verification_code": """
def verify(input_grid, output_grid):
    import numpy as np
    input_arr = np.array(input_grid)
    output_arr = np.array(output_grid)
    return np.all((input_arr == 1) == (output_arr == 2))
"""
    }
] 
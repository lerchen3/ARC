# DESCRIPTION: Example verification code for "hard to verify" observations; only used at end of searching
# (probably will delete).

FSP_RAW_DIFFICULT = [
    {
        "file_path": "arc-agi_training_challenges.json",
        "task_id": "complex_example",
        "input_grid": [[1, 0, 2], [0, 1, 0], [2, 0, 1]],
        "output_grid": [[1, 1, 2], [1, 1, 2], [2, 2, 1]],
        "observation": "Colors spread to adjacent cells while maintaining relative density ratios",
        "verification_code": """
def verify(input_grid, output_grid):
    import numpy as np
    from scipy.ndimage import label
    
    def get_color_ratios(grid):
        unique, counts = np.unique(grid, return_counts=True)
        total = np.sum(counts)
        return {color: count/total for color, count in zip(unique, counts)}
    
    def are_ratios_similar(ratio1, ratio2, tolerance=0.1):
        all_colors = set(ratio1.keys()) | set(ratio2.keys())
        return all(abs(ratio1.get(c, 0) - ratio2.get(c, 0)) <= tolerance for c in all_colors)
    
    input_arr = np.array(input_grid)
    output_arr = np.array(output_grid)
    
    # Check if color ratios are maintained within tolerance
    input_ratios = get_color_ratios(input_arr)
    output_ratios = get_color_ratios(output_arr)
    
    # Verify color spreading is only to adjacent cells
    for color in np.unique(input_arr):
        if color == 0:  # Skip background
            continue
        input_regions, _ = label(input_arr == color)
        output_regions, _ = label(output_arr == color)
        if not np.all(output_regions[input_arr == color] > 0):
            return False
    
    return are_ratios_similar(input_ratios, output_ratios)
"""
    }
] 
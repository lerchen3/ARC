# DESCRIPTION: "Easy to verify" observation selection from gpt-4.

FSP_RAW_REGULAR = [
    {
        "observations": [
            "**Expansion of Dimensions**: Each transformation results in an output grid with larger dimensions (typically 3 times wider and taller in the examples shown), indicating spatial expansion.",
            "**Color Retention**: The transformation maintains consistent color usage throughout each sequence. Each color present in the initial pattern remains consistent in the final pattern, suggesting that the transformation rules are color-independent.",
            "**Zero Dominance**: The black color (represented by 0) occupies a significant portion of the output grids, serving as a background while colored elements are embedded within it to create patterns.",
        ],
        "num_best": 2,
        "selected_observations": [
            "**Expansion of Dimensions**: Each transformation results in an output grid with larger dimensions, 3 times wider and taller in the examples shown, indicating spatial expansion.",
            "**Color Retention**: The transformation maintains consistent color usage throughout each sequence. Each color present in the initial pattern remains consistent in the final pattern, suggesting that the transformation rules are color-independent.",
        ]
    },
    {
        "observations": [
            "**Grid Dimensions**: Both the input and output grids maintain the same dimensions in each transformation pair, ensuring that the transformation rules are applied within a consistent spatial framework.",
            "**Central Focus**: Each transformation sequence begins with a central pattern surrounded by a mostly unaltered field of gray cells. This central focus then undergoes a transformation involving color changes and expansions outward.",
            "**Boundary Integrity**: The boundaries of the grid are unchanged, with transformations occurring internally without expanding or contracting the grid's external dimensions."
        ],
        "num_best": 1,
        "selected_observations": [
            "**Grid Dimensions**: Both the input and output grids maintain the same dimensions in each transformation pair, ensuring that the transformation rules are applied within a consistent spatial framework.",
        ]
    }
] 
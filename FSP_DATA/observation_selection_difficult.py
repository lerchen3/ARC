# DESCRIPTION: "Hard to verify" observation selection from gpt-4.

FSP_RAW_DIFFICULT = [
    {
        "observations": [
            "**Consistent Complexity Increase**: Each transformation increases the complexity in a consistent manner, implying that the rule applied is systematic and could be represented mathematically or algorithmically.",
            "**Pattern Consistency**: The final pattern in each sequence preserves some spatial characteristics of the initial pattern. This suggests that the transformation rule might involve a local duplication or scaling within each block of the original grid.",
            "**Non-linear Distribution**: Transition from the input grids to output grids does not maintain linear uniformity; rather, colors can cluster together or create isolated patches that do not follow a straightforward distribution.",
            "**Selective Surety**: Some colored areas in the input grids are entirely omitted in the output grids, indicating a selective transformation where certain colors or positional instances are favored over others.",
            "**Spatial Connectivity**: Some colored regions maintain relative proximity to their positions in the input grids, forming linked patterns like cross shapes or vertical columns in the output grids.",
            "**Transformation Complexity**: The transformations often exhibit complexity in shape; for example, the distinct color patterns within the output grid generate a visual discontinuity relative to the relatively simple input shapes, indicating more intricate design transformations."
        ],
        "num_best": 1,
        "selected_observations": [
            "**Pattern Consistency**: The final pattern in each sequence preserves some spatial characteristics of the initial pattern. This suggests that the transformation rule might involve a local duplication or scaling within each block of the original grid.",
        ]
    },
    {
        "observations": [
            "**Recurrent Colors**: Specific colors (like blue, yellow, red) appear repeatedly across different transformation scenarios, hinting at standardized roles or functions for these colors within the transformation rules.",
            "**Color Retention**: The transformation maintains consistent color usage throughout each sequence. Each color present in the initial pattern remains consistent in the final pattern, suggesting that the transformation rules are color-independent.",
            "**Symmetry and Patterns**: There is a visible tendency towards creating symmetrical or patterned arrangements in the output grids, suggesting that the transformation rules may prioritize or result in organized structures.",
            "**No Isolation of Colors**: Colors in the output grids are generally connected to each other or to cells of the same color, indicating that isolated cells of a particular color in the output are rare, which may suggest rules about continuity or clustering.",
            "**Symmetrical Expansion**: The pattern expansion in the final images is symmetrical, suggesting that the transformation rules apply equally in each direction from the center.",
            "**Pattern Growth**: In all sequences, the central pattern grows into a larger configuration that includes arms extending diagonally outward. This suggests a rule in the transformation process that replicates or extends the pattern outward from the center in specific directions.",
            "**Visible Transformation Pathways**: The transformations generally show a progression or pathway of change, such as a blue cell influencing its immediate neighbors, which then might transform into red or yellow. This stepwise change implies a rule set that might mimic diffusion or influence spreading from a point of origin."
        ],
        "num_best": 2,
        "selected_observations": [
            "**Symmetrical Expansion**: The pattern expansion in the final images is symmetrical, suggesting that the transformation rules apply equally in each direction from the center.",
            "**Pattern Growth**: In all sequences, the central pattern grows into a larger configuration that includes arms extending diagonally outward. This suggests a rule in the transformation process that replicates or extends the pattern outward from the center in specific directions."
        ]
    }
] 
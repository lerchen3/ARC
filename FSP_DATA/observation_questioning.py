# DESCRIPTION: Example questions for breaking down observations into refinable components.

FSP_RAW = [
    {
        # 007bbfb7
        "observation": "**Pattern Consistency**: The final pattern in each sequence preserves some spatial characteristics of the initial pattern. This suggests that the transformation rule might involve a local duplication or scaling within each block of the original grid.",
        "questions": [
            "Does the transformation involve exact duplication of any part of the input pattern?",
            "Are there specific blocks or regions where scaling occurs consistently?",
            "What spatial characteristics are specifically preserved between input and output?",
            "Is the preservation of patterns uniform across all regions of the grid?",
            "Can we identify a consistent scaling factor in regions where scaling occurs?"
        ]
    },
    {
        # 212895b5
        "observation": "**Symmetrical Expansion**: The pattern expansion in the final images is symmetrical, suggesting that the transformation rules apply equally in each direction from the center.",
        "questions": [
            "Is the symmetry perfectly mirrored across both horizontal and vertical axes?",
            "Does the expansion maintain equal distances from the center in all directions?",
            "Are there specific colors that maintain symmetrical relationships?",
            "Does the symmetrical expansion follow a consistent mathematical ratio?",
            "Are there any asymmetrical elements that break the overall pattern?"
        ]
    },
    {
        # 212895b5
        "observation": "**Pattern Growth**: In all sequences, the central pattern grows into a larger configuration that includes arms extending diagonally outward.",
        "questions": [
            "Is the diagonal growth pattern consistent in all examples?",
            "What is the exact angle of the diagonal extensions?",
            "Do all arms extend to the same length?",
            "Is there a mathematical relationship between input size and arm length?",
            "Are the diagonal arms composed of the same colors as the central pattern?"
        ]
    }
] 
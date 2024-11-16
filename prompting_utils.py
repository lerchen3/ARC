def grid_to_python_literal(grid: list[list[int]]) -> str:
    """
    Convert a grid to its literal Python representation.
    """
    return repr(grid)

def format_additional_context(questions: list[str], original_observation: str = "") -> str:
    """Format additional context with consistent wrapper text.
    
    Parameters:
    ----------
    questions: list[str]
        A list of questions
    original_observation: str, optional
        The original observation being refined, if any
        
    Returns:
    -------
    str
        Formatted context with consistent wrapper text
    """
    formatted = (
        "Here's an observation I made. For all of the observations "
        "you give, please address these specific questions about the base observation:\n"
        f"{questions}"
    )
    
    if original_observation:
        formatted += f"\n\n Base observation:\n{original_observation}"
    
    return formatted
def load_prompt(filename: str) -> str:
    """
    Load the prompt from a text file.

    Args:
        filename (str): The path to the text file containing the prompt.

    Returns:
        str: The prompt text.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        prompt = file.read().strip()
    return prompt

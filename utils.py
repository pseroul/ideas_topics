
def format_text(name: str, description: str) -> str:
        """
        Format text for storage in the embedding database.
        
        Formats the name and description into a structured string for embedding generation.
        
        Args:
            name (str): The name/title of the data item
            description (str): The description/content of the data item
            
        Returns:
            str: Formatted string combining name and description
        """
        return f"{name}. {name}: {description}"
    
def unformat_text(name: str, description: str) -> str:
    """
    Unformat text from the embedding database storage format.
    
    Reverses the formatting applied by format_text, extracting the original
    description from the stored formatted string.
    
    Args:
        name (str): The name/title of the data item
        description (str): The formatted description from the database
        
    Returns:
        str: Extracted original description
    """
    return description.replace(f"{name}. {name}:", "")
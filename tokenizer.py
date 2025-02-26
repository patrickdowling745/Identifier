def analyze_parcel_id(pid):
    '''
    Purpose:
        Analyzes a parcel ID to determine its structure and character composition.
    Parameters:
        pid (str): The parcel ID string to analyze.
    
    Returns:
        A dictionary with:
            pattern (str): Format of the string (N for numbers, A for letters, special characters as-is).
            numbers (int): Count of numeric characters.
            alphabets (int): Count of alphabetic characters.
            spaces (int): Count of space characters.
            special_characters (int): Count of special characters (excluding spaces).
            length (int): Total length of the string.
    '''
    counts = {
        'numbers': 0, 
        'alphabets': 0, 
        'spaces': 0,
        'special_characters': 0, 
        'length': len(pid)
    }
    tokens = []
    
    for char in pid:
        if char.isdigit():
            tokens.append('N')  # Number
            counts['numbers'] += 1
        elif char.isalpha():
            tokens.append('A')  # Alphabet
            counts['alphabets'] += 1
        elif char.isspace():
            tokens.append('_')  # Space character represented as underscore
            counts['spaces'] += 1
        else:
            tokens.append(char)  # Other special character
            counts['special_characters'] += 1
    pattern = "".join(tokens)
    return {
        'pattern': pattern,
        **counts
    }

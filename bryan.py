import re
from typing import List, Dict

def extract_pattern(value: str):
    if not isinstance(value, str):
        return None

    pattern = re.sub(r'[A-Za-z]', 'A', value)
    pattern = re.sub(r'[0-9]', '0', pattern)
    pattern = re.sub(r'\W', '-', pattern)

    return pattern
parcel = '123-45-6789'

result = extract_pattern(parcel)
print(result)




# Function to suggest corrections
def suggest_correction(value: str, dominant_pattern: str):
    if not value or not dominant_pattern:
        return "No suggestion"
    # Example: Insert missing dashes based on dominant pattern
    corrected: List[str] = []
    for v_char, p_char in zip(value.ljust(len(dominant_pattern), ' '), dominant_pattern):
        if p_char == 'A' and not v_char.isalpha():
            corrected.append('A')  # Suggest a letter
        elif p_char == '0' and not v_char.isdigit():
            corrected.append('0')  # Suggest a digit
        elif p_char == '-' and v_char != '-':
            corrected.append('-')  # Suggest a dash
        else:
            corrected.append(v_char)

    return ''.join(corrected).strip()

result = suggest_correction('12345678', '000-A0-0000')





def validate_against_schema(value: str, patterns: Dict[str, int]):
    pattern = extract_pattern(value)
    if pattern in patterns:
        return True, None, pattern  # Valid
    else:
        # Suggest correction (simple example: show expected and actual)
        expected = list(patterns.keys())[0]  # Take the most common pattern
        return False, f"Expected pattern {expected}, but got {pattern}", pattern
    

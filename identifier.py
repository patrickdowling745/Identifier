import streamlit as st
import pandas as pd
import re

st.title("Property Identifier Tool")

st.subheader("Instructions:")
st.markdown(
    """

1. **Input a valid (correctly formatted) Parcel ID**  
   - For example: `12-345.6789` or `123-45.67-890`

2. **Upload your file**  
   - Choose a CSV file containing the Parcel IDs you want to reformat.

3. **Select the column containing Parcel IDs**  
   - The script will take those Parcel IDs, strip out everything except digits, then re-insert dashes and periods using your example pattern.

4. **Download the reformatted file**  
   - After the Parcel IDs are reformatted, download the CSV and use it in your scripts.
   
5. **Test the reformatted Parcel IDs in scraping scripts or other tools.** 
    - [TaxProper Recorder](https://recorder.taxproper.com)
    - [BrowseAi](https://browse.ai)


**Important Notes**:  
   - The script will return "Unable to reformat" if the final string does not match the input example's length.
   - It is possible that counties have multiple character lengths for Parcel IDs. This script assumes a consistent length. Retry with other examples if needed.
"""
)

# -----------------------------------------------------------------------------
# 1. Parse the format from the example parcel: find digits and positions of '-' or '.'
# -----------------------------------------------------------------------------
def parse_parcel_format(parcel_str):
    """
    Given an example Parcel ID with digits, dashes, and/or periods, return:
      1) A string of all digits (stripped from any separators)
      2) A list of (position, character) where `character` is '-' or '.' 
         and `position` is the index among the digits.
    
    Example:
       Input: "12.34-567"
       Digits extracted: "1234567"
       insertion_points: [(2, '.'), (4, '-')]
    """
    # Extract just the digits
    digits_only = re.sub(r"\D", "", parcel_str)

    digit_count_so_far = 0
    insertion_points = []

    # Go through the example string, character by character
    for char in parcel_str:
        if char.isdigit():
            digit_count_so_far += 1
        else:
            # Record only dashes/periods as separators
            if char in ['-', '.']:
                insertion_points.append((digit_count_so_far, char))
    return digits_only, insertion_points


# -----------------------------------------------------------------------------
# 2. Insert dashes/periods into a new string of digits based on the insertion points
# -----------------------------------------------------------------------------
def format_parcel_id(digits_str, insertion_points):
    """
    Insert the stored characters (dashes/periods) at the specified positions
    in the digits string.

    insertion_points is a list of (position, char), where position is the number
    of digits after which we insert `char`.
    """
    output = digits_str

    # Insert from the right to left so we don't mess up the indices
    for pos, char in reversed(insertion_points):
        if pos <= len(output):
            output = output[:pos] + char + output[pos:]
        else:
            # If position is beyond the length, decide how to handle it.
            # Here, we append, but you could also skip or handle differently.
            output = output + char

    return output


# -----------------------------------------------------------------------------
# 3. Helper to apply the discovered pattern (remove non-digits, then insert),
#    and finally enforce length-check.
# -----------------------------------------------------------------------------
def detect_and_format_parcel(parcel_id, insertion_points, target_length):
    """
    1) Strips all non-digits from the raw parcel_id.
    2) Inserts dashes/periods according to insertion_points.
    3) If the final string's length != target_length, return None.
    """
    # Remove all non-digits
    digits_str = re.sub(r"\D", "", parcel_id)

    # If no digits found, return None
    if not digits_str:
        return None

    # Re-insert the known separators
    final_str = format_parcel_id(digits_str, insertion_points)

    # Enforce length-check
    if len(final_str) != target_length:
        return "Unable to reformat"

    return final_str


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

# 1. User inputs a "correctly formatted" (example) Parcel ID
example_parcel = st.text_input("Enter a valid, correctly formatted Parcel ID (e.g., 12-345.6789)")

# 2. Upload a CSV file
if example_parcel:
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of the uploaded file:")
        st.write(df.head())

        # Let user choose which column has the Parcel IDs
        columns = df.columns.tolist()
        header_column = st.selectbox("Select the column that contains Parcel IDs", columns)

        if example_parcel and header_column:
            # Parse the example for digits & insertion points
            base_digits, insertion_points = parse_parcel_format(example_parcel)
            # We'll use the EXACT length of the example parcel as the target.
            target_length = len(example_parcel.strip())  # Trim spaces, just in case

            # Apply the detected pattern to the user's file
            df["Reformatted_Parcel_ID"] = df[header_column].astype(str).apply(
                lambda x: detect_and_format_parcel(x, insertion_points, target_length)
            )

            st.write("Reformatted Parcel IDs (preview):")
            st.write(df[["Reformatted_Parcel_ID"]].head())

            # Provide a download link
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download Reformatted CSV",
                data=csv_data,
                file_name="reformatted_parcel_ids.csv",
                mime="text/csv"
            )
        else:
            st.info("Please provide an example Parcel ID and select your Parcel ID column.")


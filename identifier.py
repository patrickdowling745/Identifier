import streamlit as st
import pandas as pd
import re

st.title("Property Identifier Tool")

st.subheader("Instructions:")
st.markdown(
    """
1. **Input a valid (correctly formatted) Parcel ID**  
   - For example: 12-345.6789 or 123-45.67-890

2. **Upload your file**  
   - Choose a CSV file containing the Parcel IDs you want to reformat.

3. **Select the column containing Parcel IDs**  
   - The script will take those Parcel IDs, strip out everything except digits, then re-insert dashes and periods using your example pattern.

4. **Click Submit to Reformat**  
   - After selecting the column, click the button to run the transformation.

5. **Download the reformatted file**  
   - After the Parcel IDs are reformatted, download the CSV and use it in your scripts.
   
6. **Test the reformatted Parcel IDs in scraping scripts or other tools.** 
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
      2) A list of (position, character) where character is '-' or '.' 
         and position is the index among the digits.
    
    Example:
       Input: "12.34-567"
       Digits extracted: "1234567"
       insertion_points: [(2, '.'), (4, '-')]
    """
    digits_only = re.sub(r"\D", "", parcel_str)
    digit_count_so_far = 0
    insertion_points = []

    for char in parcel_str:
        if char.isdigit():
            digit_count_so_far += 1
        else:
            if char in ['-', '.']:
                # Record the index position among digits and the special char
                insertion_points.append((digit_count_so_far, char))
    return digits_only, insertion_points


# -----------------------------------------------------------------------------
# 2. Insert dashes/periods into a new string of digits based on the insertion points
# -----------------------------------------------------------------------------
def format_parcel_id(digits_str, insertion_points):
    """
    Insert the stored characters (dashes/periods) at the specified positions
    in the digits string.
    """
    output = digits_str

    # Insert from right to left so we don't mess up indices after insertion
    for pos, char in reversed(insertion_points):
        if pos <= len(output):
            output = output[:pos] + char + output[pos:]
        else:
            output = output + char

    return output


# -----------------------------------------------------------------------------
# 3. Helper to apply the discovered pattern and enforce length-check
# -----------------------------------------------------------------------------
def detect_and_format_parcel(parcel_id, insertion_points, target_length):
    """
    1) Strip non-digits.
    2) Insert dashes/periods.
    3) Enforce final string length.
    """
    digits_str = re.sub(r"\D", "", parcel_id)
    if not digits_str:
        return None  # No digits at all
    final_str = format_parcel_id(digits_str, insertion_points)
    if len(final_str) != target_length:
        return "Unable to reformat"
    return final_str


# -----------------------------------------------------------------------------
# 4. Break the final reformatted string into digit-only parts based on insertion points
# -----------------------------------------------------------------------------
def get_parts(reformatted_str, insertion_points):
    """
    1) If the parcel is "Unable to reformat", return an empty list.
    2) Otherwise, remove non-digit characters and slice into segments
       using the insertion points from the example Parcel ID.
    """
    if reformatted_str in [None, "Unable to reformat"]:
        return []
    # Remove dashes/periods (or any non-digits)
    digits_str = re.sub(r"\D", "", reformatted_str)

    parts = []
    start = 0
    for pos, _char in insertion_points:
        parts.append(digits_str[start:pos])
        start = pos
    # Append the remaining segment
    parts.append(digits_str[start:])
    return parts


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

# Step 1: Input a "correctly formatted" Parcel ID
example_parcel = st.text_input("Enter a valid, correctly formatted Parcel ID (e.g., 12-345.6789)")

# Step 2: Upload a CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Only proceed if we have both an example Parcel and a file
if example_parcel and uploaded_file:
    # Read the file
    df = pd.read_csv(uploaded_file)
    st.write("Preview of the uploaded file:")
    st.write(df.head())

    # Let the user select which column contains Parcel IDs
    columns = df.columns.tolist()
    header_column = st.selectbox("Select the column that contains Parcel IDs", columns)

    # Add a button to explicitly trigger the reformatting
    if st.button("Submit"):
        # Parse the example to get digits & insertion points
        base_digits, insertion_points = parse_parcel_format(example_parcel)
        target_length = len(example_parcel.strip())  # We assume the example's length is the standard

        # Apply the detected pattern to the selected column
        df["Reformatted_Parcel_ID"] = df[header_column].astype(str).apply(
            lambda x: detect_and_format_parcel(x, insertion_points, target_length)
        )

        # Create new columns for each digit-only part using insertion points
        df_parts = df["Reformatted_Parcel_ID"].apply(lambda x: get_parts(x, insertion_points))
        max_parts = df_parts.apply(len).max()

        # Dynamically create new columns for each part
        for i in range(max_parts):
            df[f"Part_{i+1}"] = df_parts.apply(
                lambda x: x[i] if i < len(x) else ""
            )

        st.write("Reformatted Parcel IDs (with parts in separate columns):")
        st.write(df.head())  # Display only head as a preview

        # Provide a download link for the updated file
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download Reformatted CSV",
            data=csv_data,
            file_name="reformatted_parcel_ids_with_parts.csv",
            mime="text/csv"
        )
    else:
        st.write("Select your column above and then click **Submit** to reformat the Parcel IDs.")
elif example_parcel:
    # If there's an example parcel but no file, prompt user to upload
    st.info("Please upload a CSV file to continue.")
elif uploaded_file:
    # If there's a file but no example parcel, prompt user for example
    st.info("Please enter a valid example Parcel ID to continue.")
else:
    # Neither file nor example provided
    st.info("Enter an example Parcel ID and upload a CSV to begin.")



import streamlit as st
import pandas as pd
import re

st.title("Property Identifier Tool")

st.subheader("Instructions:")
st.markdown(
    """
1. **Input multiple valid (correctly formatted) Parcel IDs** (one example at a time)  
   - Click "**Add Example Format**" each time. For example, you might add:
       - 06F-04069O
       - 07F-08028M

2. **Upload your file**  
   - Choose a CSV file containing the Parcel IDs you want to reformat.

3. **Select the column containing Parcel IDs**  
   - The script will take those Parcel IDs, strip out everything except letters/digits, then try **each** known format to see if it can be reformatted correctly.

4. **Click Submit to Reformat**  
   - After selecting the column, click the button to run the transformation.

5. **Download the reformatted file**  
   - After the Parcel IDs are reformatted, download the CSV and use it in your scripts.
   
6. **Test the reformatted Parcel IDs in scraping scripts or other tools.** 
   - [TaxProper Recorder](https://recorder.taxproper.com)
   - [BrowseAi](https://browse.ai)

**Important Notes**:  
   - The script returns "**Unable to reformat**" if none of your provided formats match the row’s Parcel ID.
   - Some counties have multiple lengths/formats for Parcel IDs. Enter **all** relevant examples (one at a time).
   - The script will use the **first** format that matches each Parcel ID.  
   - If you want separate digit/letter segments (Part_1, Part_2, etc.), the script will figure out which format was used for that row and split accordingly.
"""
)

# -----------------------------------------------------------------------------
# 1. Parse the format from a single example Parcel
#    (Preserves letters as well as digits)
# -----------------------------------------------------------------------------
def parse_parcel_format(parcel_str):
    """
    Given an example Parcel ID with alphanumeric characters plus possible dashes/periods, 
    return:
      1) A string of all letters/digits (stripped of punctuation/spaces)
      2) A list of (position, character) where character is '-' or '.' 
         and position is the index among the alphanumeric characters.
      3) The total length (including alphanumeric + separators) 
         of the final, properly formatted parcel string.
    """
    # Keep only letters and digits (remove punctuation, spaces, etc.)
    alphanumeric_str = re.sub(r'[^a-zA-Z0-9]', '', parcel_str)
    
    char_count_so_far = 0
    insertion_points = []

    for char in parcel_str:
        # If it's a letter or digit, increment the counter
        if re.match(r'[a-zA-Z0-9]', char):
            char_count_so_far += 1
        else:
            # If it's a dash or period, record an insertion point
            if char in ['-', '.']:
                insertion_points.append((char_count_so_far, char))

    target_length = len(parcel_str.strip())  # length of the example (alphanumeric + separators)
    return alphanumeric_str, insertion_points, target_length


# -----------------------------------------------------------------------------
# 2. Insert dashes/periods into a string of alphanumeric chars based on insertion points
# -----------------------------------------------------------------------------
def format_parcel_id(alphanumeric_str, insertion_points):
    """
    Insert the stored characters (dashes/periods) at the specified positions
    in the alphanumeric string.
    """
    output = alphanumeric_str
    # Insert from right to left so we don't disrupt subsequent indices
    for pos, char in reversed(insertion_points):
        if pos <= len(output):
            output = output[:pos] + char + output[pos:]
        else:
            output += char
    return output


# -----------------------------------------------------------------------------
# 3. Attempt a single format
# -----------------------------------------------------------------------------
def attempt_format(parcel_id, fmt):
    """
    1) Strip punctuation/spaces (keep letters/digits)
    2) Insert dashes/periods according to the example format
    3) Enforce final string length
    """
    # Keep only letters and digits
    alphanumeric_str = re.sub(r'[^a-zA-Z0-9]', '', parcel_id)
    if not alphanumeric_str:
        return "Unable to reformat"

    insertion_points = fmt["insertion_points"]
    target_length = fmt["target_length"]

    final_str = format_parcel_id(alphanumeric_str, insertion_points)
    if len(final_str) != target_length:
        return "Unable to reformat"
    return final_str


# -----------------------------------------------------------------------------
# 4. Try multiple formats; return first that works
# -----------------------------------------------------------------------------
def detect_and_format_multi(parcel_id, all_formats):
    """
    Go through each known format in 'all_formats'.
    Return the first that produces a valid final length.
    If none fit, return "Unable to reformat".
    """
    for f in all_formats:
        candidate = attempt_format(parcel_id, f)
        if candidate != "Unable to reformat":
            return candidate
    return "Unable to reformat"


# -----------------------------------------------------------------------------
# 5. Determine which format actually worked, then split into parts
# -----------------------------------------------------------------------------
def get_parts_for_multi(original_val, all_formats):
    """
    1) For the given 'original_val', figure out which format actually works 
       (the first that yields a valid reformat).
    2) Use that format's insertion_points to split the alphanumeric string.
    3) Return a list of segments (e.g. ['06F', '04069', 'O']) 
       or [] if no format matches.
    """
    for f in all_formats:
        candidate = attempt_format(original_val, f)
        if candidate != "Unable to reformat":
            # We found the correct format; now extract parts
            alphanumeric_str = re.sub(r'[^a-zA-Z0-9]', '', candidate)
            insertion_points = f["insertion_points"]

            parts = []
            start = 0
            for pos, _char in insertion_points:
                parts.append(alphanumeric_str[start:pos])
                start = pos
            # Remainder
            parts.append(alphanumeric_str[start:])
            return parts
    # If none matched
    return []


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

# We'll store all valid formats in session_state so the user can add multiple
if "all_formats" not in st.session_state:
    st.session_state.all_formats = []

st.subheader("Add Multiple Parcel ID Formats")
with st.form(key="example_form", clear_on_submit=True):
    example_parcel = st.text_input("Enter a valid example Parcel ID (e.g., 06F-04069O)")
    add_btn = st.form_submit_button("Add Example Format")

    if add_btn and example_parcel.strip():
        base_alnum, insertion_points, target_length = parse_parcel_format(example_parcel)
        # Store it as a dict
        st.session_state.all_formats.append({
            "insertion_points": insertion_points,
            "target_length": target_length
        })
        st.success(f"Added new format: {example_parcel}")

# Display the currently known formats
if st.session_state.all_formats:
    st.markdown("**Current Known Formats:**")
    for i, fdata in enumerate(st.session_state.all_formats, start=1):
        st.write(
            f"- Format {i}: insertion_points={fdata['insertion_points']}, "
            f"target_length={fdata['target_length']}"
        )
else:
    st.info("No formats added yet. Please enter at least one example above.")

st.markdown("---")

# Step 2: Upload a CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Only proceed if at least one format is known & user uploaded a file
if st.session_state.all_formats and uploaded_file:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    st.write("Preview of the uploaded file:")
    st.write(df.head())

    # Let the user select which column has Parcel IDs
    columns = df.columns.tolist()
    header_column = st.selectbox("Select the column that contains Parcel IDs", columns)

    # Button to reformat
    if st.button("Submit to Reformat"):
        # Create a new column with the reformatted ID
        df["Reformatted_Parcel_ID"] = df[header_column].astype(str).apply(
            lambda x: detect_and_format_multi(x, st.session_state.all_formats)
        )

        # Create separate Part_X columns
        df_parts = df[header_column].astype(str).apply(
            lambda x: get_parts_for_multi(x, st.session_state.all_formats)
        )
        max_parts = df_parts.apply(len).max()
        for i in range(max_parts):
            df[f"Part_{i+1}"] = df_parts.apply(lambda p: p[i] if len(p) > i else "")

        st.write("Reformatted Parcel IDs (with parts in separate columns):")
        st.write(df.head())  # Show a preview

        # Provide a download link
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download Reformatted CSV",
            data=csv_data,
            file_name="reformatted_parcel_ids_with_parts.csv",
            mime="text/csv"
        )
    else:
        st.write("Select your column above and then click **Submit to Reformat**.")
elif uploaded_file:
    st.info("Please add at least one valid Parcel ID example (above) before reformatting.")
elif st.session_state.all_formats:
    st.info("Please upload a CSV file to continue.")
else:
    st.info("Add an example format and upload a CSV to begin.")

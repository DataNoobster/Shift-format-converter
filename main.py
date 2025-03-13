import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io


# Function to process the uploaded Excel file (unchanged)
def process_excel_with_runtime_and_output(df: pd.DataFrame):
    try:
        required_columns = {"Weaving Date", "Loom", "Shift", "Base Date and Time", "Pick Counter", "Running Status"}
        if not required_columns.issubset(df.columns):
            missing_columns = required_columns - set(df.columns)
            st.error(f"Missing required columns: {missing_columns}")
            return pd.DataFrame()

        df["Base Date and Time"] = pd.to_datetime(df["Base Date and Time"], errors="coerce")
        df["Pick Counter"] = pd.to_numeric(df["Pick Counter"], errors="coerce")
        df.dropna(subset=["Base Date and Time", "Pick Counter", "Running Status"], inplace=True)
        df.sort_values(by=["Weaving Date", "Loom", "Base Date and Time"], ascending=True, inplace=True)

        shift_times = {
            "A": (pd.Timestamp("07:00:00").time(), pd.Timestamp("14:59:59").time()),
            "B": (pd.Timestamp("15:00:00").time(), pd.Timestamp("23:59:59").time()),
            "C": (pd.Timestamp("00:00:00").time(), pd.Timestamp("06:59:59").time())
        }

        for shift, (start_time, end_time) in shift_times.items():
            shift_df = df[df["Shift"] == shift].copy()
            for loom in shift_df["Loom"].unique():
                loom_shift_df = shift_df[shift_df["Loom"] == loom]
                first_five_indices = loom_shift_df.index[:5]
                df.loc[first_five_indices, "Pick Counter"] = 0

        def calculate_runtime(group):
            try:
                group = group.sort_values("Base Date and Time")
                group["Prev Status"] = group["Running Status"].shift(1)
                starts = group[(group["Running Status"].isin(["RUNNING", "START"])) & (group["Prev Status"] == "STOP")]["Base Date and Time"]
                ends = group[(group["Running Status"] == "STOP") & (group["Prev Status"].isin(["RUNNING", "START"]))]["Base Date and Time"]

                total_runtime = 0
                if not starts.empty and not ends.empty:
                    for start in starts:
                        if pd.isna(start):
                            continue
                        next_end = ends[ends > start]
                        if not next_end.empty:
                            end = next_end.iloc[0]
                            if pd.isna(end):
                                continue
                            runtime = (end - start).total_seconds()
                            if runtime >= 0:
                                total_runtime += runtime
                return total_runtime
            except:
                return 0

        results = []
        for (loom, date), group in df.groupby(["Loom", "Weaving Date"]):
            group = group.copy()
            group["Time"] = group["Base Date and Time"].dt.time

            aa_start = pd.Timestamp("07:00:00").time()
            aa_end = pd.Timestamp("18:59:59").time()
            bb_start = pd.Timestamp("19:00:00").time()
            bb_end = pd.Timestamp("06:59:59").time()

            aa_mask = (group["Time"] >= aa_start) & (group["Time"] <= aa_end)
            bb_mask = ((group["Time"] >= bb_start) & (group["Time"] <= pd.Timestamp("23:59:59").time())) | \
                      ((group["Time"] >= pd.Timestamp("00:00:00").time()) & (group["Time"] <= bb_end))

            aa_group = group[aa_mask]
            bb_group = group[bb_mask]

            if not aa_group.empty:
                a_mask = (aa_group["Shift"] == "A") & (aa_group["Time"] <= shift_times["A"][1])
                shift_a_max = aa_group[a_mask]["Pick Counter"].max() if not aa_group[a_mask].empty else 0
                b_mask = (aa_group["Shift"] == "B") & (aa_group["Time"] <= aa_end)
                shift_b_interim = aa_group[b_mask]["Pick Counter"].iloc[-1] if not aa_group[b_mask].empty else 0
                total_output_aa = shift_a_max + shift_b_interim
                runtime_aa = calculate_runtime(aa_group)
                start_date_aa = aa_group["Base Date and Time"].min().date()

                results.append({
                    "Loom": loom,
                    "Date": start_date_aa,
                    "Shift": "AA",
                    "Runtime": pd.to_timedelta(runtime_aa, unit="s").__str__().split()[-1],
                    "Total Output": total_output_aa
                })

            if not bb_group.empty:
                b_full_mask = (bb_group["Shift"] == "B") & (bb_group["Time"] <= shift_times["B"][1])
                shift_b_max = bb_group[b_full_mask]["Pick Counter"].max() if not bb_group[b_full_mask].empty else 0
                b_interim_mask = (group["Shift"] == "B") & (group["Time"] <= aa_end)
                shift_b_interim = group[b_interim_mask]["Pick Counter"].iloc[-1] if not group[b_interim_mask].empty else 0
                shift_b_contribution = max(0, shift_b_max - shift_b_interim)
                c_mask = (bb_group["Shift"] == "C") & (bb_group["Time"] <= shift_times["C"][1])
                shift_c_max = bb_group[c_mask]["Pick Counter"].max() if not bb_group[c_mask].empty else 0
                total_output_bb = shift_b_contribution + shift_c_max
                runtime_bb = calculate_runtime(bb_group)
                start_date_bb = bb_group["Base Date and Time"].min().date()

                results.append({
                    "Loom": loom,
                    "Date": start_date_bb,
                    "Shift": "BB",
                    "Runtime": pd.to_timedelta(runtime_bb, unit="s").__str__().split()[-1],
                    "Total Output": total_output_bb
                })

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

# Optimized Streamlit UI/UX
st.set_page_config(page_title="Shift Format Converter", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5em;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .description {
        font-size: 1.1em;
        color: #555;
        text-align: center;
        margin-bottom: 2em;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5em 1em;
    }
    .stButton>button:hover {
        background-color: #135e96;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar configuration
logo_path_2 = "./skilltelligent_1.jpeg"
skilltelligent_logo = Image.open(logo_path_2)
with st.sidebar:
    st.image(skilltelligent_logo, width=100)
    st.markdown("<strong style='color: #e0e0e0;'>Designed by Skilltelligent</strong>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Upload an Excel file (.xlsx) with weaving data.
    2. Ensure it contains required columns: 
       - Weaving Date
       - Loom
       - Shift
       - Base Date and Time
       - Pick Counter
       - Running Status
    3. Download the transformed data after processing.
    """)
    st.info("File processing may take a moment depending on size.")

# Main content
st.markdown('<div class="main-title">Shift Format Converter</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Transform your old shift-wise weaving data into the new shift format with runtime and output calculations.</div>', unsafe_allow_html=True)

# File uploader with enhanced styling and help text
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"],
    help="Upload an Excel file containing weaving data in the old shift format.",
    key="file_uploader"
)

if uploaded_file is not None:
    with st.spinner("Processing your file..."):
        try:
            df = pd.read_excel(uploaded_file)
            st.success("✅ File uploaded successfully!")
            
            processed_df = process_excel_with_runtime_and_output(df)
            
            if not processed_df.empty:
                # Display data preview in a cleaner layout
                st.subheader("Transformed Data Preview")
                with st.expander("View Processed Data", expanded=True):
                    st.dataframe(
                        processed_df.style.format({"Total Output": "{:.0f}"}),
                        height=300,
                        use_container_width=True
                    )

                # Download button with better placement and styling
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    processed_df.to_excel(writer, index=False, sheet_name="Shift Data")
                output.seek(0)

                st.download_button(
                    label="Download Transformed Data",
                    data=output,
                    file_name=f"new_shift_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_button"
                )
            else:
                st.warning("⚠️ No valid data to display after processing.")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
else:
    st.info("Please upload an Excel file to begin.")
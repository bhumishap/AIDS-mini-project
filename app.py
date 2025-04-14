import streamlit as st
import pandas as pd
import os
import nbformat
import matplotlib
import seaborn
import sklearn

# Function to load the notebook as a module
def load_ipynb_module(notebook_path):
    """
    Load functions from an ipynb file (using exec)
    This is a workaround to import functions from Jupyter notebook
    """
    # Load the notebook using nbformat
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook_content = nbformat.read(f, as_version=4)
    
    # Extract and execute each code cell in the notebook
    for cell in notebook_content.cells:
        if cell.cell_type == 'code':
            exec(cell.source, globals())

# Set Streamlit page configuration
st.set_page_config(page_title="Website Traffic Anomaly Detection", page_icon="🔍", layout="wide")

# Title and description
st.title("Website Traffic Anomaly Detection")
st.markdown("""
This application analyzes website traffic data to detect potential anomalies and security threats.
Upload your traffic data CSV file to get started.
""")

# File uploader for CSV files
st.header("Upload Traffic Data")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Save uploaded file temporarily
        temp_file_path = "temp_upload.csv"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load the notebook functions
        load_ipynb_module('anamoly_backend.ipynb')

        # Process data using the loaded functions
        with st.spinner("Processing data... This may take a moment."):
            df = process_traffic_data(temp_file_path)
            traffic_per_minute, traffic_per_hour, traffic_per_day = generate_traffic_analysis(df)

            traffic_per_minute = detect_traffic_anomalies(traffic_per_minute, "Minute_Request_Count")
            traffic_per_hour = detect_traffic_anomalies(traffic_per_hour, "Hourly_Request_Count")
            traffic_per_day = detect_traffic_anomalies(traffic_per_day, "Daily_Request_Count")

            # Create output folders
            output_dir = "output"
            plots_dir = os.path.join(output_dir, "plots")
            reports_dir = os.path.join(output_dir, "reports")
            os.makedirs(plots_dir, exist_ok=True)
            os.makedirs(reports_dir, exist_ok=True)

            generate_traffic_plots(traffic_per_minute, traffic_per_hour, traffic_per_day, plots_dir)
            generate_anomaly_plots(traffic_per_minute, traffic_per_hour, traffic_per_day, plots_dir)

            df, features_used = detect_packet_anomalies(df)
            df = categorize_anomalies(df)
            anomaly_summary, outliers = generate_anomaly_report(df, reports_dir)

        st.success("Analysis complete!")

        # Display tabs for results
        tab1, tab2, tab3, tab4 = st.tabs(["Data Overview", "Traffic Analysis", "Anomaly Detection", "Download Reports"])

        with tab1:
            st.header("Data Overview")
            st.subheader("Processed Data Sample")
            st.dataframe(df.head(10))

            st.subheader("Dataset Statistics")
            st.write(f"Total records: {len(df)}")
            st.write(f"Features analyzed: {df.columns.tolist()}")

        with tab2:
            st.header("Traffic Analysis")

            st.subheader("Traffic Per Minute")
            st.image(f"{plots_dir}/minute_traffic.png")

            st.subheader("Traffic Per Hour")
            st.image(f"{plots_dir}/hour_traffic.png")

            st.subheader("Traffic Per Day")
            st.image(f"{plots_dir}/day_traffic.png")

        with tab3:
            st.header("Anomaly Detection Results")

            st.subheader("Anomaly Summary")
            st.write(f"Total anomalies detected: {anomaly_summary['anomalies_detected']} ({anomaly_summary['anomaly_percentage']:.2f}% of total traffic)")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Anomaly Categories**")
                st.write(pd.Series(anomaly_summary["anomaly_categories"]))

            with col2:
                st.write("**Protocol Categories**")
                st.write(pd.Series(anomaly_summary["protocol_categories"]))

            with col3:
                st.write("**Source Categories**")
                st.write(pd.Series(anomaly_summary["source_categories"]))

            st.subheader("Minute-Level Anomalies")
            st.image(f"{plots_dir}/minute_anomalies.png")

            st.subheader("Hour-Level Anomalies")
            st.image(f"{plots_dir}/hour_anomalies.png")

            st.subheader("Anomaly Details")
            st.dataframe(outliers.head(20))

        with tab4:
            st.header("Download Reports")
            st.download_button(
                label="Download Full Report",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="final_anomalies_report.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Download Outliers Only",
                data=outliers.to_csv(index=False).encode('utf-8'),
                file_name="outliers_detected.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred during processing: {str(e)}")
        st.write("Please make sure your CSV file has the required columns: Time, Length, Source, Destination, Protocol")

    finally:
        # Clean up temporary file
        if os.path.exists("temp_upload.csv"):
            os.remove("temp_upload.csv")

else:
    # Show sample data format when no file is uploaded
    st.info("Please upload a CSV file with the following columns: Time, Length, Source, Destination, Protocol")

    # Display sample data format
    sample_data = {
        "Time": [0, 1, 2, 3, 4],
        "Length": [128, 256, 512, 128, 1024],
        "Source": ["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"],
        "Destination": ["10.0.0.1", "10.0.0.2", "10.0.0.1", "10.0.0.3", "10.0.0.2"],
        "Protocol": [6, 17, 6, 1, 6]
    }
    st.dataframe(pd.DataFrame(sample_data))

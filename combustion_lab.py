import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# UCD Logo
st.markdown("""
    <div style="text-align: center;">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/6/6e/University_College_Dublin_logo.svg/1200px-University_College_Dublin_logo.svg.png" 
             alt="UCD Crest" width="80">
    </div>
""", unsafe_allow_html=True)

# Title
st.markdown("")
st.markdown("<h5 style='text-align: center;'>UCD College of Engineering & Architecture</h2>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>Combustion Lab Analyzer</h2>", unsafe_allow_html=True)

# (Styling) 
st.markdown("""
    <style>
        body, .stApp {
            background: linear-gradient(140deg, #d9d7c3);
            background-size: 200% 200%;
            animation: fireflow 8s ease infinite;
        }

         .block-container {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(0,0,0,0.15);
        }

        /* Optional: headings and labels */
        h1, h2, h3, h4, h5, h6, .stMarkdown, .css-1d391kg, .stText, .stSelectbox, label {
            color: #6a5d4d;
        }
        
    </style>
""", unsafe_allow_html=True)

# == User Inputs ==
st.markdown("### Inputs 📋")
st.markdown(
    "<span style='color: #31333F; font-size: 0.9rem;'>Please enter fuel information below:</span>",
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    fuel_mass = st.number_input("Fuel mass (kg)", min_value=0.0, format="%.3f")
with col2:
    firelighter_mass = st.number_input("Firelighter mass (kg)", min_value=0.0, format="%.3f")
with col3:
    kindling_mass = st.number_input("Kindling mass (kg)", min_value=0.0, format="%.3f")
with col4:
    pm_mass = st.number_input("Measured PM mass (g)", min_value=0.0, format="%.4f")

col5, col6, col7 = st.columns(3)
with col5:
    fuel_type = st.selectbox("Choose fuel type", ["wood", "briquettes", "bituminous", "smokeless", "sod", "firelighters", "other"])
    if fuel_type == "other":
        custom_fuel_name = st.text_input("Enter fuel name")
        custom_lhv = st.number_input("Enter LHV for the new fuel (MJ/kg)", min_value=0.0, format="%.3f")
with col6:
    appliance = st.selectbox("Choose appliance", ["open fireplace", "closed stove"])
with col7:
    date = st.date_input("Date", value=datetime.date.today())

# == Upload Raw Data ==
st.markdown("##### Upload Raw Data 📂")
raw_file = st.file_uploader("Please upload raw data file", type=["xlsx", "xls", "csv", "txt"])

# (Calculations)

# Calculations Button
if st.button("Calculate & Save Results"):
    try:
        # Fuel LHV Properties Table 
        LHV = {
            "briquettes": 21.716,
            "wood": 18.401,
            "bituminous": 33.176,
            "smokeless": 33.096,
            "sod": 20.918,
            "firelighters": 33.891
        }
        if fuel_type == "other":
            if not custom_fuel_name or custom_lhv == 0.0:
                st.error("Please enter both a fuel name and LHV value for custom fuel.")
                st.stop()
            lhv_fuel = custom_lhv
            fuel_type_label = custom_fuel_name.strip().lower().replace(" ", "_")
        else:
            lhv_fuel = LHV.get(fuel_type)
            fuel_type_label = fuel_type.lower()

        lhv_firelighter = LHV["firelighters"]
        total_energy = (lhv_fuel * fuel_mass) + (lhv_firelighter * firelighter_mass)

        if total_energy == 0:
            st.warning("Total energy is zero — PM EF can't be computed.")
        else:
            pm_ef = pm_mass / total_energy

            # Processing Raw Data
            if raw_file is None:
                st.error("Please upload a raw data file.")
                st.stop()

            if raw_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(raw_file)
            else:
                df = pd.read_csv(raw_file, sep=None, engine='python')

            # Adding User Inputs and Computed Results to New File
            df["Fuel mass"] = fuel_mass
            df["Firelighter mass"] = firelighter_mass
            df["Kindling mass"] = kindling_mass
            df["PM mass"] = pm_mass
            df["Total Energy (MJ)"] = round(total_energy, 3)
            df["PM EF (g/MJ)"] = round(pm_ef, 6)
            
            # Renaming Columns Before Saving 
            column_renames = {
                "X_Value": "Elapsed Time (s)",
                "1-Load Cell (Formula Result)": "Load Cell (kg)",
                "2-T_MFM (Formula Result)": "T_MFM",
                "3-T_bottom (Arith. Mean)": "T_Botton (°C)",
                "4-T_middle (Arith. Mean)": "T_Flue (°C)",
                "5-T_top (Arith. Mean)": "T_Top (°C)",
                "6-T_ambient (Arith. Mean)": "T_Ambient (°C)",
                "7-T_filter (Arith. Mean)": "T_Filter (°C)",
                "8-Flue Pressure (Formula Result)": "Flue_Pressure (Pa)",
                "11-Mass flowmeter_flue gas (Formula Result)": "Mass Flowmeter_Flue Gas (g/min)",
                "11-Mass flowmeter_flue gas (Formula Result) 1": "Suggested Mass FLow (g/min)",
                "12-MFC_mass flow (Formula Result)": "MFC_Mass Flow (g/min)",
                "Comment": "Time"
            }
            df.rename(columns=column_renames, inplace=True)
            try:
                df["Elapsed Time (s)"] = pd.to_numeric(df["Elapsed Time (s)"], errors="coerce")
                df["Load Cell (kg)"] = pd.to_numeric(df["Load Cell (kg)"], errors="coerce")
                df["mdot fuel (kg/s)"] = df["Load Cell (kg)"].diff() / df["Elapsed Time (s)"].diff()
                if "mdot fuel (kg/s)" in df.columns:
                    df["mdot fuel (kg/s)"] = pd.to_numeric(df["mdot fuel (kg/s)"], errors="coerce")
                    avg_mdot = df["mdot fuel (kg/s)"].mean()
                    df["Average mdot fuel (kg/s)"] = avg_mdot

            except Exception as mdot_error:
                st.warning(f"⚠️ Couldn't calculate mdot fuel: {mdot_error}")


            # Adding Run Number to File Name
            os.makedirs("data", exist_ok=True)
            date_str = date.strftime("%d%m%Y")
            base_name = f"{date_str}-{fuel_type_label.lower()}-{appliance.replace(' ', '_').lower()}"
            existing_runs = [
                f for f in os.listdir("data")
                if f.startswith(base_name) and f.endswith(".csv")
            ]
            run_number = len(existing_runs) + 1
            filename = f"{base_name}-run{run_number}.csv"
            save_path = os.path.join("data", filename)

            # Saving
            df.to_csv(save_path, index=False)

            # Showing Results
            st.success(f"✅ Data calculated and saved as {filename}")
            st.write(f"**Total Energy Loaded:** {total_energy:.3f} MJ")
            st.write(f"**PM Emission Factor:** {pm_ef:.6f} g/MJ")
            st.dataframe(df.head())

    except Exception as e:
        st.error(f"Error during calculation: {e}")


# == Visualisation Section ==
st.divider()
st.markdown("### Data Visualisation 📈")

import scipy.stats as stats
import plotly.express as px

viz_type = st.selectbox(
    "Choose visualization type",
    ["Line Plot", "Bar chart", "Error bar chart (95% CI)"]
)

uploaded_files = st.file_uploader(
    "Upload one or more CSV result files", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    if viz_type == "Error bar chart (95% CI)":
        st.markdown("#### Select a metric (must be one consistent value per file)")

        allowed_metrics = ["PM EF (g/MJ)", "Total Energy (MJ)", "Average mdot fuel (kg/s)"]
        selected_metric = st.selectbox("Metric", allowed_metrics)

        metric_data = []

        for file in uploaded_files:
            try:
                df = pd.read_csv(file)
                df.columns = df.columns.str.strip()

                if selected_metric not in df.columns:
                    st.warning(f"{file.name}: '{selected_metric}' not found — skipped.")
                    continue

                # Extract Values
                values = pd.to_numeric(df[selected_metric], errors="coerce").dropna().unique()
                if len(values) != 1:
                    st.warning(f"{file.name}: Must have exactly one unique value in '{selected_metric}' — skipped.")
                    continue

                fuel = file.name.split("-")[1].replace("_", " ").title()
                metric_data.append({"Fuel Type": fuel, selected_metric: values[0]})

            except Exception as e:
                st.warning(f"{file.name}: Error processing file: {e}")

        if len(metric_data) >= 2:
            df_summary = pd.DataFrame(metric_data)
            stats_df = df_summary.groupby("Fuel Type")[selected_metric].agg(["mean", "std", "count"]).reset_index()
            stats_df["sem"] = stats_df["std"] / stats_df["count"]**0.5
            stats_df["ci95"] = stats_df["sem"] * stats.t.ppf(0.975, df=stats_df["count"] - 1)

            fig = px.bar(
                stats_df,
                x="Fuel Type",
                y="mean",
                error_y="ci95",
                title=f"{selected_metric} by Fuel Type (95% CI)",
                labels={"mean": f"{selected_metric} (mean)"}
            )

            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(stats_df)
        else:
            st.info("At least two valid files with consistent values are required.")


    else:
        cleaned_dfs = []
        for file in uploaded_files:
            try:
                if file.size == 0:
                    st.warning(f"{file.name}: File is empty — skipped.")
                    continue
                df = pd.read_csv(file)
                df["Source File"] = file.name
                df = df.apply(pd.to_numeric, errors="ignore")
                cleaned_dfs.append(df)
            except Exception as e:
                st.error(f"Error loading {file.name}: {e}")

        if cleaned_dfs:
            combined_df = pd.concat(cleaned_dfs, ignore_index=True)

            # Add Derived Fields
            if "fuel_type" not in combined_df.columns:
                combined_df["fuel_type"] = combined_df["Source File"].str.extract(r"\d{8}-(.*?)-")[0].str.replace("_", " ").str.title()
            if "appliance" not in combined_df.columns:
                combined_df["appliance"] = combined_df["Source File"].str.extract(r"\d{8}-.*?-(.*?)-")[0].str.replace("_", " ").str.title()

            if "Elapsed Time (s)" in combined_df.columns and "Load Cell (kg)" in combined_df.columns:
                try:
                    combined_df["Elapsed Time (s)"] = pd.to_numeric(combined_df["Elapsed Time (s)"], errors="coerce")
                    combined_df["Load Cell (kg)"] = pd.to_numeric(combined_df["Load Cell (kg)"], errors="coerce")
                    combined_df["mdot fuel (kg/s)"] = combined_df["Load Cell (kg)"].diff() / combined_df["Elapsed Time (s)"].diff()
                except Exception as e:
                    st.warning(f"Couldn't compute mdot fuel: {e}")

            all_columns = combined_df.columns.tolist()
            x_axis_options = sorted(set(all_columns + ["fuel_type", "appliance"]))
            x_var = st.selectbox("X-axis variable", x_axis_options, key="x_axis")
            y_var = st.selectbox("Y-axis variable", all_columns, key="y_axis")
            group_by_file = st.checkbox("Group data by file for comparison", value=True)

            st.markdown("#### Resulting Plot")

            combined_df[y_var] = pd.to_numeric(combined_df[y_var], errors="coerce")
            plot_df = combined_df.dropna(subset=[x_var, y_var])

            if x_var.lower() == "time":
                plot_df[x_var] = pd.to_datetime(plot_df[x_var], errors="coerce")

            color = "Source File" if group_by_file else None

            if viz_type == "Line Plot":
                fig = px.line(
                    plot_df,
                    x=x_var,
                    y=y_var,
                    color=color,
                    title=f"Line Plot: {y_var} vs {x_var}",
                    labels={x_var: x_var, y_var: y_var}
                )

            elif viz_type == "Bar chart":
                fig = px.bar(
                    plot_df,
                    x=x_var,
                    y=y_var,
                    color=color,
                    title=f"Bar Chart: {y_var} vs {x_var}",
                    labels={x_var: x_var, y_var: y_var}
                )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No valid data loaded from files.")
else:
    st.info("Please upload one or more CSV files to visualize.")

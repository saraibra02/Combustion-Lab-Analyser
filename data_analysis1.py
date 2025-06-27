import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import io

# Title
st.title("Combustion Lab Analyser🔥")

# === 1. User Inputs ===
st.header("📝 Inputs")
st.write("Please enter fuel information below:")
col1, col2, col3, col4 = st.columns(4)
with col1:
    fuel_mass = st.number_input("Fuel mass (kg)", min_value=0.0, format="%.3f")
with col2:
    firelighter_mass = st.number_input("Firelighter mass (kg)", min_value=0.0, format="%.3f")
with col3:
    kindling_mass = st.number_input("Kindling mass (kg)", min_value=0.0, format="%.3f")
with col4:
    pm_mass = st.number_input("Measured PM mass (g)", min_value=0.0, format="%.4f")

col5, col6 = st.columns(2)
with col5:
    fuel_type = st.selectbox("Choose fuel type", ["wood", "briquettes", "bituminous", "smokeless", "sod", "firelighters"])
with col6:
    appliance = st.selectbox("Choose appliance", ["open fireplace", "closed stove"])

date = st.date_input("Date of Experiment", value=datetime.date.today())

# === 2. LHV Table ===
LHV = {
    "briquettes": 21.716,
    "wood": 18.401,
    "bituminous": 33.176,
    "smokeless": 33.096,
    "sod": 20.918,
    "firelighters": 33.891
}

# === 3. Calculations ===
st.header("🧮 Calculations")

calc_option = st.radio(
    "What would you like to calculate?",
    ["PM Emission Factor", "Upload & Analyze Fuel Temperature Data"]
)

# === A. PM EMISSION FACTOR CALC ===
if calc_option == "PM Emission Factor":
    st.subheader("PM Emission Factor Calculation")

    st.markdown("##### 📁 Save Results")
    excel_filename = st.text_input("Enter Excel file name (no extension)", value="pm_ef_log")
    excel_path = os.path.join("data", f"{excel_filename}.xlsx")
    st.markdown("*Note: if you wish to compare PM EF values of different runs, record data on the same file and only change input variable of interest.*")

    # Choose error input mode
    error_mode = st.radio("How would you like to enter PM EF error?", ["g/MJ", "% of calculated PM EF"])

    # Placeholder for error input
    pm_error_input = 0.0
    if error_mode == "g/MJ":
        pm_error_input = st.number_input("Enter PM EF error (g/MJ)", min_value=0.0, format="%.4f", value=0.0)
    elif error_mode == "% of calculated PM EF":
        pm_error_input = st.number_input("Enter PM EF error (%)", min_value=0.0, max_value=100.0, format="%.2f", value=5.0)

    if st.button("Calculate PM EF"):
        try:
            lhv_fuel = LHV.get(fuel_type)
            lhv_firelighter = LHV["firelighters"]
            total_energy = (lhv_fuel * fuel_mass) + (lhv_firelighter * firelighter_mass)

            if total_energy == 0:
                st.warning("Total energy is zero — PM EF can't be computed.")
            else:
                pm_ef = pm_mass / total_energy

                # Convert % error to g/MJ if needed
                if error_mode == "g/MJ":
                    pm_ef_error = pm_error_input
                else:
                    pm_ef_error = (pm_error_input / 100) * pm_ef

                new_row = pd.DataFrame([{
                    "Date": date.strftime("%Y-%m-%d"),
                    "Fuel type": fuel_type,
                    "Appliance": appliance,
                    "Fuel mass (kg)": fuel_mass,
                    "Firelighter mass (kg)": firelighter_mass,
                    "PM mass (g)": pm_mass,
                    "Total Energy (MJ)": round(total_energy, 3),
                    "PM EF (g/MJ)": round(pm_ef, 6),
                    "PM EF error (g/MJ)": round(pm_ef_error, 6)
                }])

                os.makedirs("data", exist_ok=True)

                if os.path.exists(excel_path):
                    existing_df = pd.read_excel(excel_path)
                    updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                else:
                    updated_df = new_row

                updated_df.to_excel(excel_path, index=False)

                st.success(f"✅ PM Emission Factor = {pm_ef:.6f} g/MJ")
                st.success(f"✅ Total Energy Loaded = {total_energy:.3f} MJ")
                st.write(f"Data saved to `{excel_filename}.xlsx`")
                st.dataframe(updated_df.tail())

                # After saving updated_df to Excel
                excel_bytes = io.BytesIO()
                updated_df.to_excel(excel_bytes, index=False, engine='openpyxl')
                excel_bytes.seek(0)

                st.download_button(
                    label="⬇️ Download PM EF Excel File",
                    data=excel_bytes,
                    file_name=f"{excel_filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"Error calculating PM EF: {e}")

    # === Visualization Section ===
    if os.path.exists(excel_path):
        st.markdown("### 📊 Visualize Your PM EF Data")
        vis_df = pd.read_excel(excel_path)

        chart_type = st.selectbox("Choose a visualization type", ["Table", "Bar Chart", "Scatter Plot", "Bar Chart with Error Bars"])
        x_var = st.selectbox("X-axis", vis_df.columns)
        y_var = st.selectbox("Y-axis", [col for col in vis_df.columns if col != x_var])

        if chart_type == "Table":
            st.dataframe(vis_df[[x_var, y_var]])
        elif chart_type == "Bar Chart":
            fig = px.bar(vis_df, x=x_var, y=y_var, title=f"{y_var} by {x_var}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Scatter Plot":
            fig = px.scatter(vis_df, x=x_var, y=y_var, title=f"{y_var} vs {x_var}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Bar Chart with Error Bars":
            if "PM EF error (g/MJ)" in vis_df.columns:
                color_by = st.checkbox("Color bars by appliance", value=False)

                fig = px.bar(
                    vis_df,
                    x=x_var,
                    y=y_var,
                    color="Appliance" if color_by else None,
                    error_y=vis_df["PM EF error (g/MJ)"],
                    text=y_var,  # value labels on top
                    title=f"{y_var} by {x_var} (with error bars)"
                )

                fig.update_traces(texttemplate='%{text:.4f}', textposition='outside')
                fig.update_layout(
                    yaxis_title=y_var,
                    xaxis_title=x_var,
                    yaxis_tickformat=".6f",  # control y-axis formatting
                    template="plotly_white"
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No PM EF error column found. Please recalculate PM EF with error input.")
    else:
        st.info("No saved file found to visualize.")


# === B. TEMPERATURE DATA ANALYSIS ===
elif calc_option == "Upload & Analyze Fuel Temperature Data":
    st.subheader("📂 Upload & Analyze Fuel Temperature Data")
    st.markdown("Upload one or more files containing `time` and `T_fuel` columns. Accepted formats: CSV, Excel.")

    uploaded_files = st.file_uploader(
        "Upload CSV or Excel file(s)",
        type=["csv", "xlsx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        import plotly.graph_objects as go
        fig = go.Figure()

        for file in uploaded_files:
            try:
                df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
                df.columns = df.columns.str.strip().str.lower()

                if "time" in df.columns and "t_fuel" in df.columns:
                    df["time"] = pd.to_datetime(df["time"], format="%H:%M:%S", errors="coerce")
                    df = df.dropna(subset=["time", "t_fuel"]).sort_values("time")

                    fig.add_trace(go.Scatter(
                        x=df["time"],
                        y=df["t_fuel"],
                        mode="lines",
                        name=file.name
                    ))
                else:
                    st.warning(f"Skipping '{file.name}' — missing 'time' and/or 'T_fuel' columns.")
            except Exception as e:
                st.error(f"Error reading '{file.name}': {e}")

        fig.update_layout(
            title="T_fuel vs Time",
            xaxis_title="Time",
            yaxis_title="T_fuel (°C)",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True) 

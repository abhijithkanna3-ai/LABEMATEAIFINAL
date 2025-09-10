import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 📌 Input Readings ---
# Instructions: Replace the values in this list with your own experimental data.
# Each dictionary represents one trial.
trials = [
    {"P.G.": 0.2, "V.G.": -20, "t": 29.81, "t_n": 19.34},
    {"P.G.": 0.4, "V.G.": -30, "t": 26.00, "t_n": 18.50},
    {"P.G.": 0.6, "V.G.": -40, "t": 23.94, "t_n": 17.06},
    {"P.G.": 0.8, "V.G.": -50, "t": 21.06, "t_n": 16.50},
    {"P.G.": 1.0, "V.G.": -60, "t": 19.16, "t_n": 15.65},
    # Add more trials here, e.g., {"P.G.": value, "V.G.": value, "t": value, "t_n": value},
]

# --- 📌 Constants ---
n_revolutions = 10
Ec_rev_kwh = 750
eta_T = 0.75
rho_kg_m3 = 1000
g_ms2 = 9.81
A_m2 = 0.49
h_m = 0.1
X_m = 0.31

# --- Processing Trials ---
results_data = []

# Check if any trials have been entered
if not trials:
    print("Error: The 'trials' list is empty. Please add your experimental data to the script.")
else:
    for i, trial in enumerate(trials):
        pg_kg_cm2 = trial["P.G."]
        vg_mm_hg = trial["V.G."]
        t_s = trial["t"]
        t_n_s = trial["t_n"]

        # --- Formula Calculations ---
        # Pressure Head, H in meters of H₂O
        pressure_head_pg = pg_kg_cm2 * 10.33
        pressure_head_vg = (vg_mm_hg * 10.33) / 760
        H_m = pressure_head_pg + pressure_head_vg + X_m

        # Flow rate, Q in m³/s
        Q_m3_s = (A_m2 * h_m) / t_s

        # Input Power, I/P in kW
        IP_kw = (n_revolutions * 3600 * eta_T) / (t_n_s * Ec_rev_kwh)

        # Output Power, O/P in kW
        OP_kw = (rho_kg_m3 * g_ms2 * Q_m3_s * H_m) / 1000

        # Efficiency, η in %
        # Avoid division by zero if Input Power is 0
        eta_percent = (OP_kw / IP_kw) * 100 if IP_kw > 0 else 0

        results_data.append({
            "Trial": i + 1,
            "P.G. (Kg/cm²)": pg_kg_cm2,
            "V.G. (mm Hg)": vg_mm_hg,
            "H (m)": H_m,
            "Q (m³/s)": Q_m3_s,
            "I/P (kW)": IP_kw,
            "O/P (kW)": OP_kw,
            "η (%)": eta_percent,
        })

    # --- Display Results Table ---
    df = pd.DataFrame(results_data)
    print("--- Centrifugal Pump Test Results ---")
    # Format the dataframe for better readability
    pd.options.display.float_format = '{:.4f}'.format
    print(df.to_string(index=False))
    print("-" * 35)

    # --- Step-by-Step Model Calculation for the First Trial ---
    print("\n--- Model Calculation for Trial 1 ---")
    first_trial_data = results_data[0]
    print("1. Calculate Pressure Head (H):")
    print(f"   H = [P.G. × 10.33] + [(V.G. × 10.33) / 760] + X")
    print(f"   H = [{first_trial_data['P.G. (Kg/cm²)']} × 10.33] + [({first_trial_data['V.G. (mm Hg)']}) × 10.33 / 760] + {X_m}")
    print(f"   H = {first_trial_data['H (m)']:.4f} m of H₂O")

    print("\n2. Calculate Flow Rate (Q):")
    print(f"   Q = (A × h) / t")
    print(f"   Q = ({A_m2} m² × {h_m} m) / {trials[0]['t']} s = {first_trial_data['Q (m³/s)']:.6f} m³/s")

    print("\n3. Calculate Input Power (I/P):")
    print(f"   I/P = [n × 3600 × η_T] / [t_n × E_c]")
    print(f"   I/P = [{n_revolutions} × 3600 × {eta_T}] / [{trials[0]['t_n']} s × {Ec_rev_kwh}] = {first_trial_data['I/P (kW)']:.4f} kW")

    print("\n4. Calculate Output Power (O/P):")
    print(f"   O/P = [ρ × g × Q × H] / 1000")
    print(f"   O/P = [{rho_kg_m3} × {g_ms2} × {first_trial_data['Q (m³/s)']:.6f} × {first_trial_data['H (m)']:.4f}] / 1000 = {first_trial_data['O/P (kW)']:.4f} kW")

    print("\n5. Calculate Efficiency (η):")
    print(f"   η = [O/P / I/P] × 100")
    print(f"   η = [{first_trial_data['O/P (kW)']:.4f} / {first_trial_data['I/P (kW)']:.4f}] × 100 = {first_trial_data['η (%)']:.2f}%")
    print("-" * 35)


    # --- Plotting Characteristic Curves ---
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Set common x-axis
    x_axis_Q = df["Q (m³/s)"]

    # Primary Y-axis (for Head and O/P)
    ax1.set_xlabel('Flow rate, Q (m³/s)', fontsize=12)
    ax1.set_ylabel('Total Head, H (m)  |  Output Power, O/P (kW)', color='tab:blue', fontsize=12)
    p1, = ax1.plot(x_axis_Q, df["H (m)"], 'o-', label='H vs. Q (Head)', color='tab:blue')
    p2, = ax1.plot(x_axis_Q, df["O/P (kW)"], 's--', label='O/P vs. Q (Output Power)', color='tab:cyan')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Secondary Y-axis (for Efficiency)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Efficiency, η (%)', color='tab:red', fontsize=12)
    p3, = ax2.plot(x_axis_Q, df["η (%)"], '^-', label='η vs. Q (Efficiency)', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Title and Legend
    plt.title('Characteristic Curves of Centrifugal Pump', fontsize=16)
    lines = [p1, p2, p3]
    ax1.legend(lines, [l.get_label() for l in lines], loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3)
    
    # Adjust layout to prevent labels from overlapping
    fig.tight_layout(rect=[0, 0.05, 1, 1])

    # Save and show the plot
    plt.savefig("pump_characteristic_curves.png")
    print("\nGraph has been saved as 'pump_characteristic_curves.png'")
    plt.show()

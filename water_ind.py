import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class WTPAnalysis:
    """
    A class to perform analysis on Water Treatment Plant (WTP) design and performance.
    It takes raw experimental data, calculates key metrics, generates reports, and plots graphs.
    """
    
    # --- Constants ---
    G = 9.81  # Acceleration due to gravity (m/s^2)
    RHO = 1000  # Density of water (kg/m^3)
    M3_DAY_TO_L_S = 0.011574  # Conversion factor for m³/day to L/s

    # --- Recommended Design Ranges for Potable Water Treatment ---
    RECOMMENDED_RANGES = {
        'DT_sed': (2, 4),   # Detention Time for sedimentation (hours)
        'SLR': (20, 40),    # Surface Loading Rate (m³/m²·day)
        'FLR': (120, 240)   # Filter Loading Rate for rapid sand filters (m³/m²·day)
    }

    def __init__(self, data):
        """
        Initializes the WTPAnalysis class with the user-provided data.
        
        Args:
            data (list): A list of dictionaries, where each dictionary represents one trial's readings.
        """
        self.data = data
        self.results = []
        self.df = None
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 120)

    def _convert_flow_units(self, trial_data):
        """Ensures flow rate is consistently available in both m³/day and L/s."""
        if 'Q_m3_day' in trial_data and 'Q_L_s' not in trial_data:
            trial_data['Q_L_s'] = round(trial_data['Q_m3_day'] * self.M3_DAY_TO_L_S, 2)
        elif 'Q_L_s' in trial_data and 'Q_m3_day' not in trial_data:
            trial_data['Q_m3_day'] = round(trial_data['Q_L_s'] / self.M3_DAY_TO_L_S, 2)
        return trial_data

    def _calculate_all_metrics(self, trial_data):
        """Calculates all performance metrics for a single trial based on provided formulae."""
        # 1. Coagulation/Turbidity Removal Efficiency
        initial_turb = trial_data.get('initial_turbidity_NTU', 0)
        final_turb = trial_data.get('final_turbidity_NTU', 0)
        coag_eff = ((initial_turb - final_turb) / initial_turb) * 100 if initial_turb > 0 else 0

        # 2. & 3. Sedimentation Tank Metrics (DT and SLR)
        sed_tank_l = trial_data.get('sed_tank_L_m', 0)
        sed_tank_b = trial_data.get('sed_tank_B_m', 0)
        sed_tank_d = trial_data.get('sed_tank_D_m', 0)
        sed_vol = sed_tank_l * sed_tank_b * sed_tank_d
        sed_area = sed_tank_l * sed_tank_b
        q_m3_day = trial_data.get('Q_m3_day', 0)

        dt_sed = (sed_vol / q_m3_day) * 24 if q_m3_day > 0 else 0 # in hours
        slr = q_m3_day / sed_area if sed_area > 0 else 0

        # 4. Filter Metrics (FLR)
        filter_area = trial_data.get('filter_area_m2', 0)
        flr = q_m3_day / filter_area if filter_area > 0 else 0

        # 5. Disinfection Metrics (Chlorine Demand)
        chlorine_dose = trial_data.get('chlorine_dose_mg_L', 0)
        chlorine_residual = trial_data.get('chlorine_residual_mg_L', 0)
        chlorine_demand = chlorine_dose - chlorine_residual

        # 6. Energy Cost Calculation
        if 'energy_kWh_day' in trial_data and trial_data['energy_kWh_day'] is not None:
            energy_cost = trial_data['energy_kWh_day']
        elif 'pump_head_m' in trial_data and trial_data.get('pump_head_m') is not None:
            q_m3_s = q_m3_day / (24 * 3600)
            power_watts = trial_data['pump_head_m'] * q_m3_s * self.RHO * self.G
            power_kw = power_watts / 1000
            energy_cost = power_kw * 24
        else:
            energy_cost = 0

        return {
            "Turbidity Removal Eff. (%)": round(coag_eff, 2),
            "DT (hr)": round(dt_sed, 2),
            "SLR (m³/m²·day)": round(slr, 2),
            "FLR (m³/m²·day)": round(flr, 2),
            "Chlorine Demand (mg/L)": round(chlorine_demand, 2),
            "Energy Cost (kWh/day)": round(energy_cost, 2),
        }

    def run_analysis(self):
        """Processes all trials, performs calculations, and stores results in a DataFrame."""
        for i, trial in enumerate(self.data):
            trial = self._convert_flow_units(trial)
            calcs = self._calculate_all_metrics(trial)
            
            result_row = {
                "Trial": i + 1,
                "Flow (m³/day)": trial['Q_m3_day'],
                "Flow (L/s)": trial['Q_L_s'],
                **calcs,
                "Residual Chlorine (mg/L)": trial['chlorine_residual_mg_L'],
                "Coagulant Dose (mg/L)": trial.get('coagulant_dose_mg_L', 0) # Needed for plots
            }
            self.results.append(result_row)
        
        self.df = pd.DataFrame(self.results)
        
        # Create a DataFrame specifically for display to match requested format
        self.df_display = self.df[[
            "Trial", "Flow (m³/day)", "Flow (L/s)", "DT (hr)", "SLR (m³/m²·day)",
            "FLR (m³/m²·day)", "Turbidity Removal Eff. (%)", "Chlorine Demand (mg/L)",
            "Residual Chlorine (mg/L)", "Energy Cost (kWh/day)"
        ]]

    def generate_model_calculation(self):
        """Generates a detailed, step-by-step calculation for the first trial."""
        if not self.results:
            return "No data to process. Please run analysis first."

        trial1_data = self._convert_flow_units(self.data[0])
        trial1_results = self.results[0]
        
        q = trial1_data['Q_m3_day']
        it, ft = trial1_data['initial_turbidity_NTU'], trial1_data['final_turbidity_NTU']
        sl, sb, sd = trial1_data['sed_tank_L_m'], trial1_data['sed_tank_B_m'], trial1_data['sed_tank_D_m']
        sv, sa = sl * sb * sd, sl * sb
        fa = trial1_data['filter_area_m2']
        cd, cr = trial1_data['chlorine_dose_mg_L'], trial1_data['chlorine_residual_mg_L']

        output = "--- Model Calculation for Trial 1 ---\n\n"
        output += f"1. Turbidity Removal Efficiency (%):\n   Formula: ((Initial - Final Turbidity) / Initial) * 100\n   Substitution: (({it} - {ft}) / {it}) * 100\n   Result: {trial1_results['Turbidity Removal Eff. (%)']} %\n\n"
        output += f"2. Detention Time (DT) for Sedimentation Tank (hr):\n   Formula: (Volume / Flow) * 24\n   Volume = {sl}m × {sb}m × {sd}m = {sv} m³\n   Substitution: ({sv} m³ / {q} m³/day) * 24 hr/day\n   Result: {trial1_results['DT (hr)']} hours\n\n"
        output += f"3. Surface Loading Rate (SLR) (m³/m²·day):\n   Formula: Flow Rate / Surface Area\n   Surface Area = {sl}m × {sb}m = {sa} m²\n   Substitution: {q} m³/day / {sa} m²\n   Result: {trial1_results['SLR (m³/m²·day)']} m³/m²·day\n\n"
        output += f"4. Filter Loading Rate (FLR) (m³/m²·day):\n   Formula: Flow Rate / Filter Area\n   Substitution: {q} m³/day / {fa} m²\n   Result: {trial1_results['FLR (m³/m²·day)']} m³/m²·day\n\n"
        output += f"5. Chlorine Demand (mg/L):\n   Formula: Dose - Residual\n   Substitution: {cd} mg/L - {cr} mg/L\n   Result: {trial1_results['Chlorine Demand (mg/L)']} mg/L\n\n"
        output += f"6. Energy Cost (kWh/day):\n"
        if trial1_data.get('energy_kWh_day') is not None:
            output += f"   Value provided directly.\n   Result: {trial1_results['Energy Cost (kWh/day)']} kWh/day\n"
        elif trial1_data.get('pump_head_m') is not None:
            ph = trial1_data['pump_head_m']
            q_s = q / 86400
            p_w = ph * q_s * self.RHO * self.G
            e_kwh = (p_w / 1000) * 24
            output += f"   Formula: (Head × Q × ρ × g) -> W to kWh/day\n   Q = {q_s:.5f} m³/s\n   Power (W) = {ph}m × {q_s:.5f}m³/s × {self.RHO}kg/m³ × {self.G}m/s² = {p_w:.2f} W\n   Energy = ({p_w:.2f}W / 1000) * 24h\n   Result: {e_kwh:.2f} kWh/day\n"
        else:
            output += "   No pump head or direct energy data provided.\n   Result: 0 kWh/day\n"
        return output

    def plot_graphs(self):
        """Generates and saves the required X-Y plots with best-fit lines."""
        if self.df is None or len(self.df) < 2:
            print("Warning: Not enough data to plot graphs (at least 2 data points required).")
            return

        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Plot 1: Flow rate (Q) vs Detention Time (DT)
        fig, ax1 = plt.subplots(figsize=(10, 6))
        x1, y1 = self.df['Flow (m³/day)'], self.df['DT (hr)']
        ax1.plot(x1, y1, 'o', color='blue', markersize=8, label='Data Points')
        z1 = np.polyfit(x1, y1, 2); p1 = np.poly1d(z1)
        xp1 = np.linspace(x1.min(), x1.max(), 100)
        ax1.plot(xp1, p1(xp1), '--', color='red', label='Best-fit Curve')
        ax1.set_title('Flow Rate vs. Detention Time', fontsize=16)
        ax1.set_xlabel('Flow Rate (Q) [m³/day]', fontsize=12)
        ax1.set_ylabel('Detention Time (DT) [hours]', fontsize=12)
        ax1.legend()
        fig.tight_layout()
        plt.savefig('flow_vs_dt.png')
        plt.show()

        # Plot 2: Coagulant dose vs Turbidity removal efficiency
        fig, ax2 = plt.subplots(figsize=(10, 6))
        x2, y2 = self.df['Coagulant Dose (mg/L)'], self.df['Turbidity Removal Eff. (%)']
        ax2.plot(x2, y2, 'o', color='blue', markersize=8, label='Data Points')
        z2 = np.polyfit(x2, y2, 2); p2 = np.poly1d(z2)
        xp2 = np.linspace(x2.min(), x2.max(), 100)
        ax2.plot(xp2, p2(xp2), '--', color='green', label='Best-fit Curve')
        ax2.set_title('Coagulant Dose vs. Turbidity Removal Efficiency', fontsize=16)
        ax2.set_xlabel('Coagulant Dose [mg/L]', fontsize=12)
        ax2.set_ylabel('Turbidity Removal Efficiency [%]', fontsize=12)
        ax2.legend()
        fig.tight_layout()
        plt.savefig('dose_vs_efficiency.png')
        plt.show()

    def generate_summary_report(self):
        """Generates a final text report summarizing the findings."""
        if self.df is None:
            return "No data to process. Please run analysis first."

        report = "--- WTP Performance Analysis Report ---\n\n"
        report += "1. Summary of Mean Values:\n"
        report += self.df_display.drop('Trial', axis=1).mean().to_string() + "\n\n"

        report += "2. Design Parameter Compliance Check:\n"
        for _, row in self.df.iterrows():
            dt_min, dt_max = self.RECOMMENDED_RANGES['DT_sed']
            slr_min, slr_max = self.RECOMMENDED_RANGES['SLR']
            flr_min, flr_max = self.RECOMMENDED_RANGES['FLR']
            dt_ok = "OK" if dt_min <= row['DT (hr)'] <= dt_max else "OUT OF RANGE"
            slr_ok = "OK" if slr_min <= row['SLR (m³/m²·day)'] <= slr_max else "OUT OF RANGE"
            flr_ok = "OK" if flr_min <= row['FLR (m³/m²·day)'] <= flr_max else "OUT OF RANGE"
            report += f"  Trial {row['Trial']}:\n"
            report += f"    - DT: {row['DT (hr)']:.2f} hr ({dt_ok}, Recommended: {dt_min}-{dt_max} hr)\n"
            report += f"    - SLR: {row['SLR (m³/m²·day)']:.2f} m³/m²·d ({slr_ok}, Recommended: {slr_min}-{slr_max})\n"
            report += f"    - FLR: {row['FLR (m³/m²·day)']:.2f} m³/m²·d ({flr_ok}, Recommended: {flr_min}-{flr_max})\n\n"

        report += "3. Unit Efficiency and Final Water Quality:\n"
        max_eff_row = self.df.loc[self.df['Turbidity Removal Eff. (%)'].idxmax()]
        avg_final_turb = np.mean([d['final_turbidity_NTU'] for d in self.data])
        report += f"  - Maximum turbidity removal of {max_eff_row['Turbidity Removal Eff. (%)']}% was achieved in Trial {max_eff_row['Trial']} with a coagulant dose of {max_eff_row['Coagulant Dose (mg/L)']} mg/L.\n"
        report += f"  - The average final turbidity is {avg_final_turb:.2f} NTU. For potable water, a value < 1.0 NTU is preferred.\n"
        report += f"  - The average residual chlorine is {self.df['Residual Chlorine (mg/L)'].mean():.2f} mg/L. A residual of 0.2-0.5 mg/L is desired for effective disinfection in the distribution network.\n\n"
        
        report += "4. Conclusion:\n  The analysis highlights the plant's performance under various conditions. The compliance check identifies deviations from standard design criteria, suggesting areas for operational adjustment. The dose-efficiency curve can be used to optimize chemical usage for cost-effectiveness and performance.\n"
        
        return report

# --- Main Execution Block ---
if __name__ == "__main__":
    #
    # 📌 --- USER INPUT SECTION --- 📌
    # Modify the list below with your experimental readings.
    # Use 'None' if a value is not applicable (e.g., if energy is provided, pump_head can be None).
    #
    input_readings = [
        {
            "Q_m3_day": 4320,
            "initial_turbidity_NTU": 50, "final_turbidity_NTU": 5,
            "coagulant_dose_mg_L": 20,
            "sed_tank_L_m": 20, "sed_tank_B_m": 10, "sed_tank_D_m": 3,
            "filter_area_m2": 25,
            "chlorine_dose_mg_L": 3, "chlorine_residual_mg_L": 0.5,
            "pump_head_m": 15, "energy_kWh_day": None # Will be calculated
        },
        {
            "Q_m3_day": 5000,
            "initial_turbidity_NTU": 55, "final_turbidity_NTU": 4,
            "coagulant_dose_mg_L": 25,
            "sed_tank_L_m": 20, "sed_tank_B_m": 10, "sed_tank_D_m": 3,
            "filter_area_m2": 25,
            "chlorine_dose_mg_L": 3.2, "chlorine_residual_mg_L": 0.4,
            "pump_head_m": None, "energy_kWh_day": 95 # Provided directly
        },
        {
            "Q_m3_day": 3800,
            "initial_turbidity_NTU": 45, "final_turbidity_NTU": 6,
            "coagulant_dose_mg_L": 18,
            "sed_tank_L_m": 20, "sed_tank_B_m": 10, "sed_tank_D_m": 3,
            "filter_area_m2": 25,
            "chlorine_dose_mg_L": 2.8, "chlorine_residual_mg_L": 0.6,
            "pump_head_m": 14, "energy_kWh_day": None
        },
    ]

    # Create an analyzer instance and run the full analysis
    analyzer = WTPAnalysis(input_readings)
    
    # 1. Perform calculations and create the DataFrame
    analyzer.run_analysis()

    # 2. Display the main results table
    print("--- Calculated Performance Metrics ---")
    print(analyzer.df_display.to_string())
    print("\n" + "="*80 + "\n")

    # 3. Display the detailed model calculation for the first trial
    print(analyzer.generate_model_calculation())
    print("\n" + "="*80 + "\n")

    # 4. Generate and display the final summary report
    print(analyzer.generate_summary_report())
    print("\n" + "="*80 + "\n")
    
    # 5. Generate, save, and show plots
    print("Generating plots...")
    analyzer.plot_graphs()
    print("Analysis complete. Plots saved as 'flow_vs_dt.png' and 'dose_vs_efficiency.png'.")

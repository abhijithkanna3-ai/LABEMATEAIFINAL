import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

class OilGasAnalysis:
    """
    A class to perform analysis on Oil & Gas process plant performance.
    It takes raw experimental data, calculates key metrics, generates reports, and plots graphs.
    """
    
    # --- Constants ---
    G = 9.81  # Acceleration due to gravity (m/s^2)
    PI = 3.1415926535

    # --- Conversion Factors ---
    BBL_DAY_TO_M3_S = 0.158987 / (24 * 3600)
    MMSCFD_TO_M3_S = 1187 / 3600 
    PSI_TO_BAR = 0.0689476
    BAR_TO_PA = 100000
    CP_TO_PA_S = 0.001
    
    def __init__(self, data):
        """
        Initializes the OilGasAnalysis class with the user-provided data.
        
        Args:
            data (list): A list of dictionaries, where each dictionary represents one trial's readings.
        """
        self.data = data
        self.results = []
        self.df = None
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 150)

    def _convert_and_prepare_si_units(self, trial_data):
        """Converts all input readings into a consistent set of SI units for calculation."""
        si_data = trial_data.copy()
        
        # Convert flows to m³/s
        si_data['Q_oil_m3_s'] = si_data.get('Q_oil_bbl_day', 0) * self.BBL_DAY_TO_M3_S
        si_data['Q_gas_m3_s'] = si_data.get('Q_gas_MMSCFD', 0) * self.MMSCFD_TO_M3_S
        
        # Convert pressures to Pa for calculations
        si_data['P_in_Pa'] = si_data.get('P_in_bar', 0) * self.BAR_TO_PA
        si_data['P_out_Pa'] = si_data.get('P_out_bar', 0) * self.BAR_TO_PA
        
        # Convert viscosity to Pa·s
        si_data['mu_oil_Pa_s'] = si_data.get('mu_oil_cP', 0) * self.CP_TO_PA_S
        
        # Pipe diameter to m
        si_data['D_m'] = si_data.get('D_m', si_data.get('D_mm', 0) / 1000)

        # Power to Watts
        si_data['Pi_W'] = si_data.get('Pi_kW', 0) * 1000

        return si_data

    def _calculate_all_metrics(self, si_data):
        """Calculates all performance metrics for a single trial using SI units."""
        q_oil = si_data['Q_oil_m3_s']
        rho_oil = si_data['rho_oil_kg_m3']
        d = si_data['D_m']
        mu_oil = si_data['mu_oil_Pa_s']
        
        # Mass Flow
        mass_flow_oil = rho_oil * q_oil
        
        # Velocity
        area = self.PI * (d ** 2) / 4
        velocity = q_oil / area if area > 0 else 0
        
        # Reynolds Number
        reynolds_num = (rho_oil * velocity * d) / mu_oil if mu_oil > 0 else 0
        
        # Pressure Drop (from inlet/outlet pressures)
        delta_p_pa = si_data['P_in_Pa'] - si_data['P_out_Pa']
        delta_p_bar = delta_p_pa / self.BAR_TO_PA
        
        # Hydraulic Power
        pw_watts = q_oil * delta_p_pa
        pw_kw = pw_watts / 1000
        
        # Efficiency
        pi_watts = si_data['Pi_W']
        efficiency = (pw_watts / pi_watts) * 100 if pi_watts > 0 else 0
        
        # Gas-Oil Ratio
        q_gas = si_data['Q_gas_m3_s']
        gor = q_gas / q_oil if q_oil > 0 else 0
        
        # Separator Retention Time
        sep_vol = si_data.get('separator_volume_m3', 0)
        ret_time_s = sep_vol / q_oil if q_oil > 0 else 0
        ret_time_min = ret_time_s / 60

        return {
            "ΔP (bar)": round(delta_p_bar, 2),
            "V (m/s)": round(velocity, 2),
            "Re": int(reynolds_num),
            "Pw (kW)": round(pw_kw, 2),
            "η (%)": round(efficiency, 2),
            "GOR (m³/m³)": round(gor, 2),
            "t (min)": round(ret_time_min, 2)
        }

    def run_analysis(self):
        """Processes all trials, performs calculations, and stores results in a DataFrame."""
        for i, trial in enumerate(self.data):
            si_trial = self._convert_and_prepare_si_units(trial)
            calcs = self._calculate_all_metrics(si_trial)
            
            flow_regime = "Laminar" if calcs['Re'] < 2000 else ("Turbulent" if calcs['Re'] > 4000 else "Transitional")
            notes = f"Flow is {flow_regime}."
            if calcs['ΔP (bar)'] > 10:
                 notes += " High ΔP flagged."

            result_row = {
                "Trial": i + 1,
                "Q_oil (bbl/day)": trial['Q_oil_bbl_day'],
                "Q_gas (MMSCFD)": trial['Q_gas_MMSCFD'],
                "Water cut (%)": trial['water_cut_percent'],
                "P_in (bar)": trial['P_in_bar'],
                "P_out (bar)": trial['P_out_bar'],
                "Pi (kW)": trial['Pi_kW'],
                **calcs,
                "Notes": notes
            }
            self.results.append(result_row)
        
        self.df = pd.DataFrame(self.results)
        
        self.df_display = self.df[[
            "Trial", "Q_oil (bbl/day)", "Q_gas (MMSCFD)", "Water cut (%)", "P_in (bar)", "P_out (bar)", 
            "ΔP (bar)", "V (m/s)", "Re", "Pw (kW)", "Pi (kW)", "η (%)", "GOR (m³/m³)", "t (min)", "Notes"
        ]]

    def generate_model_calculation(self, trial_num=1):
        """Generates a detailed, step-by-step calculation for a specified trial."""
        if not self.results: return "No data processed."
        
        trial_data = self.data[trial_num - 1]
        si_data = self._convert_and_prepare_si_units(trial_data)
        results = self.df.iloc[trial_num-1]

        output = f"--- Model Calculation for Trial {trial_num} ---\n\n"
        output += f"1. Volumetric Flow (Q_oil) in m³/s:\n   Formula: Q_bbl_day * {self.BBL_DAY_TO_M3_S:.8f}\n   Substitution: {trial_data['Q_oil_bbl_day']} * {self.BBL_DAY_TO_M3_S:.8f}\n   Result: {si_data['Q_oil_m3_s']:.6f} m³/s\n\n"
        output += f"2. Superficial Velocity (V) in m/s:\n   Formula: 4 * Q / (π * D²)\n   Area = π * ({si_data['D_m']} m)² / 4 = {self.PI * (si_data['D_m'] ** 2) / 4:.6f} m²\n   Substitution: 4 * {si_data['Q_oil_m3_s']:.6f} / (π * {si_data['D_m']}²)\n   Result: {results['V (m/s)']} m/s\n\n"
        output += f"3. Reynolds Number (Re):\n   Formula: (ρ * V * D) / μ\n   μ = {trial_data['mu_oil_cP']} cP = {si_data['mu_oil_Pa_s']} Pa·s\n   Substitution: ({trial_data['rho_oil_kg_m3']} * {results['V (m/s)']} * {si_data['D_m']}) / {si_data['mu_oil_Pa_s']}\n   Result: {results['Re']}\n\n"
        output += f"4. Pressure Drop (ΔP) in bar:\n   Formula: P_in - P_out\n   Substitution: {trial_data['P_in_bar']} bar - {trial_data['P_out_bar']} bar\n   Result: {results['ΔP (bar)']} bar\n\n"
        output += f"5. Hydraulic Power (Pw) in kW:\n   Formula: Q_m³/s * ΔP_Pa / 1000\n   ΔP = {results['ΔP (bar)']} bar = {results['ΔP (bar)']*self.BAR_TO_PA} Pa\n   Substitution: {si_data['Q_oil_m3_s']:.6f} * {results['ΔP (bar)']*self.BAR_TO_PA} / 1000\n   Result: {results['Pw (kW)']} kW\n\n"
        output += f"6. Efficiency (η) in %:\n   Formula: (Pw / Pi) * 100\n   Substitution: ({results['Pw (kW)']} kW / {trial_data['Pi_kW']} kW) * 100\n   Result: {results['η (%)']} %\n\n"
        return output

    def plot_graphs(self):
        """Generates and saves the required X-Y plots with best-fit lines and equations."""
        if self.df is None or len(self.df) < 2:
            print("Warning: Not enough data to plot graphs (at least 2 data points required).")
            return

        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Plot 1: Flow rate (Q) vs Pressure drop (ΔP)
        fig, ax1 = plt.subplots(figsize=(10, 6))
        x1, y1 = self.df['Q_oil (bbl/day)'], self.df['ΔP (bar)']
        ax1.plot(x1, y1, 'o', color='blue', markersize=8, label='Data Points')
        m, b = np.polyfit(x1, y1, 1)
        ax1.plot(x1, m*x1 + b, '--', color='red', label=f'Fit: y={m:.4f}x + {b:.2f}')
        ax1.set_title('Q vs ΔP for Oil & Gas Flow', fontsize=16)
        ax1.set_xlabel('Oil Flow Rate (Q_oil) [bbl/day]', fontsize=12)
        ax1.set_ylabel('Pressure Drop (ΔP) [bar]', fontsize=12)
        ax1.legend()
        fig.tight_layout()
        plt.savefig('flow_vs_pressure_drop.png')
        plt.show()

        # Plot 2: Flow rate (Q) vs Efficiency (η)
        fig, ax2 = plt.subplots(figsize=(10, 6))
        x2, y2 = self.df['Q_oil (bbl/day)'], self.df['η (%)']
        ax2.plot(x2, y2, 'o', color='blue', markersize=8, label='Data Points')
        z = np.polyfit(x2, y2, 2)
        p = np.poly1d(z)
        xp = np.linspace(x2.min(), x2.max(), 100)
        ax2.plot(xp, p(xp), '--', color='green', label=f'Fit: y={z[0]:.4f}x² + {z[1]:.2f}x + {z[2]:.2f}')
        ax2.set_title('Q vs Efficiency for Oil & Gas Equipment', fontsize=16)
        ax2.set_xlabel('Oil Flow Rate (Q_oil) [bbl/day]', fontsize=12)
        ax2.set_ylabel('Efficiency (η) [%]', fontsize=12)
        ax2.legend()
        fig.tight_layout()
        plt.savefig('flow_vs_efficiency.png')
        plt.show()

    def generate_summary_report(self):
        """Generates a final text report summarizing the findings."""
        if self.df is None: return "No data."

        report = "--- Oil & Gas Process Analysis Report ---\n\n"
        report += "1. Flow Regime Classification:\n"
        regime_counts = self.df['Notes'].apply(lambda x: x.split('.')[0].split(' ')[-1]).value_counts()
        report += regime_counts.to_string() + "\n\n"

        report += "2. Key Performance Indicators (Mean Values):\n"
        report += f"  - Mean Pump/Compressor Efficiency: {self.df['η (%)'].mean():.2f} %\n"
        report += f"  - Mean Gas-Oil Ratio (GOR): {self.df['GOR (m³/m³)'].mean():.2f} m³/m³\n"
        report += f"  - Mean Pressure Drop: {self.df['ΔP (bar)'].mean():.2f} bar\n\n"

        max_eff_row = self.df.loc[self.df['η (%)'].idxmax()]
        report += "3. Peak Performance and Risks:\n"
        report += f"  - Maximum efficiency of {max_eff_row['η (%)']}% was observed in Trial {max_eff_row['Trial']} at an oil flow rate of {max_eff_row['Q_oil (bbl/day)']} bbl/day.\n"
        
        risks = self.df[self.df['Notes'].str.contains("High ΔP")]
        if not risks.empty:
            report += f"  - Safety Check: High pressure drop was flagged in Trial(s) {list(risks['Trial'])}, which may indicate flow assurance issues or equipment strain.\n"
        else:
            report += "  - Safety Check: No excessive pressure drops were flagged in the given trials.\n"
        
        if self.df['t (min)'].mean() > 0:
            report += f"  - Separator Adequacy: The average retention time is {self.df['t (min)'].mean():.2f} minutes. Typically, 1-3 minutes is sufficient for good separation, but this depends on fluid properties.\n"
        else:
             report += "  - Separator Adequacy: Retention time could not be calculated as separator volume was not provided.\n"

        report += "\n4. Conclusion:\n  The analysis indicates predominantly turbulent flow conditions. The efficiency curve can guide operations to the most energy-effective flow rate. Monitored pressure drops are crucial for maintaining pipeline integrity and throughput.\n"
        return report

# --- Main Execution Block ---
if __name__ == "__main__":
    #
    # 📌 --- USER INPUT SECTION --- 📌
    # Modify the list below with your experimental readings.
    # Provide 'separator_volume_m3' to calculate retention time.
    #
    input_readings = [
        {
            "Q_oil_bbl_day": 1200, "Q_gas_MMSCFD": 0.5, "water_cut_percent": 20,
            "P_in_bar": 25, "P_out_bar": 20, "T_C": 40, "D_m": 0.2, "L_m": 500,
            "rho_oil_kg_m3": 850, "mu_oil_cP": 2, "Pi_kW": 75,
            "separator_volume_m3": 5
        },
        {
            "Q_oil_bbl_day": 1500, "Q_gas_MMSCFD": 0.6, "water_cut_percent": 25,
            "P_in_bar": 30, "P_out_bar": 24, "T_C": 42, "D_m": 0.2, "L_m": 500,
            "rho_oil_kg_m3": 860, "mu_oil_cP": 2.5, "Pi_kW": 85,
            "separator_volume_m3": 5
        },
        {
            "Q_oil_bbl_day": 1800, "Q_gas_MMSCFD": 0.7, "water_cut_percent": 22,
            "P_in_bar": 35, "P_out_bar": 28, "T_C": 45, "D_m": 0.2, "L_m": 500,
            "rho_oil_kg_m3": 855, "mu_oil_cP": 2.2, "Pi_kW": 100,
            "separator_volume_m3": 5
        },
    ]

    analyzer = OilGasAnalysis(input_readings)
    
    analyzer.run_analysis()

    print("--- Calculated Process Metrics ---")
    print(analyzer.df_display.to_string())
    print("\n" + "="*100 + "\n")

    print(analyzer.generate_model_calculation())
    print("\n" + "="*100 + "\n")

    print(analyzer.generate_summary_report())
    print("\n" + "="*100 + "\n")
    
    print("Generating plots...")
    analyzer.plot_graphs()
    print("Analysis complete. Plots saved as 'flow_vs_pressure_drop.png' and 'flow_vs_efficiency.png'.")

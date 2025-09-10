import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

# --- 📌 Constants ---
DEFAULT_CONSTANTS = {
    'n_revolutions': 10,
    'Ec_rev_kwh': 750,
    'eta_T': 0.75,
    'rho_kg_m3': 1000,
    'g_ms2': 9.81,
    'A_m2': 0.49,
    'h_m': 0.1,
    'X_m': 0.31
}

def process_centrifugal_pump_data(trials, custom_constants=None):
    """
    Process centrifugal pump test data
    
    Args:
        trials: List of trial data [{'P.G.': float, 'V.G.': float, 't': float, 't_n': float}, ...]
        custom_constants: Dict with custom constants (optional)
    
    Returns:
        dict: Complete calculation results
    """
    try:
        # Use custom constants or defaults
        constants = DEFAULT_CONSTANTS.copy()
        if custom_constants:
            constants.update(custom_constants)
        
        # Extract constants
        n_revolutions = constants['n_revolutions']
        Ec_rev_kwh = constants['Ec_rev_kwh']
        eta_T = constants['eta_T']
        rho_kg_m3 = constants['rho_kg_m3']
        g_ms2 = constants['g_ms2']
        A_m2 = constants['A_m2']
        h_m = constants['h_m']
        X_m = constants['X_m']
        
        # Process trials
        results_data = []
        
        for i, trial in enumerate(trials):
            pg_kg_cm2 = float(trial["P.G."])
            vg_mm_hg = float(trial["V.G."])
            t_s = float(trial["t"])
            t_n_s = float(trial["t_n"])

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
                "P.G. (Kg/cm²)": round(pg_kg_cm2, 2),
                "V.G. (mm Hg)": round(vg_mm_hg, 1),
                "H (m)": round(H_m, 4),
                "Q (m³/s)": round(Q_m3_s, 6),
                "I/P (kW)": round(IP_kw, 4),
                "O/P (kW)": round(OP_kw, 4),
                "η (%)": round(eta_percent, 2),
            })

        # Calculate mean efficiency
        efficiencies = [r["η (%)"] for r in results_data if r["η (%)"] > 0]
        mean_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0

        # Generate model calculation
        model_calculation = generate_model_calculation(results_data[0] if results_data else None, constants)

        # Generate graph
        graph_base64 = generate_centrifugal_pump_graph(results_data)

        # Generate PDF report
        pdf_base64 = generate_centrifugal_pump_pdf(results_data, constants, mean_efficiency)

        return {
            'success': True,
            'results': results_data,
            'mean_efficiency': round(mean_efficiency, 2),
            'model_calculation': model_calculation,
            'graph_base64': graph_base64,
            'pdf_base64': pdf_base64
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_model_calculation(first_trial, constants):
    """Generate step-by-step model calculation for first trial"""
    if not first_trial:
        return "No data available for model calculation"
    
    try:
        # Extract values
        pg_kg_cm2 = first_trial['P.G. (Kg/cm²)']
        vg_mm_hg = first_trial['V.G. (mm Hg)']
        t_s = first_trial.get('t', 0)  # This would need to be passed separately
        t_n_s = first_trial.get('t_n', 0)  # This would need to be passed separately
        
        # Extract constants
        n_revolutions = constants['n_revolutions']
        Ec_rev_kwh = constants['Ec_rev_kwh']
        eta_T = constants['eta_T']
        rho_kg_m3 = constants['rho_kg_m3']
        g_ms2 = constants['g_ms2']
        A_m2 = constants['A_m2']
        h_m = constants['h_m']
        X_m = constants['X_m']
        
        # Step-by-step calculation
        steps = []
        
        # Step 1: Calculate Pressure Head
        pressure_head_pg = pg_kg_cm2 * 10.33
        pressure_head_vg = (vg_mm_hg * 10.33) / 760
        H_m = pressure_head_pg + pressure_head_vg + X_m
        steps.append(f"Step 1: Calculate Pressure Head (H)")
        steps.append(f"   H = [P.G. × 10.33] + [(V.G. × 10.33) / 760] + X")
        steps.append(f"   H = [{pg_kg_cm2} × 10.33] + [({vg_mm_hg}) × 10.33 / 760] + {X_m}")
        steps.append(f"   H = {H_m:.4f} m of H₂O")
        
        # Step 2: Calculate Flow Rate
        Q_m3_s = (A_m2 * h_m) / t_s
        steps.append(f"")
        steps.append(f"Step 2: Calculate Flow Rate (Q)")
        steps.append(f"   Q = (A × h) / t")
        steps.append(f"   Q = ({A_m2} m² × {h_m} m) / {t_s} s = {Q_m3_s:.6f} m³/s")
        
        # Step 3: Calculate Input Power
        IP_kw = (n_revolutions * 3600 * eta_T) / (t_n_s * Ec_rev_kwh)
        steps.append(f"")
        steps.append(f"Step 3: Calculate Input Power (I/P)")
        steps.append(f"   I/P = [n × 3600 × η_T] / [t_n × E_c]")
        steps.append(f"   I/P = [{n_revolutions} × 3600 × {eta_T}] / [{t_n_s} s × {Ec_rev_kwh}] = {IP_kw:.4f} kW")
        
        # Step 4: Calculate Output Power
        OP_kw = (rho_kg_m3 * g_ms2 * Q_m3_s * H_m) / 1000
        steps.append(f"")
        steps.append(f"Step 4: Calculate Output Power (O/P)")
        steps.append(f"   O/P = [ρ × g × Q × H] / 1000")
        steps.append(f"   O/P = [{rho_kg_m3} × {g_ms2} × {Q_m3_s:.6f} × {H_m:.4f}] / 1000 = {OP_kw:.4f} kW")
        
        # Step 5: Calculate Efficiency
        eta_percent = (OP_kw / IP_kw) * 100 if IP_kw > 0 else 0
        steps.append(f"")
        steps.append(f"Step 5: Calculate Efficiency (η)")
        steps.append(f"   η = [O/P / I/P] × 100")
        steps.append(f"   η = [{OP_kw:.4f} / {IP_kw:.4f}] × 100 = {eta_percent:.2f}%")
        
        return "\n".join(steps)
        
    except Exception as e:
        return f"Error in model calculation: {str(e)}"

def generate_centrifugal_pump_graph(results):
    """Generate characteristic curves graph"""
    try:
        if not results:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Create figure
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
        
        # Adjust layout
        fig.tight_layout(rect=[0, 0.05, 1, 1])

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        graph_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return graph_base64
        
    except Exception as e:
        print(f"Error generating graph: {e}")
        return None

def generate_centrifugal_pump_pdf(results, constants, mean_efficiency):
    """Generate PDF report for centrifugal pump experiment"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Centrifugal Pump Test Experiment", title_style))
        story.append(Spacer(1, 20))
        
        # Constants
        story.append(Paragraph("Experiment Constants:", styles['Heading2']))
        constants_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Number of revolutions (n)', f"{constants['n_revolutions']}", ''],
            ['Energy per revolution (E_c)', f"{constants['Ec_rev_kwh']}", 'kWh'],
            ['Turbine efficiency (η_T)', f"{constants['eta_T']}", ''],
            ['Water density (ρ)', f"{constants['rho_kg_m3']}", 'kg/m³'],
            ['Gravity (g)', f"{constants['g_ms2']}", 'm/s²'],
            ['Tank area (A)', f"{constants['A_m2']}", 'm²'],
            ['Water height (h)', f"{constants['h_m']}", 'm'],
            ['Height difference (X)', f"{constants['X_m']}", 'm']
        ]
        
        constants_table = Table(constants_data, colWidths=[2*inch, 1*inch, 0.8*inch])
        constants_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(constants_table)
        story.append(Spacer(1, 20))
        
        # Results table
        if results:
            story.append(Paragraph("Experimental Results:", styles['Heading2']))
            results_data = [['Trial', 'P.G. (Kg/cm²)', 'V.G. (mm Hg)', 'H (m)', 'Q (m³/s)', 'I/P (kW)', 'O/P (kW)', 'η (%)']]
            
            for result in results:
                results_data.append([
                    str(result['Trial']),
                    f"{result['P.G. (Kg/cm²)']:.2f}",
                    f"{result['V.G. (mm Hg)']:.1f}",
                    f"{result['H (m)']:.4f}",
                    f"{result['Q (m³/s)']:.6f}",
                    f"{result['I/P (kW)']:.4f}",
                    f"{result['O/P (kW)']:.4f}",
                    f"{result['η (%)']:.2f}"
                ])
            
            results_table = Table(results_data, colWidths=[0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch, 0.6*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(results_table)
            story.append(Spacer(1, 20))
        
        # Final result
        story.append(Paragraph(f"<b>Mean Efficiency (η) = {mean_efficiency:.2f}%</b>", styles['Heading2']))
        
        doc.build(story)
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

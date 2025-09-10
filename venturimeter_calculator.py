import math
import matplotlib.pyplot as plt
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

def calculate_venturimeter_data(readings, constants):
    """
    Calculate Venturimeter calibration data
    
    Args:
        readings: List of trial data [{'h1': float, 'h2': float, 't': float}, ...]
        constants: Dict with experiment constants
    
    Returns:
        dict: Complete calculation results
    """
    try:
        # Extract constants
        d1 = constants['d1'] / 1000  # Convert mm to m
        d2 = constants['d2'] / 1000  # Convert mm to m
        tank_area = constants['tank_length'] * constants['tank_width']  # m²
        water_height = constants['water_height']  # m
        g = constants['g']  # m/s²
        conversion_factor = constants['conversion_factor']
        
        # Calculate areas
        a1 = math.pi * (d1 ** 2) / 4  # Inlet area
        a2 = math.pi * (d2 ** 2) / 4  # Throat area
        
        # Validate that inlet area is larger than throat area
        if a1 <= a2:
            return {'success': False, 'error': 'Inlet diameter must be larger than throat diameter for Venturimeter to work properly'}
        
        # Calculate volume collected
        V = tank_area * water_height  # m³
        
        results = []
        cd_values = []
        
        for i, reading in enumerate(readings):
            h1 = float(reading['h1'])
            h2 = float(reading['h2'])
            t = float(reading['t'])
            
            # Calculate head of water
            H = ((h1 - h2) / 100) * conversion_factor  # m
            
            # Validate head is positive (h1 should be > h2 for proper flow)
            if H <= 0:
                return {'success': False, 'error': f'Trial {i+1}: h₁ ({h1} cm) must be greater than h₂ ({h2} cm) for positive head. Current head: {H:.4f} m'}
            
            # Calculate theoretical flow rate
            Qt = (a1 * a2 * math.sqrt(2 * g * H)) / math.sqrt(a1**2 - a2**2)  # m³/s
            
            # Calculate actual flow rate
            Qa = V / t  # m³/s
            
            # Calculate discharge coefficient
            Cd = Qa / Qt if Qt != 0 else 0
            
            cd_values.append(Cd)
            
            results.append({
                'trial': i + 1,
                'h1': h1,
                'h2': h2,
                't': t,
                'H': round(H, 4),
                'Qt': round(Qt, 6),
                'Qa': round(Qa, 6),
                'Cd': round(Cd, 4)
            })
        
        # Calculate mean Cd
        mean_cd = sum(cd_values) / len(cd_values) if cd_values else 0
        
        # Generate graph
        graph_base64 = generate_venturimeter_graph(results)
        
        # Generate PDF report
        pdf_base64 = generate_venturimeter_pdf(results, constants, mean_cd)
        
        return {
            'success': True,
            'results': results,
            'mean_cd': round(mean_cd, 4),
            'constants': {
                'd1': constants['d1'],
                'd2': constants['d2'],
                'a1': round(a1, 8),
                'a2': round(a2, 8),
                'tank_area': round(tank_area, 4),
                'volume_collected': round(V, 4)
            },
            'model_calculation': generate_model_calculation(results[0] if results else None, constants),
            'graph_base64': graph_base64,
            'pdf_base64': pdf_base64
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_venturimeter_graph(results):
    """Generate graph between Qt and Qa"""
    try:
        if not results:
            return None
        
        # Extract data
        Qt_values = [r['Qt'] for r in results]
        Qa_values = [r['Qa'] for r in results]
        
        # Create plot
        plt.figure(figsize=(10, 8))
        plt.scatter(Qt_values, Qa_values, color='red', s=100, alpha=0.7, label='Data Points')
        
        # Calculate best-fit line
        if len(Qt_values) > 1:
            # Linear regression
            n = len(Qt_values)
            sum_x = sum(Qt_values)
            sum_y = sum(Qa_values)
            sum_xy = sum(x * y for x, y in zip(Qt_values, Qa_values))
            sum_x2 = sum(x * x for x in Qt_values)
            
            # Calculate slope (Cd) and intercept
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Plot best-fit line
            x_line = [min(Qt_values), max(Qt_values)]
            y_line = [slope * x + intercept for x in x_line]
            plt.plot(x_line, y_line, 'b-', linewidth=2, 
                    label=f'Best-fit line: y = {slope:.4f}x + {intercept:.6f}')
        
        plt.xlabel('Theoretical Flow Rate, Qt (m³/s)', fontsize=12)
        plt.ylabel('Actual Flow Rate, Qa (m³/s)', fontsize=12)
        plt.title('Graph between Theoretical and Actual Flow', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add equation text
        if len(Qt_values) > 1:
            plt.text(0.05, 0.95, f'Slope (Cd) = {slope:.4f}', 
                    transform=plt.gca().transAxes, fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
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

def generate_model_calculation(first_trial, constants):
    """Generate step-by-step model calculation for first trial"""
    if not first_trial:
        return "No data available for model calculation"
    
    try:
        # Extract values
        h1 = first_trial['h1']
        h2 = first_trial['h2']
        t = first_trial['t']
        
        d1 = constants['d1'] / 1000  # Convert to m
        d2 = constants['d2'] / 1000
        tank_area = constants['tank_length'] * constants['tank_width']
        water_height = constants['water_height']
        g = constants['g']
        conversion_factor = constants['conversion_factor']
        
        # Step-by-step calculation
        steps = []
        
        # Step 1: Calculate areas
        a1 = math.pi * (d1 ** 2) / 4
        a2 = math.pi * (d2 ** 2) / 4
        steps.append(f"Step 1: Calculate areas")
        steps.append(f"   Inlet area, a₁ = πd₁²/4 = π × ({d1*1000:.1f}×10⁻³)²/4 = {a1:.8f} m²")
        steps.append(f"   Throat area, a₂ = πd₂²/4 = π × ({d2*1000:.1f}×10⁻³)²/4 = {a2:.8f} m²")
        
        # Step 2: Calculate volume
        V = tank_area * water_height
        steps.append(f"")
        steps.append(f"Step 2: Calculate volume collected")
        steps.append(f"   V = Area of tank × Height = {tank_area:.4f} × {water_height:.2f} = {V:.4f} m³")
        
        # Step 3: Calculate head
        H = ((h1 - h2) / 100) * conversion_factor
        steps.append(f"")
        steps.append(f"Step 3: Calculate head of water")
        steps.append(f"   H = [(h₁ - h₂)/100] × {conversion_factor} = [({h1} - {h2})/100] × {conversion_factor} = {H:.4f} m")
        
        # Step 4: Calculate theoretical flow rate
        Qt = (a1 * a2 * math.sqrt(2 * g * H)) / math.sqrt(a1**2 - a2**2)
        steps.append(f"")
        steps.append(f"Step 4: Calculate theoretical flow rate")
        steps.append(f"   Qt = (a₁ × a₂ × √(2gH)) / √(a₁² - a₂²)")
        steps.append(f"   Qt = ({a1:.8f} × {a2:.8f} × √(2×{g}×{H:.4f})) / √({a1**2:.10f} - {a2**2:.10f})")
        steps.append(f"   Qt = {Qt:.6f} m³/s")
        
        # Step 5: Calculate actual flow rate
        Qa = V / t
        steps.append(f"")
        steps.append(f"Step 5: Calculate actual flow rate")
        steps.append(f"   Qa = V/t = {V:.4f}/{t} = {Qa:.6f} m³/s")
        
        # Step 6: Calculate discharge coefficient
        Cd = Qa / Qt
        steps.append(f"")
        steps.append(f"Step 6: Calculate discharge coefficient")
        steps.append(f"   Cd = Qa/Qt = {Qa:.6f}/{Qt:.6f} = {Cd:.4f}")
        
        return "\n".join(steps)
        
    except Exception as e:
        return f"Error in model calculation: {str(e)}"

def generate_venturimeter_pdf(results, constants, mean_cd):
    """Generate PDF report for Venturimeter experiment"""
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
        story.append(Paragraph("Venturimeter Calibration Experiment", title_style))
        story.append(Spacer(1, 20))
        
        # Constants
        story.append(Paragraph("Experiment Constants:", styles['Heading2']))
        constants_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Inlet diameter (d₁)', f"{constants['d1']:.1f}", 'mm'],
            ['Throat diameter (d₂)', f"{constants['d2']:.1f}", 'mm'],
            ['Tank length', f"{constants['tank_length']:.2f}", 'm'],
            ['Tank width', f"{constants['tank_width']:.2f}", 'm'],
            ['Water height', f"{constants['water_height']:.2f}", 'm'],
            ['Gravity (g)', f"{constants['g']:.2f}", 'm/s²'],
            ['Conversion factor', f"{constants['conversion_factor']:.1f}", '']
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
            results_data = [['Trial', 'h₁ (cm)', 'h₂ (cm)', 't (s)', 'H (m)', 'Qt (m³/s)', 'Qa (m³/s)', 'Cd']]
            
            for result in results:
                results_data.append([
                    str(result['trial']),
                    f"{result['h1']:.1f}",
                    f"{result['h2']:.1f}",
                    f"{result['t']:.1f}",
                    f"{result['H']:.4f}",
                    f"{result['Qt']:.6f}",
                    f"{result['Qa']:.6f}",
                    f"{result['Cd']:.4f}"
                ])
            
            results_table = Table(results_data, colWidths=[0.6*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch, 1*inch, 1*inch, 0.6*inch])
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
        story.append(Paragraph(f"<b>Mean Discharge Coefficient (Cd) = {mean_cd:.4f}</b>", styles['Heading2']))
        
        doc.build(story)
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

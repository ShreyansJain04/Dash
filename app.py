import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context, no_update
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import io
import base64
import xlsxwriter
from io import BytesIO

# --- Enhanced Data Setup ---
data = {
    'State': ['APTS', 'APTS', 'APTS', 'KA', 'KA', 'KA', 'MH', 'MH', 'MH', 'TN', 'TN', 'TN', 'WB', 'WB', 'WB'],
    'Lost Reason': [
        'Bidding/ Requirement cancelled/ Uncertain/ Delay',
        'P- Same brand', 'Price discovery', 'P- Same brand', 'P- Other brand', 'Credit',
        'Credit', 'P- Same brand', 'Bidding/ Requirement cancelled/ Uncertain/ Delay',
        'Price discovery', 'Others', 'Bidding/ Requirement cancelled/ Uncertain/ Delay',
        'Price discovery', 'Bidding/ Requirement cancelled/ Uncertain/ Delay', 'Others'
    ],
    'Total Lost': [54, 37, 33, 66, 11, 7, 113, 46, 45, 53, 20, 17, 20, 11, 9],
    'P1': [6, 1, 1, 11, 1, 0, 0, 1, 3, 9, 5, 5, 2, 1, 0],
    'P2': [4, 4, 3, 9, 4, 0, 3, 1, 5, 7, 4, 1, 3, 2, 2],
    'P3': [8, 3, 3, 8, 0, 1, 0, 2, 5, 3, 3, 0, 0, 1, 2],
    'P4': [36, 29, 26, 38, 6, 6, 110, 42, 32, 34, 8, 11, 15, 7, 5]
}

df = pd.DataFrame(data)
avg_mt = {'APTS': 14.8, 'WB': 31.5, 'MH': 10.1, 'TN': 21.5, 'KA': 15.2}
df['Avg_MT'] = df['State'].map(avg_mt)

# Enhanced utility functions
def get_top_problems(state):
    state_data = df[df['State'] == state]
    return state_data.nlargest(3, 'Total Lost')

def calculate_state_summary(state):
    state_data = df[df['State'] == state]
    return {
        'total_lost': state_data['Total Lost'].sum(),
        'avg_mt': avg_mt[state],
        'problems_count': len(state_data),
        'highest_loss': state_data['Total Lost'].max(),
        'highest_loss_reason': state_data.loc[state_data['Total Lost'].idxmax(), 'Lost Reason']
    }

def convert_to_serializable(obj):
    """Convert pandas/numpy types to JSON serializable types"""
    if hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    elif hasattr(obj, 'tolist'):  # numpy array
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

def generate_export_data(state, calculations):
    """Generate export data for the current analysis"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert all data to JSON-serializable format
    export_data = {
        'timestamp': timestamp,
        'state': state,
        'analysis': calculations,
        'summary': calculate_state_summary(state)
    }
    
    return convert_to_serializable(export_data)

def create_excel_export(state, calculations_data):
    """Create a professionally formatted Excel report"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define professional formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': '#1a202c',
            'bg_color': '#e2e8f0',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': 'white',
            'bg_color': '#2c5aa0',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        subheader_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'font_color': '#1a202c',
            'bg_color': '#f8fafc',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        data_format = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        number_format = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0.0'
        })
        
        percentage_format = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0%'
        })
        
        currency_format = workbook.add_format({
            'font_size': 10,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0.0" MT"'
        })
        
        # 1. Executive Summary Sheet
        summary_df = pd.DataFrame({
            'Metric': [
                'State',
                'Analysis Date',
                'Total Lost Customers',
                'Average MT per Customer',
                'Total Recovery Potential (MT/month)',
                'Number of Problems Analyzed',
                'Highest Impact Problem'
            ],
            'Value': [
                state,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                calculate_state_summary(state)['total_lost'],
                f"{avg_mt[state]} MT",
                f"{calculations_data.get('total_mt', 0):.1f} MT/month",
                len(calculations_data.get('problems', [])),
                calculate_state_summary(state)['highest_loss_reason']
            ]
        })
        
        summary_df.to_excel(writer, sheet_name='Executive Summary', index=False, startrow=2)
        summary_sheet = writer.sheets['Executive Summary']
        
        # Format Executive Summary
        summary_sheet.merge_range('A1:B1', f'Recovery Analysis Report - {state}', title_format)
        summary_sheet.write('A3', 'Metric', header_format)
        summary_sheet.write('B3', 'Value', header_format)
        
        for row in range(len(summary_df)):
            summary_sheet.write(row + 3, 0, summary_df.iloc[row, 0], subheader_format)
            summary_sheet.write(row + 3, 1, summary_df.iloc[row, 1], data_format)
        
        summary_sheet.set_column('A:A', 25)
        summary_sheet.set_column('B:B', 30)
        
        # 2. Detailed Analysis Sheet
        analysis_data = []
        for problem in calculations_data.get('problems', []):
            for priority in problem['priorities']:
                analysis_data.append({
                    'Problem': problem['name'],
                    'Priority Level': priority['priority'],
                    'Lost Customers': priority['customers'],
                    'Conversion Rate': priority['conversion_rate'] / 100,
                    'Potential Customers': priority['potential_customers'],
                    'Recovery Potential (MT)': priority['potential_mt'],
                    'Problem Total (MT)': problem['total_mt']
                })
        
        if analysis_data:
            analysis_df = pd.DataFrame(analysis_data)
            analysis_df.to_excel(writer, sheet_name='Detailed Analysis', index=False, startrow=2)
            analysis_sheet = writer.sheets['Detailed Analysis']
            
            # Format Detailed Analysis
            analysis_sheet.merge_range('A1:G1', 'Detailed Recovery Potential Analysis', title_format)
            
            headers = ['Problem', 'Priority Level', 'Lost Customers', 'Conversion Rate', 
                      'Potential Customers', 'Recovery Potential (MT)', 'Problem Total (MT)']
            
            for col, header in enumerate(headers):
                analysis_sheet.write(2, col, header, header_format)
            
            # Apply data formatting
            for row in range(len(analysis_df)):
                analysis_sheet.write(row + 3, 0, analysis_df.iloc[row, 0], data_format)  # Problem
                analysis_sheet.write(row + 3, 1, analysis_df.iloc[row, 1], data_format)  # Priority
                analysis_sheet.write(row + 3, 2, analysis_df.iloc[row, 2], data_format)  # Lost Customers
                analysis_sheet.write(row + 3, 3, analysis_df.iloc[row, 3], percentage_format)  # Conversion Rate
                analysis_sheet.write(row + 3, 4, analysis_df.iloc[row, 4], number_format)  # Potential Customers
                analysis_sheet.write(row + 3, 5, analysis_df.iloc[row, 5], currency_format)  # Recovery Potential
                analysis_sheet.write(row + 3, 6, analysis_df.iloc[row, 6], currency_format)  # Problem Total
            
            # Set column widths
            analysis_sheet.set_column('A:A', 35)  # Problem
            analysis_sheet.set_column('B:B', 15)  # Priority Level
            analysis_sheet.set_column('C:C', 15)  # Lost Customers
            analysis_sheet.set_column('D:D', 15)  # Conversion Rate
            analysis_sheet.set_column('E:E', 18)  # Potential Customers
            analysis_sheet.set_column('F:F', 20)  # Recovery Potential
            analysis_sheet.set_column('G:G', 18)  # Problem Total
        
        # 3. Problem Summary Sheet
        problem_summary_data = []
        for problem in calculations_data.get('problems', []):
            total_customers = sum(p['customers'] for p in problem['priorities'])
            avg_conversion = sum(p['conversion_rate'] for p in problem['priorities']) / len(problem['priorities'])
            
            problem_summary_data.append({
                'Problem': problem['name'],
                'Total Lost Customers': total_customers,
                'Average Conversion Rate': avg_conversion / 100,
                'Recovery Potential (MT/month)': problem['total_mt'],
                'Percentage of Total Recovery': problem['total_mt'] / calculations_data.get('total_mt', 1) if calculations_data.get('total_mt', 0) > 0 else 0
            })
        
        if problem_summary_data:
            problem_df = pd.DataFrame(problem_summary_data)
            problem_df.to_excel(writer, sheet_name='Problem Summary', index=False, startrow=2)
            problem_sheet = writer.sheets['Problem Summary']
            
            # Format Problem Summary
            problem_sheet.merge_range('A1:E1', 'Problem-wise Recovery Summary', title_format)
            
            headers = ['Problem', 'Total Lost Customers', 'Average Conversion Rate', 
                      'Recovery Potential (MT/month)', 'Percentage of Total Recovery']
            
            for col, header in enumerate(headers):
                problem_sheet.write(2, col, header, header_format)
            
            # Apply data formatting
            for row in range(len(problem_df)):
                problem_sheet.write(row + 3, 0, problem_df.iloc[row, 0], data_format)
                problem_sheet.write(row + 3, 1, problem_df.iloc[row, 1], data_format)
                problem_sheet.write(row + 3, 2, problem_df.iloc[row, 2], percentage_format)
                problem_sheet.write(row + 3, 3, problem_df.iloc[row, 3], currency_format)
                problem_sheet.write(row + 3, 4, problem_df.iloc[row, 4], percentage_format)
            
            # Set column widths
            problem_sheet.set_column('A:A', 35)
            problem_sheet.set_column('B:B', 20)
            problem_sheet.set_column('C:C', 22)
            problem_sheet.set_column('D:D', 25)
            problem_sheet.set_column('E:E', 28)
        
        # 4. Raw Data Sheet
        state_data = df[df['State'] == state]
        state_data.to_excel(writer, sheet_name='Raw Data', index=False, startrow=2)
        raw_sheet = writer.sheets['Raw Data']
        
        # Format Raw Data
        raw_sheet.merge_range('A1:H1', f'Raw Data for {state}', title_format)
        
        for col, header in enumerate(state_data.columns):
            raw_sheet.write(2, col, header, header_format)
        
        for row in range(len(state_data)):
            for col in range(len(state_data.columns)):
                raw_sheet.write(row + 3, col, state_data.iloc[row, col], data_format)
        
        # Auto-adjust column widths for raw data
        for col in range(len(state_data.columns)):
            max_width = max(len(str(state_data.columns[col])), 
                           max(len(str(state_data.iloc[row, col])) for row in range(len(state_data))))
            raw_sheet.set_column(col, col, min(max_width + 2, 30))
    
    output.seek(0)
    return output

# --- Enhanced App Setup ---
app = dash.Dash(__name__, 
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
                ])

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
                 <style>
             .metric-card {
                 background: linear-gradient(135deg, #2c5aa0 0%, #1e4078 100%);
                 color: white;
                 border-radius: 12px;
                 padding: 20px;
                 margin: 10px 0;
                 box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                 transition: transform 0.2s ease;
             }
             .metric-card:hover {
                 transform: translateY(-3px);
             }
             .priority-section {
                 background: #f8fafc;
                 border-radius: 12px;
                 padding: 20px;
                 margin: 15px 0;
                 border-left: 5px solid #2c5aa0;
                 border: 1px solid #e2e8f0;
             }
             .result-card {
                 background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
                 color: white;
                 border-radius: 12px;
                 padding: 20px;
                 margin: 10px 0;
                 box-shadow: 0 4px 12px rgba(0,0,0,0.15);
             }
             .total-summary {
                 background: linear-gradient(135deg, #2c5aa0 0%, #1a365d 100%);
                 color: white;
                 border-radius: 16px;
                 padding: 25px;
                 margin: 20px 0;
                 text-align: center;
                 font-size: 1.5rem;
                 font-weight: bold;
                 box-shadow: 0 6px 20px rgba(44,90,160,0.25);
             }
             .custom-slider .rc-slider-track {
                 background: linear-gradient(to right, #2c5aa0, #1e4078);
             }
             .custom-slider .rc-slider-handle {
                 border: 3px solid #2c5aa0;
                 background: white;
             }
             .header-gradient {
                 background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                 color: white;
                 padding: 30px 0;
                 margin-bottom: 30px;
                 border-radius: 0 0 20px 20px;
             }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Enhanced Layout
app.layout = dbc.Container([
    # Header Section
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                                         html.H1([
                         html.I(className="fas fa-chart-line me-3"),
                         "Recovery Analytics Dashboard"
                     ], className="mb-2"),
                     html.P("Strategic State-wise Recovery Potential Analysis", 
                            className="lead mb-0")
                ], width=8),
                dbc.Col([
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-download me-2"),
                            "Export Analysis"
                        ], id="export-btn", color="light", outline=True, className="me-2"),
                        dbc.Button([
                            html.I(className="fas fa-sync-alt me-2"),
                            "Reset All"
                        ], id="reset-btn", color="light", outline=True)
                    ], className="text-end")
                ], width=4)
            ], align="center")
        ])
    ], className="header-gradient"),
    
    # Controls Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label([
                        html.I(className="fas fa-map-marker-alt me-2"),
                        "Select State for Analysis:"
                    ], className="fw-bold mb-2"),
                    dcc.Dropdown(
                        id='state-dropdown',
                        options=[
                            {'label': f"{s} ({calculate_state_summary(s)['total_lost']} Total Lost)", 
                             'value': s} for s in df['State'].unique()
                        ],
                        value='APTS',
                        className="mb-3"
                    ),
                    html.Div(id="state-summary-cards")
                ])
            ])
        ], width=4),
        dbc.Col([
            html.Div(id="state-overview-chart")
        ], width=8)
    ], className="mb-4"),
    
    # Main Analysis Section
    html.Div(id='state-content'),
    
    # Export Modal
    dbc.Modal([
        dbc.ModalHeader("Export Analysis Results"),
        dbc.ModalBody(id="export-modal-body"),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-export", className="ms-auto", n_clicks=0)
        ])
    ], id="export-modal", is_open=False, size="lg"),
    
    # Store for calculations
    dcc.Store(id='calculations-store', data={})
    
], fluid=True)

# --- Enhanced Callbacks ---

@app.callback(
    [Output('state-summary-cards', 'children'),
     Output('state-overview-chart', 'children')],
    Input('state-dropdown', 'value')
)
def update_state_overview(selected_state):
    if not selected_state:
        return [], []
    
    summary = calculate_state_summary(selected_state)
    
    # Summary Cards
    cards = dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-2x mb-2"),
                html.H4(f"{summary['total_lost']}", className="mb-1"),
                html.Small("Total Lost Customers")
            ], className="metric-card text-center")
        ], width=6),
        dbc.Col([
            html.Div([
                html.I(className="fas fa-weight fa-2x mb-2"),
                html.H4(f"{summary['avg_mt']}", className="mb-1"),
                html.Small("Avg MT per Customer")
            ], className="metric-card text-center")
        ], width=6)
    ])
    
    # Overview Chart
    state_data = df[df['State'] == selected_state]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Lost Customers by Reason', 'Priority Distribution'),
        specs=[[{"type": "pie"}, {"type": "bar"}]]
    )
    
    # Pie chart for lost reasons
    fig.add_trace(
        go.Pie(
            labels=state_data['Lost Reason'],
            values=state_data['Total Lost'],
            name="Lost Customers",
            hole=0.4,
            marker_colors=px.colors.qualitative.Set3
        ),
        row=1, col=1
    )
    
    # Bar chart for priority distribution
    priorities = ['P1', 'P2', 'P3', 'P4']
    priority_totals = [state_data[p].sum() for p in priorities]
    
    fig.add_trace(
        go.Bar(
            x=priorities,
            y=priority_totals,
            name="Priority Distribution",
            marker_color=['#dc3545', '#fd7e14', '#0d6efd', '#198754']
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text=f"Overview for {selected_state}",
        title_x=0.5
    )
    
    chart = dcc.Graph(figure=fig, config={'displayModeBar': False})
    
    return cards, dbc.Card([dbc.CardBody(chart)])

@app.callback(
    Output('state-content', 'children'),
    Input('state-dropdown', 'value')
)
def update_state_content(selected_state):
    if not selected_state:
        return []
    
    state_data = get_top_problems(selected_state)
    content = []
    
    # Priority Conversion Rates Section
    for idx, (_, row) in enumerate(state_data.iterrows()):
        problem = row['Lost Reason']
        
        # Problem header with metrics
        problem_header = dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-exclamation-circle me-2"),
                    f"Problem {idx + 1}: {problem}"
                ], className="text-primary"),
                html.P(f"Total Lost: {row['Total Lost']} customers", className="text-muted")
            ], width=8),
            dbc.Col([
                dbc.Badge(f"Priority Score: {row['Total Lost']}", 
                         color="danger", className="fs-6")
            ], width=4, className="text-end")
        ])
        
        # Sliders for each priority
        slider_group = []
        for priority in ['P1', 'P2', 'P3', 'P4']:
            customers = row[priority]
            slider_id = {'type': 'slider', 'state': selected_state, 'problem': idx, 'priority': priority}
            
            color_map = {'P1': 'danger', 'P2': 'warning', 'P3': 'info', 'P4': 'success'}
            
            slider_card = dbc.Card([
                dbc.CardBody([
                    html.Div([
                        dbc.Badge(f"{priority}", color=color_map[priority], className="me-2"),
                        html.Strong(f"{customers} customers")
                    ], className="mb-3"),
                    html.Label("Conversion Rate:", className="small text-muted mb-1"),
                    dcc.Slider(
                        id=slider_id,
                        min=0, max=100, step=5, value=50,
                        marks={i: f"{i}%" for i in range(0, 101, 25)},
                        className="custom-slider",
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ], className="h-100")
            
            slider_group.append(dbc.Col(slider_card, md=3))
        
        problem_section = html.Div([
            problem_header,
            dbc.Row(slider_group, className="g-3 mb-4")
        ], className="priority-section")
        
        content.append(problem_section)
    
    # Results Section
    results_section = []
    for idx, (_, row) in enumerate(state_data.iterrows()):
        result_id = {'type': 'result', 'state': selected_state, 'problem': idx}
        results_section.append(
            html.Div(
                id=result_id,
                className="result-card",
                children=[
                    html.I(className="fas fa-calculator me-2"),
                    f"Calculating potential for: {row['Lost Reason']}..."
                ]
            )
        )
    
    # Total section
    total_id = {'type': 'total', 'state': selected_state}
    results_section.append(
        html.Div(
            id=total_id,
            className="total-summary",
            children=[
                html.I(className="fas fa-trophy me-3"),
                "Total Recovery Potential will appear here"
            ]
        )
    )
    
    content.append(
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-bar me-2"),
                "Recovery Potential Analysis"
            ], className="h4"),
            dbc.CardBody(results_section)
        ], className="mt-4")
    )
    
    return content

# Enhanced calculation callback with data storage
@app.callback(
    [Output({'type': 'result', 'state': ALL, 'problem': ALL}, 'children'),
     Output({'type': 'total', 'state': ALL}, 'children'),
     Output('calculations-store', 'data')],
    [Input({'type': 'slider', 'state': ALL, 'problem': ALL, 'priority': ALL}, 'value')],
    [State('state-dropdown', 'value')]
)
def update_calculations(slider_values, selected_state):
    if not slider_values or not selected_state:
        return [], [], {}
    
    state_data = get_top_problems(selected_state)
    avg_mt_value = avg_mt[selected_state]
    
    problem_results = []
    total_mt = 0
    calculations_data = {'state': selected_state, 'problems': []}
    
    for problem_idx in range(len(state_data)):
        row = state_data.iloc[problem_idx]
        problem = row['Lost Reason']
        
        problem_sliders = slider_values[problem_idx*4:(problem_idx+1)*4]
        
        if len(problem_sliders) == 4:
            problem_total = 0
            details = []
            problem_calc = {'name': problem, 'priorities': []}
            
            for i, priority in enumerate(['P1', 'P2', 'P3', 'P4']):
                customers = row[priority]
                conversion_rate = problem_sliders[i] if problem_sliders[i] is not None else 50
                potential_customers = customers * (conversion_rate / 100)
                potential_mt = potential_customers * avg_mt_value
                problem_total += potential_mt
                
                priority_calc = {
                    'priority': priority,
                    'customers': customers,
                    'conversion_rate': conversion_rate,
                    'potential_customers': potential_customers,
                    'potential_mt': potential_mt
                }
                problem_calc['priorities'].append(priority_calc)
                
                if customers > 0:
                    details.append(
                        html.Div([
                            dbc.Badge(priority, color="light", text_color="dark", className="me-2"),
                            f"{customers} customers × {conversion_rate}% × {avg_mt_value} MT = ",
                            html.Strong(f"{potential_mt:.1f} MT", className="text-warning")
                        ], className="mb-1")
                    )
            
            total_mt += problem_total
            problem_calc['total_mt'] = problem_total
            calculations_data['problems'].append(problem_calc)
            
            result_content = [
                html.Div([
                    html.I(className="fas fa-industry me-2"),
                    html.Strong(f"{problem}", className="fs-5")
                ], className="mb-3"),
                html.Div([
                    html.I(className="fas fa-target me-2"),
                    f"Recovery Potential: ",
                    html.Strong(f"{problem_total:.1f} MT/month", className="fs-4 text-warning")
                ], className="mb-3"),
                html.Div(details, className="small")
            ]
            problem_results.append(result_content)
    
    calculations_data['total_mt'] = total_mt
    
    total_content = [
        html.I(className="fas fa-trophy me-3"),
        f"TOTAL RECOVERY POTENTIAL: ",
        html.Strong(f"{total_mt:.1f} MT/MONTH", className="fs-3"),
        html.Br(),
        html.Small(f"for {selected_state} state", className="opacity-75")
    ]
    
    return problem_results, [total_content], calculations_data

# Reset functionality
@app.callback(
    Output({'type': 'slider', 'state': ALL, 'problem': ALL, 'priority': ALL}, 'value'),
    Input('reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_all_sliders(n_clicks):
    if n_clicks:
        ctx = callback_context
        if ctx.triggered:
            # Get the number of sliders from the pattern-matching callback context
            return [50] * len(ctx.outputs_list)
    return no_update

# Export functionality
@app.callback(
    [Output('export-modal', 'is_open'),
     Output('export-modal-body', 'children')],
    [Input('export-btn', 'n_clicks'),
     Input('close-export', 'n_clicks')],
    [State('calculations-store', 'data'),
     State('state-dropdown', 'value')],
    prevent_initial_call=True
)
def handle_export(export_clicks, close_clicks, calculations_data, selected_state):
    ctx = callback_context
    if not ctx.triggered:
        return False, ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'close-export':
        return False, ""
    
    if trigger_id == 'export-btn' and calculations_data:
        export_data = generate_export_data(selected_state, calculations_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create JSON download
        json_string = json.dumps(export_data, indent=2)
        json_encoded = base64.b64encode(json_string.encode()).decode()
        
        # Create Excel download
        excel_buffer = create_excel_export(selected_state, calculations_data)
        excel_encoded = base64.b64encode(excel_buffer.getvalue()).decode()
        
        download_content = [
            html.Div([
                html.I(className="fas fa-check-circle text-success me-2", style={'fontSize': '24px'}),
                html.H4("Export Ready!", className="text-success d-inline")
            ], className="mb-3"),
            
            html.P(f"Professional analysis report for {selected_state} state is ready for download.", 
                   className="lead"),
            
            dbc.Card([
                dbc.CardBody([
                    html.H6("📊 Analysis Summary:", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Strong("Total Recovery Potential:"),
                            html.Br(),
                            html.Span(f"{calculations_data.get('total_mt', 0):.1f} MT/month", 
                                     className="text-primary fs-5")
                        ], md=6),
                        dbc.Col([
                            html.Strong("Problems Analyzed:"),
                            html.Br(),
                            html.Span(f"{len(calculations_data.get('problems', []))}", 
                                     className="text-info fs-5")
                        ], md=6)
                    ])
                ])
            ], className="mb-4", color="light"),
            
            html.H6("📁 Download Options:", className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-file-excel text-success", 
                                      style={'fontSize': '48px'}),
                                html.H5("Excel Report", className="mt-2"),
                                html.P("Professional formatted spreadsheet with multiple sheets", 
                                      className="text-muted small"),
                                html.A(
                                    dbc.Button([
                                        html.I(className="fas fa-download me-2"),
                                        "Download Excel"
                                    ], color="success", block=True),
                                    href=f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_encoded}",
                                    download=f"recovery_analysis_{selected_state}_{timestamp}.xlsx"
                                )
                            ], className="text-center")
                        ])
                    ], className="h-100")
                ], md=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-file-code text-primary", 
                                      style={'fontSize': '48px'}),
                                html.H5("JSON Data", className="mt-2"),
                                html.P("Raw data format for integration and analysis", 
                                      className="text-muted small"),
                                html.A(
                                    dbc.Button([
                                        html.I(className="fas fa-download me-2"),
                                        "Download JSON"
                                    ], color="primary", block=True),
                                    href=f"data:application/json;charset=utf-8;base64,{json_encoded}",
                                    download=f"recovery_analysis_{selected_state}_{timestamp}.json"
                                )
                            ], className="text-center")
                        ])
                    ], className="h-100")
                ], md=6)
            ], className="g-3"),
            
            html.Hr(className="my-4"),
            html.Small([
                html.I(className="fas fa-info-circle me-1"),
                f"Reports generated on {export_data['timestamp']}"
            ], className="text-muted")
        ]
        
        return True, download_content
    
    return False, ""

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

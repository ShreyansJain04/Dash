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
        
        # Create download content
        json_string = json.dumps(export_data, indent=2)
        encoded = base64.b64encode(json_string.encode()).decode()
        
        download_content = [
            html.H5("Export Successful!"),
            html.P(f"Analysis for {selected_state} state ready for download."),
            html.Hr(),
            html.H6("Summary:"),
            html.Ul([
                html.Li(f"Total Recovery Potential: {calculations_data.get('total_mt', 0):.1f} MT/month"),
                html.Li(f"Number of Problems Analyzed: {len(calculations_data.get('problems', []))}"),
                html.Li(f"Export Time: {export_data['timestamp']}")
            ]),
            html.Hr(),
            html.A(
                dbc.Button([
                    html.I(className="fas fa-download me-2"),
                    "Download JSON Report"
                ], color="primary", size="lg"),
                href=f"data:application/json;charset=utf-8;base64,{encoded}",
                download=f"recovery_analysis_{selected_state}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        ]
        
        return True, download_content
    
    return False, ""

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

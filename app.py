import dash
from dash import dcc, html, Input, Output, State, ALL
import pandas as pd
import dash_bootstrap_components as dbc

# --- Data Setup ---
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

# Get top 3 problems per state
def get_top_problems(state):
    state_data = df[df['State'] == state]
    return state_data.nlargest(3, 'Total Lost')

# --- App Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("State-wise Recovery Potential Dashboard", className="mb-4 text-center"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Select State:", className="fw-bold"),
            dcc.Dropdown(
                id='state-dropdown',
                options=[{'label': s, 'value': s} for s in df['State'].unique()],
                value='APTS'
            )
        ], width=4)
    ], className="mb-4"),
    
    html.Div(id='state-content')
], fluid=True)

# --- Callbacks ---
@app.callback(
    Output('state-content', 'children'),
    Input('state-dropdown', 'value')
)
def update_state_content(selected_state):
    state_data = get_top_problems(selected_state)
    avg_mt_value = avg_mt[selected_state]
    
    content = []
    
    # Priority Conversion Rates Section
    sliders_section = []
    
    for idx, (_, row) in enumerate(state_data.iterrows()):
        problem = row['Lost Reason']
        sliders_section.append(html.H4(f"Problem: {problem}", className="mt-4"))
        
        slider_group = []
        for priority in ['P1', 'P2', 'P3', 'P4']:
            customers = row[priority]
            slider_id = {'type': 'slider', 'state': selected_state, 'problem': idx, 'priority': priority}
            
            slider_group.append(dbc.Col([
                html.Label(f"{priority} Customers: {customers}"),
                dcc.Slider(
                    id=slider_id,
                    min=0, max=100, step=1, value=50,
                    marks={i: f"{i}%" for i in range(0, 101, 20)},
                    className="mb-3"
                )
            ], md=3))
        
        sliders_section.append(dbc.Row(slider_group, className="g-4"))
    
    content.append(
        dbc.Card([
            dbc.CardHeader("Priority Conversion Rates", className="h4"),
            dbc.CardBody(sliders_section)
        ], className="mb-4")
    )
    
    # Results Section
    results_section = []
    for idx, (_, row) in enumerate(state_data.iterrows()):
        problem = row['Lost Reason']
        result_id = {'type': 'result', 'state': selected_state, 'problem': idx}
        
        results_section.append(
            html.Div(
                id=result_id,
                className="alert alert-info p-3 mb-3",
                children=f"Adjust sliders above to see calculations for: {problem}"
            )
        )
    
    # Total section
    total_id = {'type': 'total', 'state': selected_state}
    results_section.append(
        html.Div(
            id=total_id,
            className="alert alert-success h4 text-center",
            children="Total will appear here"
        )
    )
    
    content.append(
        dbc.Card([
            dbc.CardHeader("Potential Recovery Calculations", className="h4"),  
            dbc.CardBody(results_section)
        ])
    )
    
    return content

# Callback for individual problem calculations
@app.callback(
    [Output({'type': 'result', 'state': ALL, 'problem': ALL}, 'children'),
     Output({'type': 'total', 'state': ALL}, 'children')],
    [Input({'type': 'slider', 'state': ALL, 'problem': ALL, 'priority': ALL}, 'value')],
    [State('state-dropdown', 'value')]
)
def update_calculations(slider_values, selected_state):
    if not slider_values or not selected_state:
        return [], []
    
    state_data = get_top_problems(selected_state)
    avg_mt_value = avg_mt[selected_state]
    
    # Group slider values by problem
    problem_results = []
    total_mt = 0
    
    for problem_idx in range(len(state_data)):
        row = state_data.iloc[problem_idx]
        problem = row['Lost Reason']
        
        # Get slider values for this problem (4 sliders: P1, P2, P3, P4)
        problem_sliders = slider_values[problem_idx*4:(problem_idx+1)*4]
        
        if len(problem_sliders) == 4:
            problem_total = 0
            details = []
            
            for i, priority in enumerate(['P1', 'P2', 'P3', 'P4']):
                customers = row[priority]
                conversion_rate = problem_sliders[i] if problem_sliders[i] is not None else 50
                potential_customers = customers * (conversion_rate / 100)
                potential_mt = potential_customers * avg_mt_value
                problem_total += potential_mt
                
                if customers > 0:  # Only show if there are customers
                    details.append(f"{priority}: {customers} customers × {conversion_rate}% × {avg_mt_value} MT = {potential_mt:.1f} MT")
            
            total_mt += problem_total
            
            result_text = [
                html.Strong(f"{problem}"),
                html.Br(),
                html.Span(f"Total Potential: {problem_total:.1f} MT/month", style={'fontSize': '16px', 'color': '#0066cc'}),
                html.Br(),
                html.Small(html.Ul([html.Li(detail) for detail in details if detail]))
            ]
            problem_results.append(result_text)
        else:
            problem_results.append(f"Loading calculations for {problem}...")
    
    total_text = f"🎯 TOTAL POTENTIAL RECOVERY: {total_mt:.1f} MT/MONTH for {selected_state}"
    
    return problem_results, [total_text]

if __name__ == '__main__':
    app.run_server(debug=True, port=8053)

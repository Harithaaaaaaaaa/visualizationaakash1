import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json,os

# # Load and preprocess
# data = pd.read_csv(r"C:\Users\actionfi\Desktop\Projects\Aakash\visualization for tag\device_management_customerdevicedata.csv")

csv_path = os.path.join(os.path.dirname(__file__),"data","device_management_customerdevicedata.csv")
data = pd.read_csv(csv_path)


data['timestamp'] = data["json_1"].apply(lambda x: json.loads(x)['timestamp'] if isinstance(x,str) else x['timestamp'])

data['timestamp'] = pd.to_datetime(data['timestamp'],utc=True)
# Extract extra columns if not already present
if 'year_month_day' not in data.columns:
    data['year_month_day'] = data['timestamp'].dt.to_period('D').astype(str)

data['tags_count'] = data['json_1'].apply(lambda x: len(json.loads(x)['tags']) if isinstance(x,str) else len(x['tags']))

data['device_id_id']= data['device_id_id'].astype(str)

app = dash.Dash(__name__)
app.title = "RFID Dashboard"

app.layout = html.Div([
    html.H1("RFID Device Dashboard", style={'textAlign': 'center'}),
    
    # Filters
    html.Div([
        html.Label("Select Device:"),
        dcc.Dropdown(
            id='device-dropdown',
            options=[{"label": str(dev), "value": dev} for dev in sorted(data['device_id_id'].unique())],
            value=data['device_id_id'].unique()[0]
        ),
        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id='date-picker',
            start_date=data['timestamp'].min().date(),
            end_date=data['timestamp'].max().date(),
            # start_date_placeholder_text="Start Date",
            # end_date_placeholder_text="End Date",
            display_format='YYYY-MM-DD'
        ),
    ], style={'width': '50%', 'margin': 'auto'}),

    html.Br(),

    # KPIs
    html.Div(id='kpi-output', style={'display': 'flex', 'justifyContent': 'space-around'}),

    html.Br(),

    # Charts
    html.Div([
        dcc.Graph(id='bar-tags'),
        dcc.Graph(id='bar-sessions'),
        dcc.Graph(id='line-tags')
    ])
])

# Callback
@app.callback(
    [Output('kpi-output', 'children'),
     Output('bar-tags', 'figure'),
     Output('bar-sessions', 'figure'),
     Output('line-tags', 'figure')],
    [Input('device-dropdown', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_dashboard(device_id, start_date, end_date):


    df = data.copy()
    print("data df :",df)
    
    if device_id:
        df = data[data['device_id_id'] == device_id]
    
    if start_date:
        df = data[data['timestamp'] >= pd.to_datetime(start_date).tz_localize('UTC')]
    
    if end_date:
        df = data[data['timestamp'] <= pd.to_datetime(end_date).tz_localize('UTC')]

    if device_id and start_date and end_date:
        df = data[(data['device_id_id'] == device_id) & (data['timestamp'] >= pd.to_datetime(start_date).tz_localize('UTC')) & (data['timestamp'] <=pd.to_datetime(end_date).tz_localize('UTC'))]
    
    # if not device_id:
    #     df = data[
    #     (data['device_id_id'] == device_id) &
    #     (data['timestamp'] >= pd.to_datetime(start_date).tz_localize ('UTC')) &
    #     (data['timestamp'] <= pd.to_datetime(end_date).tz_localize ('UTC'))
    # ]
    # else:
    # # Filter data
    #     df = data[
    #         (data['device_id_id'] == device_id) &
    #         (data['timestamp'] >= pd.to_datetime(start_date).tz_localize ('UTC')) &
    #         (data['timestamp'] <= pd.to_datetime(end_date).tz_localize ('UTC'))
    #     ]
    # print("df:",df)
    # KPIs
    total_tags = df['tags_count'].sum()
    total_sessions = df['int_1'].nunique()
    total_success = (df['char_1'] == 'success').sum()
    total_failures = (df['char_1'] != 'success').sum()
    total_rows = len(df)
    success_rate = (total_success / total_rows * 100) if total_rows else 0

    kpis = [
        html.Div([
            html.H4("Total Tags"), html.P(f"{total_tags}")
        ], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'width': '15%', 'textAlign': 'center'}),
        html.Div([
            html.H4("Sessions"), html.P(f"{total_sessions}")
        ], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'width': '15%', 'textAlign': 'center'}),
        html.Div([
            html.H4("Successes"), html.P(f"{total_success}")
        ], style={'backgroundColor': '#e0ffe0', 'padding': '10px', 'width': '15%', 'textAlign': 'center'}),
        html.Div([
            html.H4("Failures"), html.P(f"{total_failures}")
        ], style={'backgroundColor': '#ffe0e0', 'padding': '10px', 'width': '15%', 'textAlign': 'center'}),
        html.Div([
            html.H4("Success Rate (%)"), html.P(f"{success_rate:.2f}")
        ], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'width': '15%', 'textAlign': 'center'})
    ]

    # Bar chart - Tags count
    df_tags = df.groupby('device_id_id', as_index=True)['tags_count'].sum()
    fig_tags = px.bar(df_tags, x='device_id_id', y='tags_count', title='Tag Reads per Device')

    # Bar chart - Sessions
    df_sessions = df.groupby('device_id_id', as_index=False)['int_1'].nunique().rename(columns={'int_1': 'sessions'})
    fig_sessions = px.bar(df_sessions, x='device_id_id', y='sessions', title='Sessions per Device', color_discrete_sequence=['red'])

    # Line chart - Time series
    df_line = df.groupby('year_month_day', as_index=False)['tags_count'].sum()
    fig_line = px.line(df_line, x='year_month_day', y='tags_count', title='Daily Tag Reads', markers=True)

    return kpis, fig_tags, fig_sessions, fig_line

# Run
if __name__ == '__main__':
    port = int(os.environ.get("PORT",8050))
    app.run(host = "0.0.0.0",port=port,debug=True)

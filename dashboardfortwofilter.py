import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import datetime
import re
# Load and preprocess
# data = pd.read_csv(r"C:\Users\actionfi\Desktop\Projects\Aakash\visualization for tag\device_management_customerdevicedata.csv")


csv_path = os.path.join(os.path.dirname(__file__),"data","device_management_customerdevicedata.csv")
data = pd.read_csv(csv_path)

data['timestamp'] = data["json_1"].apply(lambda x: json.loads(x)['timestamp'] if isinstance(x,str) else x['timestamp'])

data['timestamp'] = pd.to_datetime(data['timestamp'],utc=True)

if 'year_month_day' not in data.columns:
    data['year_month_day'] = data['timestamp'].dt.to_period('D').astype(str)

data['tags_count'] = data['json_1'].apply(lambda x: len(json.loads(x)['tags']) if isinstance(x,str) else len(x['tags']))

data['year'] = data['timestamp'].dt.year
data['month'] = data['timestamp'].dt.month_name()
data['day_of_week'] = data['timestamp'].dt.day_name()
data['hour'] = data['timestamp'].dt.hour
data = data.dropna(subset=['timestamp'])
data['year']=data['year'].round(0).astype(int)
data['year']=data['year'].astype(str)



# health_data = pd.read_csv(r"C:\Users\actionfi\Desktop\Projects\Aakash\visualization for tag\device_management_healthdata.csv")


csv_path = os.path.join(os.path.dirname(__file__),"data","device_management_healthdata.csv")
health_data = pd.read_csv(csv_path)

health_data_cleaned = health_data.drop(['deleted_at','restored_at','created_at','updated_at','category_id','device_id_id','modified_by_id','modified_by_id','created_by_id','additional_data','transaction_id'],axis=1)
health_data_cleaned['timestamp'] = pd.to_datetime(health_data_cleaned['timestamp'],utc=True)
health_data_cleaned['year_month_day'] = health_data_cleaned['timestamp'].dt.to_period('D').astype(str)
health_data_cleaned['day_of_week'] = health_data_cleaned['timestamp'].dt.day_name()
health_data_cleaned['hour'] = health_data_cleaned['timestamp'].dt.hour
health_data_cleaned['year'] = health_data_cleaned['timestamp'].dt.year
health_data_cleaned['year']=health_data_cleaned['year'].round(0).astype(int)
health_data_cleaned['year']=health_data_cleaned['year'].astype(str)
health_data_cleaned['year'] = health_data_cleaned['timestamp'].dt.year
health_data_cleaned['month'] = health_data_cleaned['timestamp'].dt.month_name()
print("health data final:",health_data_cleaned)




app = dash.Dash(__name__)
app.title = "RFID Dashboard"


app.layout = html.Div(
    style={
        'display': 'flex',
        'height': '100vh',
        'fontFamily': 'Arial, sans-serif'
    },
    children=[
        # Sidebar
        html.Div(
            style={
                'width': '20%',
                'backgroundColor': '#f9f9f9',
                'padding': '20px',
                'boxShadow': '2px 0px 5px rgba(0,0,0,0.1)',
                'overflowY': 'auto'
            },
            children=[
                # html.H2("Filters"),
                html.Label("Select Data"),
                dcc.Dropdown(
                    id='data-picker',
                    options = [
                        {'label':'Tag data', 'value':'tag'},

                       {'label':'Health data', 'value':'health'} 
                    ],
                    placeholder="Select Data Type"
            
                ),
                html.Label("Select Date Range:"),
                dcc.DatePickerRange(
                    id='date-picker',
                    start_date=data['timestamp'].min().date(),
                    end_date=data['timestamp'].max().date(),
                    display_format='YYYY-MM-DD'
                ),
                html.Br(),
                html.Br(),
                html.H3("KPIs"),
                html.Div(id='kpi-output', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'})
            ]
        ),

        # Main content
        html.Div(
            style={
                'width': '80%',
                'padding': '20px',
                'overflowY': 'scroll'
            },
            children=[
                html.H1("RFID Device Dashboard", style={'textAlign': 'center'}),
                html.Div([
                    dcc.Graph(id='line-tags')],
                    style={
                        'marginBottom': '20px'
                    }),
                
                html.Div([
                    dcc.Graph(id='bar-tags-month'),
                    dcc.Graph(id='bar-tags-week'),                    
                ],
                style = {
                    'display': 'flex',
                    'gap':'20px'
                }),

                html.Div(
                    [
                        dcc.Graph(id='bar-tags-year',style={'flex':'1'}),
                        dcc.Graph(id='line-hour',style={'flex':'2'}),
                    ],
                    style = {
                        'display': 'flex',
                        'gap':'20px'
                        }
                )        
            ]
        )
    ]

)


# Callback
@app.callback(
    [
     
     Output('kpi-output', 'children'),
     Output('line-tags', 'figure'),
     Output('bar-tags-month','figure'),
     Output('bar-tags-week','figure'),
     Output('bar-tags-year','figure'),     
     Output('line-hour', 'figure'),
     ],
    [
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('data-picker','value')]
)



def update_dashboard( start_date, end_date,value):


    if value == 'tag':

        df = data.copy()
                       
        if start_date:
            df = df[df['timestamp'] >= pd.to_datetime(start_date).tz_localize('UTC')]
        
        if end_date:
            df = df[df['timestamp'] <= pd.to_datetime(end_date).tz_localize('UTC')]

        # KPIs
        total_tags = df['tags_count'].sum()
        total_sessions = df['int_1'].nunique()
        total_success = (df['char_1'] == 'success').sum()
        total_failures = (df['char_1'] != 'success').sum()
        total_rows = len(df)
        success_rate = (total_success / total_rows * 100) if total_rows else 0
        
        data_grouped= df.groupby('year_month_day',as_index=False)['tags_count'].sum()
        peak_day = data_grouped.loc[data_grouped['tags_count'].idxmax()]['year_month_day']
        weekday_name = pd.to_datetime(peak_day).day_name()
        peak_day =  f"{peak_day} {weekday_name} "
        
        data_grouped_hour = df.groupby('hour',as_index=False)['tags_count'].mean()

        peak_hour = data_grouped_hour.loc[data_grouped_hour['tags_count'].idxmax()]['hour']
        peak_hour = int(peak_hour)

        def format_hour(hour):
            if hour == 0:
                return '12 AM'
            elif 1 <= hour < 12:
                return f'{hour} AM'
            elif hour == 12:
                return '12 PM'
            else:
                return f'{hour - 12} PM'


        peak_hour = format_hour(peak_hour)
        print("peak_hour:",peak_hour)
        
        peak_day_peak_hour =  f"{peak_day} {peak_hour}"
    

        kpis = [
            html.Div([
                html.H4("Total Tags", style={'margin': '0'}), html.P(f"{total_tags}", style={'fontSize': '20px', 'fontWeight': 'bold'})
            ], style={'backgroundColor': '#f1f1f1', 'padding': '10px',  'textAlign': 'center'}),
            html.Div([
                html.H4("Sessions"), html.P(f"{total_sessions}")
            ], style={'backgroundColor': '#f1f1f1', 'padding': '10px',  'textAlign': 'center'}),
            html.Div([
                html.H4("Successes"), html.P(f"{total_success}")
            ], style={'backgroundColor': '#e0ffe0', 'padding': '10px',  'textAlign': 'center'}),
            html.Div([
                html.H4("Failures"), html.P(f"{total_failures}")
            ], style={'backgroundColor': '#ffe0e0', 'padding': '10px',  'textAlign': 'center'}),
            html.Div([
                html.H4("Success Rate (%)"), html.P(f"{success_rate:.2f}")
            ], style={'backgroundColor': '#f1f1f1', 'padding': '10px',  'textAlign': 'center'}),
            html.Div([
                html.H4("Peak Day Peak Hour"), html.P(f"{peak_day_peak_hour}")
            ], style={'backgroundColor':'#f1f1f1', 'padding': '10px',  'textAlign': 'center'}),
          
        ]


        # Line chart - Time series
        df_line = df.groupby('year_month_day',as_index=False)['tags_count'].sum()
        fig_line = px.line(df_line, x='year_month_day', y='tags_count', title='Daily Tag Reads', markers=True)

        df_year = df.groupby('year',as_index=False)['tags_count'].sum()
        fig_year = px.bar(df_year, x='year', y='tags_count', title='Year wise Tag Reads')

        month_order = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"]

        df_month = df.groupby('month',as_index=False)['tags_count'].mean()
        fig_month = px.bar(df_month, x='month', y='tags_count', title='Month wise average Tag Reads',category_orders={"month": month_order})

        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday","Friday","Saturday","Sunday"]
        df_week = df.groupby('day_of_week',as_index=False)['tags_count'].mean()
        fig_week = px.bar(df_week, x='day_of_week', y='tags_count', title='Week wise average Tag Reads',category_orders = {"day_of_week":week_order})

        df_hour = df.groupby('hour',as_index=False)['tags_count'].mean()
        fig_hour = px.line(df_hour, x='hour', y='tags_count', title='Hour wise Tag reads',markers =True)

        fig_line.update_layout(template='plotly_white')    
        fig_month.update_layout(template='plotly_white')
        fig_week.update_layout(template='plotly_white')
        fig_year.update_layout(template='plotly_white')
        fig_hour.update_layout(template='plotly_white')

        return  kpis, fig_line,  fig_month, fig_week, fig_year,fig_hour
    
    
    if value == 'health':

        df = health_data_cleaned.copy()
        
     
        if start_date:
            df = df[df['timestamp'] >= pd.to_datetime(start_date).tz_localize('UTC')]
        
        if end_date:
            df = df[df['timestamp'] <= pd.to_datetime(end_date).tz_localize('UTC')]
    
        def format_hour(hour):
            if hour == 0:
                return '12 AM'
            elif 1 <= hour < 12:
                return f'{hour} AM'
            elif hour == 12:
                return '12 PM'
            else:
                return f'{hour - 12} PM'

        # peak_temperature = max(health_data_cleaned['temperature'])
        # peak_day_temp = health_data_cleaned.loc[health_data_cleaned['temperature'].idxmax()]['year_month_day']
        # peak_hour_temp = health_data_cleaned.loc[health_data_cleaned['temperature'].idxmax()]['hour']
        # peak_hour_temp = int(peak_hour_temp)
        # peak_hour_temp = format_hour(peak_hour_temp)    
        # weekday_name = pd.to_datetime(peak_day_temp).day_name()
        # peak_day_temperature =  f"{peak_day_temp} {weekday_name} "
        # temperature_peak =  f" {peak_temperature } {peak_day_temperature} {peak_hour_temp} "






        # peak_cpu_usage = max(health_data_cleaned['cpu_usage'])
        # peak_day_cpu_usage = health_data_cleaned.loc[health_data_cleaned['cpu_usage'].idxmax()]['year_month_day']
        # peak_hour_cpu_usage = health_data_cleaned.loc[health_data_cleaned['cpu_usage'].idxmax()]['hour']
        # peak_hour_cpu_usage = int(peak_hour_cpu_usage)
        # peak_hour_cpu_usage = format_hour(peak_hour_cpu_usage)    
        # weekday_name = pd.to_datetime(peak_day_cpu_usage).day_name()
        # peak_day_cpu_usage =  f"{peak_day_cpu_usage} {weekday_name} "
        # cpu_usage_peak =  f" {peak_cpu_usage } {peak_day_cpu_usage} {peak_hour_cpu_usage} "



        # peak_memory_usage = max(health_data_cleaned['memory_usage'])
        # peak_day_memory_usage = health_data_cleaned.loc[health_data_cleaned['memory_usage'].idxmax()]['year_month_day']
        # peak_hour_memory_usage = health_data_cleaned.loc[health_data_cleaned['memory_usage'].idxmax()]['hour']
        # peak_hour_memory_usage = int(peak_hour_memory_usage)
        # peak_hour_memory_usage = format_hour(peak_hour_memory_usage)    
        # weekday_name = pd.to_datetime(peak_day_memory_usage).day_name()
        # peak_day_memory_usage =  f"{peak_day_memory_usage} {weekday_name} "
        # memory_usage_peak =  f" {peak_memory_usage } {peak_day_memory_usage} {peak_hour_memory_usage} "

      

        # peak_disk_usage = max(health_data_cleaned['disk_usage'])
        # peak_day_disk_usage = health_data_cleaned.loc[health_data_cleaned['disk_usage'].idxmax()]['year_month_day']
        # peak_hour_disk_usage = health_data_cleaned.loc[health_data_cleaned['disk_usage'].idxmax()]['hour']
        # peak_hour_disk_usage = int(peak_hour_disk_usage)
        # peak_hour_disk_usage = format_hour(peak_hour_disk_usage)    
        # weekday_name = pd.to_datetime(peak_day_disk_usage).day_name()
        # peak_day_disk_usage =  f"{peak_day_disk_usage} {weekday_name} "
        # disk_usage_peak =  f" {peak_disk_usage } {peak_day_disk_usage} {peak_hour_disk_usage} "




        # peak_module_temperature = max(health_data_cleaned['module_temperature'])
        # peak_day_module_temperature = health_data_cleaned.loc[health_data_cleaned['module_temperature'].idxmax()]['year_month_day']
        # peak_hour_module_temperature = health_data_cleaned.loc[health_data_cleaned['module_temperature'].idxmax()]['hour']
        # peak_hour_module_temperature = int(peak_hour_module_temperature)
        # peak_hour_module_temperature = format_hour(peak_hour_module_temperature)    
        # weekday_name = pd.to_datetime(peak_day_module_temperature).day_name()
        # peak_day_module_temperature =  f"{peak_day_module_temperature} {weekday_name} "
        # module_temperature_peak =  f" {peak_module_temperature } {peak_day_module_temperature} {peak_hour_module_temperature} "






        # peak_temperature = health_data_cleaned['temperature'].max()
        # peak_rows = health_data_cleaned[health_data_cleaned['temperature'] == peak_temperature]
        # peak_info = peak_rows[['year_month_day', 'hour']]
        # peak_info_unique = peak_info.drop_duplicates()
        # peak_info_unique['weekday'] = pd.to_datetime(peak_info_unique['year_month_day']).dt.day_name()
        # peak_info_unique['hour_formatted'] = peak_info_unique['hour'].apply(format_hour)
        # temperature_peak_list = []
        # for _, row in peak_info_unique.iterrows():
        #     entry = f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}"
        #     temperature_peak_list.append(entry)
        # temperature_peak_list.insert(0, f"Peak Temperature: {peak_temperature}")


        # peak_module_temperature = health_data_cleaned['module_temperature'].max()
        # peak_rows = health_data_cleaned[health_data_cleaned['module_temperature'] == peak_module_temperature]
        # peak_info = peak_rows[['year_month_day', 'hour']]
        # peak_info_unique = peak_info.drop_duplicates()
        # peak_info_unique['weekday'] = pd.to_datetime(peak_info_unique['year_month_day']).dt.day_name()
        # peak_info_unique['hour_formatted'] = peak_info_unique['hour'].apply(format_hour)
        # module_temperature_peak_list = []
        # for _, row in peak_info_unique.iterrows():
        #     entry = f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}"
        #     module_temperature_peak_list.append(entry)
        # module_temperature_peak_list.insert(0, f"Peak Module Temperature: {peak_module_temperature}")
        
        
        # peak_cpu_usage = health_data_cleaned['cpu_usage'].max()
        # peak_rows = health_data_cleaned[health_data_cleaned['cpu_usage'] == peak_cpu_usage]
        # peak_info = peak_rows[['year_month_day', 'hour']]
        # peak_info_unique = peak_info.drop_duplicates()
        # peak_info_unique['weekday'] = pd.to_datetime(peak_info_unique['year_month_day']).dt.day_name()
        # peak_info_unique['hour_formatted'] = peak_info_unique['hour'].apply(format_hour)
        # cpu_usage_peak_list = []
        # for _, row in peak_info_unique.iterrows():
        #     entry = f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}"
        #     cpu_usage_peak_list.append(entry)        
        # cpu_usage_peak_list.insert(0, f"Peak CPU Usage: {peak_cpu_usage}")
        

        # peak_memory_usage = health_data_cleaned['memory_usage'].max()
        # peak_rows = health_data_cleaned[health_data_cleaned['memory_usage'] == peak_memory_usage]
        # peak_info = peak_rows[['year_month_day', 'hour']]
        # peak_info_unique = peak_info.drop_duplicates()
        # peak_info_unique['weekday'] = pd.to_datetime(peak_info_unique['year_month_day']).dt.day_name()
        # peak_info_unique['hour_formatted'] = peak_info_unique['hour'].apply(format_hour)
        # memory_usage_peak_list = []
        # for _, row in peak_info_unique.iterrows():
        #     entry = f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}"
        #     memory_usage_peak_list.append(entry)  
        # memory_usage_peak_list.insert(0, f"Peak Memory Usage: {peak_memory_usage}")

        # peak_disk_usage = health_data_cleaned['disk_usage'].max()
        # peak_rows = health_data_cleaned[health_data_cleaned['disk_usage'] == peak_disk_usage]
        # peak_info = peak_rows[['year_month_day', 'hour']]
        # peak_info_unique = peak_info.drop_duplicates()
        # peak_info_unique['weekday'] = pd.to_datetime(peak_info_unique['year_month_day']).dt.day_name()
        # peak_info_unique['hour_formatted'] = peak_info_unique['hour'].apply(format_hour)
        # disk_usage_peak_list = []
        # for _, row in peak_info_unique.iterrows():
        #     entry = f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}"
        #     disk_usage_peak_list.append(entry)         
        # disk_usage_peak_list.insert(0, f"Peak disk Usage: {peak_disk_usage}")

        def get_peak_info(df, column):
            peak_value = df[column].max()
            peak_rows = df[df[column] == peak_value]
            peak_info = peak_rows[['year_month_day', 'hour']].drop_duplicates()
            peak_info['weekday'] = pd.to_datetime(peak_info['year_month_day']).dt.day_name()
            peak_info['hour_formatted'] = peak_info['hour'].apply(format_hour)
            lst = [f"Peak {column.capitalize().replace('_', ' ')}: {peak_value}"]
            for _, row in peak_info.iterrows():
                lst.append(f"Day: {row['year_month_day']} ({row['weekday']}), Hour: {row['hour_formatted']}")
            return lst



        # Use helper
        temperature_peak_list = get_peak_info(df, 'temperature')
        module_temperature_peak_list = get_peak_info(df, 'module_temperature')
        cpu_usage_peak_list = get_peak_info(df, 'cpu_usage')
        memory_usage_peak_list = get_peak_info(df, 'memory_usage')
        disk_usage_peak_list = get_peak_info(df, 'disk_usage')

        all_lists = [temperature_peak_list, module_temperature_peak_list, cpu_usage_peak_list,memory_usage_peak_list,disk_usage_peak_list]

        def extract_day_hour(lst):
            pairs = []
            for item in lst:
                match = re.search(r'Day:\s*([\d-]+).*?, Hour:\s*(.*)', item)
                if match:
                    day = match.group(1)
                    hour = match.group(2)
                    pairs.append( (day, hour) )
            return pairs

        sets_of_pairs = [ set(extract_day_hour(lst)) for lst in all_lists ]

        common = set.intersection(*sets_of_pairs)

       
        if len(common) == 1:
            final_day, final_hour = list(common)[0]
        elif len(common) > 1:
            # Sort by latest datetime
            common_dt = [ (datetime.datetime.strptime(day, "%Y-%m-%d"), hour) for (day, hour) in common ]
            latest_dt = max(common_dt, key=lambda x: x[0])
            final_day = latest_dt[0].strftime("%Y-%m-%d")
            final_hour = latest_dt[1]
        else:
            # Fallback: take latest from all
            all_dt = [ (datetime.datetime.strptime(day, "%Y-%m-%d"), hour) for pairs in sets_of_pairs for (day, hour) in pairs ]
            latest_dt = max(all_dt, key=lambda x: x[0])
            final_day = latest_dt[0].strftime("%Y-%m-%d")
            final_hour = latest_dt[1]

        try:
            final_hour = int(final_hour)
        except ValueError:
            final_hour = 0
        # Format the hour
        final_hour_label = format_hour(final_hour)


        kpis = [
        html.Div([html.H4("Peak Temperature"), html.P(f"{df['temperature'].max()}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
        html.Div([html.H4("Peak CPU Usage (%)"), html.P(f"{df['cpu_usage'].max()}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
        html.Div([html.H4("Peak Memory Usage"), html.P(f"{df['memory_usage'].max()}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
        html.Div([html.H4("Peak Disk Usage (%)"), html.P(f"{df['disk_usage'].max()}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
        html.Div([html.H4("Peak Module Temperature"), html.P(f"{df['module_temperature'].max()}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
        html.Div([html.H4("Peak Day"), html.P(f"{final_day} {final_hour_label}")], style={'backgroundColor': '#f1f1f1', 'padding': '10px', 'textAlign': 'center'}),
    ]

        df_hour = df.groupby('hour').agg({
            'cpu_usage': 'mean',
            'memory_usage': 'mean',
            'disk_usage': 'mean',
            'temperature': 'mean',
            'module_temperature': 'mean'
        }).reset_index()


        df_week = df.groupby('day_of_week').agg({
            'cpu_usage': 'mean',
            'memory_usage': 'mean',
            'disk_usage': 'mean',
            'temperature': 'mean',
            'module_temperature': 'mean'
        }).reset_index()

        df_line = df.groupby('year_month_day').agg({
            'cpu_usage': 'mean',
            'memory_usage': 'mean',
            'disk_usage': 'mean',
            'temperature': 'mean',
            'module_temperature': 'mean'
        }).reset_index()

        df_year = df.groupby('year').agg({
            'cpu_usage': 'mean',
            'memory_usage': 'mean',
            'disk_usage': 'mean',
            'temperature': 'mean',
            'module_temperature': 'mean'
        }).reset_index()


        df_month = df.groupby('month').agg({
            'cpu_usage': 'mean',
            'memory_usage': 'mean',
            'disk_usage': 'mean',
            'temperature': 'mean',
            'module_temperature': 'mean'
        }).reset_index()

        # Line chart - Time series
        # df_line = df.groupby('year_month_day',as_index=False)['cpu_usage'].mean()
        fig_line = px.line(df_line, x='year_month_day', y=['cpu_usage', 'memory_usage', 'disk_usage', 'temperature', 'module_temperature'], title='Daily Health data', markers=True)

        # df_year = df.groupby('year',as_index=False)['cpu_usage'].mean()
        fig_year = px.bar(df_year, x='year', y=['cpu_usage', 'memory_usage', 'disk_usage', 'temperature', 'module_temperature'], title='Year wise Health Data',barmode='group')

        month_order = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"]

        # df_month = df.groupby('month',as_index=False)['cpu_usage'].mean()
        fig_month = px.bar(df_month, x='month', y=['cpu_usage', 'memory_usage', 'disk_usage', 'temperature', 'module_temperature'],barmode='group', title='Month wise average Health Data',category_orders={"month": month_order})

        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday","Friday","Saturday","Sunday"]
        # df_week = df.groupby('day_of_week',as_index=False)['cpu_usage'].mean()
        fig_week = px.bar(df_week, x='day_of_week', y=['cpu_usage', 'memory_usage', 'disk_usage', 'temperature', 'module_temperature'], barmode='group',title='Week wise average Health Data',category_orders = {"day_of_week":week_order})

        # df_hour = df.groupby('hour',as_index=False)['cpu_usage'].mean()
        # fig_hour = px.line(df_hour, x='hour', y='cpu_usage', title='Hour wise Health Data',markers =True)


        fig_hour = px.line(df_hour, x='hour', y=['cpu_usage', 'memory_usage', 'disk_usage', 'temperature', 'module_temperature'],
                   title='Hourly Usage Overview', markers=True)
        
        
        fig_line.update_layout(
            template='plotly_white',
            legend_title_text='Metric',
            yaxis_title='Usage / Temperature')   
        
        fig_week.update_layout(template='plotly_white', legend_title_text='Metric',
            yaxis_title='Usage / Temperature')
        
        fig_month.update_layout(template='plotly_white', legend_title_text='Metric',
            yaxis_title='Usage / Temperature')        
        
        fig_year.update_layout(template='plotly_white', legend_title_text='Metric',
            yaxis_title='Usage / Temperature')
        
        fig_hour.update_layout(
            template='plotly_white',
            legend_title_text='Metric',
            yaxis_title='Usage / Temperature')

        return  kpis, fig_line,  fig_month, fig_week, fig_year,fig_hour


    # Fallback return
    empty_fig = go.Figure()
    empty_fig.update_layout(template='plotly_white', title='No Data Selected')

    return [], empty_fig, empty_fig, empty_fig, empty_fig, empty_fig
# # Run
# if __name__ == '__main__':
#     app.run(debug=True)



# server
if __name__ == '__main__':
    port = int(os.environ.get("PORT",8050))
    app.run(host = "0.0.0.0",port=port,debug=True)

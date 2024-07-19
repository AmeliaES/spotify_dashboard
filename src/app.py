from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.io as plt_io
import pandas as pd
from dotenv import load_dotenv
import os

app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN],
            meta_tags=[{'name': 'viewport',
                        'content': 'width=device-width, initial-scale=1.0'}])

app.title = 'Spotify Analysis'
app._favicon = ('images/favicon.ico')
server = app.server

# ------------------------------------
# Load environment variables from .env
load_dotenv()

# Get the CSV file path from environment variable, with a default fallback
data_path = os.getenv('DATA_PATH')

# Load in data
data = pd.read_csv(data_path)

# Convert date time column into two separate columns "date" and "time"
data['ts'] = pd.to_datetime(data['ts'])

# Create separate 'date' and 'time' columns
data['date'] = data['ts'].dt.date

# Get a numeric value for the slider
# Get the min and max dates
min_date = data['date'].min()
max_date = data['date'].max()

date_range_df = pd.DataFrame({
    'date': pd.date_range(start=min_date, end=max_date, freq='ME'),
    'index': range(1, len(pd.date_range(start=min_date, end=max_date, freq='ME')) + 1)
})

date_range_df['month-year'] = date_range_df['date'].dt.strftime('%b %Y')

date_range_dictionary = dict(zip(date_range_df['index'], date_range_df['month-year']))

date_range_dictionary_slider = {}

# Iterate through the items of the existing dictionary
keys = list(date_range_dictionary.keys())
values = list(date_range_dictionary.values())

for i, key in enumerate(keys):
    if i == 0 or i == len(keys) - 1 or (i + 1) % 3 == 0:  # First, last, and every 3rd value
        date_range_dictionary_slider[key] = values[i]
    else:
        date_range_dictionary_slider[key] = ''

# Use "date_range_dictionary_slider" in the  dcc.RangeSlider

# add a column to our data frame called month_year
data['year-month'] = data['ts'].dt.strftime('%Y-%m')

# find a way to get our date value:
# from a number that is the key in the dictionary
# extract the year-month assigned to that key in the dictionary
# turn that into a date (last day of that year-month)
# and that date should be in the format of eg. pd.to_datetime('2022-06-01').date()

def get_date_from_slider_value_start(slider_value):
    year_month = date_range_dictionary.get(slider_value)
    if year_month:
        # Get the last day of the month
        end_of_month = pd.to_datetime(year_month) + pd.offsets.MonthBegin(0)
        return end_of_month.date()  # Return date object
    else:
        return None  # Handle case where slider_value doesn't exist in dictionary

def get_date_from_slider_value_end(slider_value):
    year_month = date_range_dictionary.get(slider_value)
    if year_month:
        # Get the last day of the month
        end_of_month = pd.to_datetime(year_month) + pd.offsets.MonthEnd(0)
        return end_of_month.date()  # Return date object
    else:
        return None  # Handle case where slider_value doesn't exist in dictionary

# ------------------------------------
# Create custom theme for plots

plt_io.templates["custom"] = plt_io.templates["ggplot2"]

# plt_io.templates["custom"]['layout']['paper_bgcolor'] = '#b2b1ad'
plt_io.templates["custom"]['layout']['plot_bgcolor'] = '#f0f0ef'

plt_io.templates['custom']['layout']['yaxis']['gridcolor'] = '#ffffff'
plt_io.templates['custom']['layout']['xaxis']['gridcolor'] = '#ffffff'

plt_io.templates['custom']['layout']['colorway'] = ['#56B4E9','#E69F00',  '#CC79A7', '#92d134', '#F0E442', '#0072B2', '#D55E00']

plt_io.templates['custom']['layout']['font']['size'] = 16
plt_io.templates['custom']['layout']['xaxis']['tickfont']['size'] = 13
plt_io.templates['custom']['layout']['yaxis']['tickfont']['size'] = 13

plt_io.templates['custom']['layout']['margin']['l'] = 20
plt_io.templates['custom']['layout']['margin']['b'] = 20
plt_io.templates['custom']['layout']['margin']['t'] = 20
plt_io.templates['custom']['layout']['margin']['r'] = 20
plt_io.templates['custom']['layout']['margin']['pad'] = 3

# ------------------------------------
# Histogram plot
df_hist = (data
    .groupby('year-month')
    .size()
    .reset_index(name = 'count')
    .sort_values(by='year-month'))

df_hist['month-year'] = pd.to_datetime(df_hist['year-month']).dt.strftime('%b %Y')


fig_histogram = px.bar(df_hist, 
            x='month-year', 
            y='count', 
            labels={'month-year': 'Month', 'count': 'Number of songs'},
            template = 'custom')

# Plot of top 20 artists listened to (based on streaming hours)
df_summary = (data
    .groupby('master_metadata_album_artist_name')
    ['ms_played'].sum() 
    .reset_index(name='total')
    .sort_values(by='total', ascending=False)
    .head(20)
    .sort_values(by='total'))

df_summary['hours'] = round(df_summary['total']/(1000*60*60), 2)

fig_top_artists = px.bar(df_summary, 
             y='master_metadata_album_artist_name', 
             x='hours', 
             labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours streamed'},
             template = 'custom')

# ------------------------------------
dateRangeText = ""

# ------------------------------------
# CALLBACKS
# ------------------------------------
# Callback to update plots based on date range slider
@app.callback(
    Output('fig_histogram', 'figure'),
    Output('fig_top_artists', 'figure'),
    Output('dateRangeText', 'children'),
    Input('date-slider', 'value')
)
def update_plots(selected_dates):
    start_date_num = selected_dates[0]
    end_date_num = selected_dates[1]

    start_date = get_date_from_slider_value_start(start_date_num)
    end_date = get_date_from_slider_value_end(end_date_num)
    
    # Update histogram plot
    df_hist = (data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    .groupby('year-month')
    .size()
    .reset_index(name = 'count')
    .sort_values(by='year-month'))

    df_hist['month-year'] = pd.to_datetime(df_hist['year-month']).dt.strftime('%b %Y')

    filtered_histogram = px.bar(df_hist, 
                x='month-year', 
                y='count', 
                labels={'month-year': 'Month', 'count': 'Number of songs'},
                template = 'custom')

    filtered_histogram.update_xaxes(tickangle=45)

    filtered_histogram.update_xaxes(tickmode='array', tickvals=df_hist['month-year'],
                    ticktext=df_hist['month-year'])

    # Update top artists plot
    filtered_summary = (data[(data['date'] >= start_date) & (data['date'] <= end_date)]
                        .groupby('master_metadata_album_artist_name')['ms_played'].sum()
                        .reset_index(name='total')
                        .sort_values(by='total', ascending=False)
                        .head(20)
                        .sort_values(by='total'))
    
    filtered_summary['hours'] = round(filtered_summary['total'] / (1000 * 60 * 60), 2)
    
    filtered_top_artists = px.bar(filtered_summary, 
                                  y='master_metadata_album_artist_name', 
                                  x='hours', 
                                  labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Streamed'},
                                  template = 'custom')
    
    filtered_top_artists.update_layout(margin=dict(b=112))

    # Explicitly label every tick on the y-axis
    filtered_top_artists.update_yaxes(tickmode='array', tickvals=filtered_summary['master_metadata_album_artist_name'],
                    ticktext=filtered_summary['master_metadata_album_artist_name'])

    
    # Create text for date range
    start_date_month_year = start_date.strftime('%b %Y')

    end_date_month_year = end_date.strftime('%b %Y')

    dateRangeText_update = f"{start_date_month_year} - {end_date_month_year}"
    
    return filtered_histogram, filtered_top_artists, dateRangeText_update


# ------------------------------------
# LAYOUT
# ------------------------------------
# Define app layout

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H1("Spotify Streaming History"),
        ], 
        className = "text-center pt-3 ms-2 me-2 bg-primary bg-opacity-10",
        width = 12)
    ]),

    dbc.Row(
        dbc.Col([
            html.H5(["Analysis of my personal Spotify data.",html.Br(),"Please move the sliders to different months to explore different date ranges."])
        ], 
        className = "text-center pb-3 ms-2 me-2 bg-primary bg-opacity-10",
        width = 12)
    ),


    dbc.Row([

        dbc.Col([
            dcc.RangeSlider(
                id='date-slider',
                marks={k: {'label': v, 'style': {'transform': 'rotate(45deg)', 'white-space': 'nowrap', 'margin-top': '10px', 'font-size' : '20px'}} for k, v in date_range_dictionary_slider.items()},
                step=None,
                min=min(date_range_dictionary_slider.keys()),
                max=max(date_range_dictionary_slider.keys()),
                value=[min(date_range_dictionary_slider.keys()), max(date_range_dictionary_slider.keys())],
                allowCross = False 
            )
        ], className = 'mb-5')

    ], className = 'mt-3 me-5 ms-5'),

    dbc.Row([

        dbc.Col([
            html.H4(id = 'dateRangeText')
        ], className = 'text-center p-3 fw-bold text-primary border-bottom',width = 12)

    ]),

    dbc.Row([

        dbc.Col([

            html.H5(["Number of songs streamed each month"], className = 'text-center'),
            dcc.Graph(id='fig_histogram', figure=fig_histogram)

        ], xs=12, sm=12, md=12, lg=6, xl=6
        ),

        dbc.Col([

            html.H5(["Top 20 artists"], className = 'text-center'),
            dcc.Graph(id='fig_top_artists', figure=fig_top_artists)

        ], xs=12, sm=12, md=12, lg=6, xl=6)

    ], className = 'me-5 ms-5 mb-1 mt-2'),

    dbc.Row([

        dbc.Col([

            dbc.Button(['About me'], 
            href = "https://ameliaes.github.io/"
            , className="me-md-2"),

            dbc.Button(['My GitHub'], 
            href = "https:www.github.com/ameliaes")

        ]),
    ], className = 'gap-2 d-flex justify-content-end')

], fluid=True)

# ------------------------------------
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


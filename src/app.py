from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import simplejson as json

app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN],
            meta_tags=[{'name': 'viewport',
                        'content': 'width=device-width, initial-scale=1.0'}])

app.title = 'Spotify Analysis'
app._favicon = ('images/favicon.ico')
server = app.server

# ------------------------------------
# Load in data
# data = pd.read_csv('extended_streaming_Sept2020-Nov2023.csv')
data = pd.read_csv('src/extended_streaming_Sept2020-Nov2023.csv')

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
            title="Total number of songs played each month",
            labels={'month-year': 'Month', 'count': 'Number of songs'})

fig_histogram.update_xaxes(tickangle=45)

fig_histogram.update_xaxes(tickmode='array', tickvals=df_hist['month-year'],
                 ticktext=df_hist['month-year'])

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
             title=f"Top 20 Artists",
             labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Played'})


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
                title="Total number of songs played each month",
                labels={'month-year': 'Month', 'count': 'Number of songs'})

    filtered_histogram.update_xaxes(tickangle=45)

    filtered_histogram.update_xaxes(tickmode='array', tickvals=df_hist['month-year'],
                    ticktext=df_hist['month-year'])

    filtered_histogram.update_layout(margin=dict(l=30, r=30, t=60, b=30))

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
                                  title=f"Top 20 Artists",
                                  labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Played'})
    
    filtered_top_artists.update_layout(margin=dict(l=30, r=30, t=10, b=60))

    # Customize layout and style
    filtered_top_artists.update_layout(
        # Add title and adjust margins
        margin=dict(l=100, r=20, t=50, b=20),  # Adjust margins as needed
   )

    # Explicitly label every tick on the y-axis
    filtered_top_artists.update_yaxes(tickmode='array', tickvals=filtered_summary['master_metadata_album_artist_name'],
                    ticktext=filtered_summary['master_metadata_album_artist_name'])

    
    # Create text for date range
    start_date_month_year = start_date.strftime('%b %Y')

    end_date_month_year = end_date.strftime('%b %Y')

    dateRangeText_update = f"Showing data selected between {start_date_month_year} and {end_date_month_year}"
    
    return filtered_histogram, filtered_top_artists, dateRangeText_update

# ------------------------------------
# LAYOUT
# ------------------------------------
# Define app layout

app.layout = dbc.Container([

    dbc.Row(
        dbc.Col([
            html.H1("Spotify Streaming History"),
            html.H5(["Analysis of my personal Spotify data from Sept 2020 to Oct 2023.",html.Br(),"Please move the sliders to different months to explore different date ranges."])
        ], 
        className = "text-center p-3 ms-2 me-2 bg-primary bg-opacity-10",
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

    ], className = 'mt-5 me-5 ms-5 mb-3'),

    dbc.Row([

        dbc.Col([
            html.H4(id = 'dateRangeText')
        ], className = 'text-center p-3 fw-bold text-primary')

    ]),

    dbc.Row([

        dbc.Col([

            dcc.Graph(id='fig_histogram', figure=fig_histogram)

        ], xs=12, sm=12, md=12, lg=6, xl=6
        ),

        dbc.Col([

            dcc.Graph(id='fig_top_artists', figure=fig_top_artists)

        ], xs=12, sm=12, md=12, lg=6, xl=6)

    ], className = 'mt-3 me-5 ms-5 mb-5')

], fluid=True)

# ------------------------------------
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


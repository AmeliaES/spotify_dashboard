# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import simplejson as json

app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Load in data
data = pd.read_csv('data/extended_streaming_Sept2020-Nov2023.csv')

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

date_range_df['year-month'] = date_range_df['date'].dt.strftime('%Y-%m')

date_range_dictionary = dict(zip(date_range_df['index'], date_range_df['year-month']))

# Use "date_range_dictionary" in the  dcc.RangeSlider

# add a column to our data frame called month_year
data['year-month'] = data['ts'].dt.strftime('%Y-%m')

# find a way to get our date value:
# from a number that is the key in the dictionary
# extract the year-month assigned to that key in the dictionary
# turn that into a date (last day of that year-month)
# and that date should be in the format of eg. pd.to_datetime('2022-06-01').date()

def get_date_from_slider_value(slider_value):
    year_month = date_range_dictionary.get(slider_value)
    if year_month:
        # Get the last day of the month
        end_of_month = pd.to_datetime(year_month) + pd.offsets.MonthBegin(0)
        return end_of_month.date()  # Return date object
    else:
        return None  # Handle case where slider_value doesn't exist in dictionary


# Histogram plot
fig_histogram = px.histogram(data, 
                    x='date', 
                    title='Number of Songs Played Over Time')

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
             title=f"Top 20 Artists (between Sept 2020 and Nov 2023)",
             labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Played'})


# Callback to update plots based on date range slider
@app.callback(
    Output('fig_histogram', 'figure'),
    Output('fig_top_artists', 'figure'),
    Input('date-slider', 'value')
)
def update_plots(selected_dates):
    start_date_num = selected_dates[0]
    end_date_num = selected_dates[1]

    start_date = get_date_from_slider_value(start_date_num)
    end_date = get_date_from_slider_value(end_date_num)
    
    # Update histogram plot
    filtered_histogram = px.histogram(data[(data['date'] >= start_date) & (data['date'] <= end_date)], 
                                      x='date', 
                                      title='Number of Songs Played Over Time')
    
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
                                  title=f"Top 20 Artists (between {start_date} and {end_date})",
                                  labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Played'})

    # Customize layout and style
    filtered_top_artists.update_layout(
        # Add title and adjust margins
        margin=dict(l=100, r=20, t=50, b=20),  # Adjust margins as needed
   )

    # Explicitly label every tick on the y-axis
    filtered_top_artists.update_yaxes(tickmode='array', tickvals=filtered_summary['master_metadata_album_artist_name'],
                    ticktext=filtered_summary['master_metadata_album_artist_name'])
    
    return filtered_histogram, filtered_top_artists

# Define app layout
app.layout = html.Div([
    html.Div(["Spotify Streaming History"], className = "h1 text-center mt-5 mb-3"),
    html.Div(["Analysis of my personal Spotify data from Sept 2020 to October 2023."], className = "h6 text-center mb-3"),
    html.Div([
        dcc.RangeSlider(
        id='date-slider',
        marks={k: {'label': v, 'style': {'transform': 'rotate(45deg)', 'white-space': 'nowrap', 'margin-top': '10px'}} for k, v in date_range_dictionary.items()},
        step=None,
        min=min(date_range_dictionary.keys()),
        max=max(date_range_dictionary.keys()),
        value=[min(date_range_dictionary.keys()), max(date_range_dictionary.keys())],
        allowCross = False
        )
    ], style={'width': '90%','padding-left':'5%'},
    className = 'm-5'),
    html.Div([
    html.Div([dcc.Graph(id='fig_histogram', figure=fig_histogram)], className = "ms-5 me-3 border w-50 inline-block"),
    html.Div([dcc.Graph(id='fig_top_artists', figure=fig_top_artists)], className = "ms-3 me-5 border w-50 inline-block")
    ], className="d-flex justify-content-center")
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


# This script creates the data used in src/app.py

import pandas as pd
import simplejson as json
import glob
import plotly.express as px

# List to hold data from all files
data_list = []

# Use glob to find all JSON files in the specified directory
for filename in glob.glob('data/Streaming_History_Audio_*.json'):
    with open(filename, 'r') as f:
        data = json.load(f)
        data_list.append(pd.json_normalize(data))

# Concatenate all dataframes in the list into a single dataframe
data = pd.concat(data_list, ignore_index=True)

# Display the first few rows of the dataframe
data.head()

# Convert date time column into two separate columns "date" and "time"
data['ts'] = pd.to_datetime(data['ts'])

# Create separate 'date' and 'time' columns
data['date'] = data['ts'].dt.date
data['time'] = data['ts'].dt.time

# Plot distribution of number of songs played over time
fig = px.histogram(data, 
                    x='date', 
                    title='Number of Songs Played Over Time',
                    marginal = 'violin')

fig

# Zooming in on the figure it looks like data from August 2020 is when Spotify use increased.
# Let's filter the data to keep anything after August 2020 

data = data.loc[(data['date'] >= pd.to_datetime('2020-09-01').date()) & (data['date'] < pd.to_datetime('2023-11-01').date())]

fig = px.histogram(data, 
                    x='date', 
                    title='Number of Songs Played Over Time',
                    marginal = 'violin')

fig

# ----------------------------------
# Save our new data frame as a csv

# Subset to only columns we need and remove potentially personally sensitive data (eg. IP address, type of browser etc.)
data = data[['date', 
'ts', 
'ms_played', 
'master_metadata_track_name', 
'master_metadata_album_artist_name',
'spotify_track_uri']]

data.to_csv('src/extended_streaming_Sept2020-Nov2023.csv', index = False)

# ----------------------------------
# Create the histogram with conditional coloring
date_range_start = pd.to_datetime('2021-05-01').date()
date_range_end = pd.to_datetime('2021-08-01').date()

# Create a new column 'color' based on date range
data['color'] = data['date'].apply(lambda x: 'Within Date Range' if date_range_start <= x <= date_range_end else 'Outside Date Range')

# Calculate number of weeks in the date range
num_weeks = (data['date'].max() - data['date'].min()).days // 7

# Create the histogram with conditional coloring
fig = px.histogram(data, 
                   x='date', 
                   title='Number of Songs Played Over Time',
                   marginal='violin',
                   color='color',  # Use the 'color' column for coloring
                   color_discrete_map={'Within Date Range': 'red', 'Outside Date Range': 'blue'},
                   nbins = num_weeks)

# Customize x-axis to show dates properly
fig.update_layout(xaxis_title='Date',
                  xaxis=dict(
                      tickformat='%Y-%m',  # Format ticks to show full date
                      ticklabelmode='period'))  # Show tick labels as month periods


# Come back to making the bins one week in size... not quite there yet I dont think.

# Instead just change the x-axis limits to only show data between those two dates
date_range_start = pd.to_datetime('2021-05-01').date()
date_range_end = pd.to_datetime('2023-06-01').date()

fig = px.histogram(data, 
                    x='date', 
                    title='Number of Songs Played Over Time')

fig

fig.update_xaxes(range=[date_range_start, date_range_end])

# This has a similar function, and will be good enough to show on the Dash application for now.

# ----------------------------------
# Ok, moving on. Let's make the main plots we want to show on our Dash app.
# Or at least make one of them then get started with showing it on Dash.
# Top artists. Let's make a plot of top 20 artists (of our data subsetted to that same date range above)

# Perform operations similar to dplyr in R
df_summary = (data[(data['date'] >= date_range_start) & (data['date'] <= date_range_end)]
    .groupby('master_metadata_album_artist_name')
    .size()  # Equivalent to n() in dplyr
    .reset_index(name='count')
    .sort_values(by='count', ascending=False)
    .head(20)
    .sort_values(by='count')
)

# Plot using Plotly Express
fig = px.bar(df_summary, 
             y='master_metadata_album_artist_name', 
             x='count', 
             title=f"Top 20 Artists (between {date_range_start} and {date_range_end})",
             labels={'master_metadata_album_artist_name': 'Artist', 'count': 'Count'})
fig
# Customize layout and style
fig.update_layout(
    # Add title and adjust margins
    margin=dict(l=100, r=20, t=50, b=20),  # Adjust margins as needed

    # Apply a built-in Plotly theme (optional)
    template='ggplot2'  # Available options: 'plotly', 'plotly_dark', 'ggplot2', 'seaborn', etc.
)

# Explicitly label every tick on the y-axis
fig.update_yaxes(tickmode='array', tickvals=df_summary['master_metadata_album_artist_name'],
                 ticktext=df_summary['master_metadata_album_artist_name'])


fig

# ----------------------------------
# Now create a plot showing the streaming time of each artist

df_summary = (data[(data['date'] >= date_range_start) & (data['date'] <= date_range_end)]
    .groupby('master_metadata_album_artist_name')
    ['ms_played'].sum() 
    .reset_index(name='total')
    .sort_values(by='total', ascending=False)
    .head(20)
    .sort_values(by='total'))

df_summary['hours'] = round(df_summary['total']/(1000*60*60), 2)

fig = px.bar(df_summary, 
             y='master_metadata_album_artist_name', 
             x='hours', 
             title=f"Top 20 Artists (between {date_range_start} and {date_range_end})",
             labels={'master_metadata_album_artist_name': 'Artist', 'hours': 'Hours Played'})
fig

# Customize layout and style
fig.update_layout(
    # Add title and adjust margins
    margin=dict(l=100, r=20, t=50, b=20),  # Adjust margins as needed

    # Apply a built-in Plotly theme (optional)
    template='ggplot2'  # Available options: 'plotly', 'plotly_dark', 'ggplot2', 'seaborn', etc.
)

# Explicitly label every tick on the y-axis
fig.update_yaxes(tickmode='array', tickvals=df_summary['master_metadata_album_artist_name'],
                 ticktext=df_summary['master_metadata_album_artist_name'])

# ----------------------------------
# Because the date slider can only have numeric values we have to manipulate the date column further
# We want a slider where each month is a mark
# First create a dictionary where each month has a unique number assigned to it (in sequence)
# Second, add a column to our data frame for month and year
# Third find a way to get our date value going from numeric value, to month_year to date.


# Get the min and max dates
min_date = data['date'].min()
max_date = data['date'].max()

date_range_df = pd.DataFrame({
    'date': pd.date_range(start=min_date, end=max_date, freq='ME'),
    'index': range(1, len(pd.date_range(start=min_date, end=max_date, freq='ME')) + 1)
})

date_range_df['year-month'] = date_range_df['date'].dt.strftime('%Y-%m')

date_range_dictionary = dict(zip(date_range_df['index'], date_range_df['year-month']))

date_range_dictionary

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

get_date_from_slider_value_start(1)
get_date_from_slider_value_end(1)
# date_range_start = get_date_from_slider_value(start_date)
# date_range_end = get_date_from_slider_value(end_date)

# ----------------------------------
# Let's also update the histogram to do a count based on the year-month 
df_hist = (data[(data['date'] >= date_range_start) & (data['date'] <= date_range_end)]
    .groupby('year-month')
    .size()
    .reset_index(name = 'count')
    .sort_values(by='year-month'))

df_hist

fig = px.bar(df_hist, 
            x='year-month', 
            y='count', 
            title="Total number of songs played each month",
            labels={'year-month': 'Month', 'count': 'Number of songs'})

fig

fig.update_xaxes(tickangle=45)

fig.update_xaxes(tickmode='array', tickvals=df_hist['year-month'],
                 ticktext=df_hist['year-month'])

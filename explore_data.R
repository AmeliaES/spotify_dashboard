# Explore my personal Spotify data (streaming history)
# downloaded "Extended streaming history" from the Spotify website (https://support.spotify.com/us/article/understanding-my-data/)

# ---------------------------------
# 1. Explore data in R. Find out what data is provided and explore some initial plots that might be interesting to show on a Python dash app.
# 
# Ideas:
# - total hours streaming time
# - top artist 
# - top track 
# - plots of artists vs listening time
# - plots of tracks vs listening time
# Use python and spotipy module to explore:
# - plots of listening time vs popularity, per track
# - most played genres (word cloud or bubble plot)
# - track analysis using the track features provided by spotipy
# ---------------------------------
# Install "rjson" to load in JSON file
install.packages("rjson")
install.packages("ggmice")

# Load libraries
library(dplyr)
library(ggmice)
library(ggplot2)
library(lubridate)
library(rjson)
library(tidyr)

# ---------------------------------
# Read in JSON of downloaded data
json_data <- fromJSON(file = "GitRepos/spotify_dashboard/data/test_data.json")
json_data <- fromJSON(file = "GitRepos/spotify_dashboard/data/StreamingHistory_music_0.json")

# Convert from JSON format to data frame
data <- do.call(rbind, json_data) %>%
  as.data.frame() %>%
  mutate(across(everything(), ~ unname(unlist(.))))
  
# Look at what column names we get, and if it matches with documentation on Spotify website
colnames(data)
# Extended streaming data:
# [1] "ts"                                "platform"                          "ms_played"                        
# [4] "conn_country"                      "master_metadata_track_name"        "master_metadata_album_artist_name"
# [7] "master_metadata_album_album_name"  "spotify_track_uri"                 "reason_start"                     
# [10] "reason_end"                        "shuffle"                           "offline"                          
# [13] "offline_timestamp"                 "incognito_mode"    

# Not extended streaming data:
# [1] "endTime"    "artistName" "trackName"  "msPlayed"  

data <- data %>%
  mutate(ts = endTime,
         master_metadata_album_artist_name = artistName,
         master_metadata_track_name = trackName,
         ms_played = msPlayed)

# ---------------------------------
# Check data looks sensible
# Within the date range we expect
min(data$ts)
max(data$ts)
class(data$ts)

# Convert time stamp column to separate date and time columns
# data <- data %>%
#   separate(ts, into = c("date", "time"), sep = "T") %>%
#   mutate(time = lubridate::hms(gsub("Z", "", time)),
#          date = lubridate::as_date(date)) 

data <- data %>%
  separate(ts, into = c("date", "time"), sep = " ") %>%
  mutate(date = lubridate::as_date(date)) 

# Any NAs or missing values?
ggmice::plot_pattern(data)
# > ggmice::plot_pattern(data)
# /\     /\
# {  `---'  }
# {  O   O  }
# ==>  V <==  No need for mice. This data set is completely observed.
#  \  \|/  /
#   `-----'
#   

# ---------------------------------
# Total hours streaming time
sum(data$ms_played) # this is in milliseconds
total_time_streamed <- round(seconds_to_period( sum(data$ms_played)/1000 ), 0)
# Split those up to individual times:
day(total_time_streamed)
hour(total_time_streamed)
minute(total_time_streamed)
second(total_time_streamed)

paste(day(total_time_streamed), "days,", 
       hour(total_time_streamed), "hours,",
       minute(total_time_streamed), "minutes and",
       second(total_time_streamed), "seconds.")
total_time_streamed

# ---------------------------------
# - top artist (based on streaming time)
# - top track (based on streaming time)
# Be aware that some tracks may have the same name but from different artists. Need to group by both artist and track.

# Artist and time streamed (ms)
artist_streaming_time <- data %>%
  group_by(master_metadata_album_artist_name) %>%
  summarise(total = sum(ms_played)) %>%
  arrange(desc(total))
# Top artist (based on streaming time)
artist_streaming_time$master_metadata_album_artist_name[1]

# Track and time streamed (ms)
track_streaming_time <- data %>%
  group_by(master_metadata_album_artist_name, master_metadata_track_name) %>%
  summarise(total = sum(ms_played)) %>%
  arrange(desc(total))
track_streaming_time
# Top track (based on streaming time)
top_track_streaming_time <- track_streaming_time$master_metadata_track_name[1]
top_track_streaming_time # This is a very long song!

# The artist of the top track:
top_track_artist_streaming_time <- data %>%
  filter(master_metadata_track_name == top_track_streaming_time) %>%
  pull(master_metadata_album_artist_name) %>%
  unique()
# Get the rank number for artists who's track is the most played:
which(artist_streaming_time$master_metadata_album_artist_name %in% top_track_artist_streaming_time)

# ------
# - top artist (based on frequency)
# - top track (based on frequency)
table(data$master_metadata_album_artist_name) %>% 
  sort(decreasing = TRUE) %>%
  head()
# Same top artist as streaming time

data %>%
  group_by(master_metadata_album_artist_name, master_metadata_track_name) %>%
  summarise(count = n()) %>%
  arrange(desc(count))
# Different track for most frequently played track

# Is that because the top track based on streaming time is influenced by the length of the song?
# Streaming time = "For how many milliseconds the track was played."
# We could take a look most frequently played tracks which are played for over 1 minute (ie. not instantly skipped)
# There's also a variable name for "Reason why the track ended (e.g. the track finished playing or you hit the next button)."
# We could filter by tracks that were played right until the end, and then find the most frequently played tracks.
# data %>% 
#   filter(reason_end == "trackdone") %>%
#   group_by(master_metadata_album_artist_name, master_metadata_track_name) %>%
#   summarise(count = n()) %>%
#   arrange(desc(count))
# Only available for extended streaming data

# Tracks played for over a minute (ie. not skipped)
data %>% 
  filter(ms_played/1000/60 > 1) %>%
  group_by(master_metadata_album_artist_name, master_metadata_track_name) %>%
  summarise(count = n()) %>%
  arrange(desc(count))

# The top 4 or so songs remain in the top 4 for each of these different ways of looking at most frequently played track

# ---------------------------------
# - plots of artists vs listening time
# - plots of tracks vs listening time

# Colour palette
mypal <- viridis::viridis(15)
notTopArtistColour <- "#9b95bf"

# Top 15 artists:
artist_streaming_time_15 <- data %>%
  filter(ms_played > 60/1000/60) %>%
  group_by(master_metadata_album_artist_name) %>%
  summarise(count = n()) %>%
  arrange(desc(count)) %>%
  ungroup() %>%
  slice(1:15) %>%
  arrange(count) %>%
  mutate(Artist = factor(master_metadata_album_artist_name, levels = master_metadata_album_artist_name)) %>%
  mutate(artistColour = mypal)

artist_streaming_time_15 %>%
  ggplot(data = ., aes(y = Artist, x = count)) +
  geom_col(aes(fill = Artist)) +
  scale_fill_manual(values = mypal) +
  theme(legend.position = "none") +
  xlab("Number of times artist's track is played (for more than one minute)")

# Top 15 tracks 
# Function to colour the bar the same as the artist plot above (if available)
getArtistColour <- function(artist){
  if(any(artist_streaming_time_15$Artist %in% artist)){
    col <- artist_streaming_time_15 %>%
      filter(Artist %in% artist) %>%
      pull(artistColour) %>%
      unique()
  }else{
    col <- notTopArtistColour
  }
  return(col)
}

data %>%
  filter(ms_played > 60/1000/60) %>%
  group_by(master_metadata_album_artist_name, master_metadata_track_name) %>%
  summarise(count = n()) %>%
  arrange(desc(count)) %>%
  ungroup() %>%
  slice(1:15) %>%
  rowwise() %>%
  mutate(artistColour = getArtistColour(master_metadata_album_artist_name)) %>%
  ungroup() %>%
  mutate(master_metadata_track_name = gsub("\\(.*", "", master_metadata_track_name )) %>%
  arrange(count) %>%
  mutate(Track = factor(master_metadata_track_name, levels = master_metadata_track_name)) %>%
  ggplot(data = ., aes(y = Track, x = count)) +
  geom_col(aes(fill = artistColour)) +
  scale_fill_identity()+
  xlab("Number of times track is played (for more than one minute)")



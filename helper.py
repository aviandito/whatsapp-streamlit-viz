import numpy as np
import pandas as pd
import scipy.stats as stats
from chatline import Chatline
import matplotlib.pyplot as plt
import altair as alt
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import re
import string
import streamlit as st

dow_dict = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}

def read_chat_txt(chat_txt):
	# the most important piece of code to read txt lol		
	lines = chat_txt.getvalue().decode('utf-8').splitlines() 
	
	message = {
		'timestamp': [],
		'sender': [],
		'body': [],
		'word': [],
		'emoji': [],
		'domain': []
	}

	previous_line = None
	for line in lines:
		chatline = Chatline(line=line, previous_line=previous_line)
		previous_line = chatline
	    
		message['timestamp'].append(chatline.timestamp)
		message['sender'].append(chatline.sender)
		message['body'].append(chatline.body.strip())
		message['word'].append(chatline.words)
		message['emoji'].append(chatline.emojis)
		message['domain'].append(chatline.domains)

	chat_df = pd.DataFrame(message)
	chat_df['month_full'] = chat_df['timestamp'].to_numpy().astype('datetime64[M]')
	chat_df['month'] = chat_df['timestamp'].map(lambda x: x.strftime('%Y-%m'))
	chat_df['day'] = chat_df['timestamp'].dt.day
	chat_df['date'] = chat_df['timestamp'].dt.date
	chat_df['dow'] = chat_df['timestamp'].dt.dayofweek
	chat_df['hour'] = chat_df['timestamp'].dt.hour
	chat_df['week'] = chat_df['date'] - pd.to_timedelta(chat_df['timestamp'].dt.dayofweek, unit='d')
	chat_df['body_length'] = [len(word) for word in chat_df['word']]

	return chat_df

def general_aggregation(chat_df):
	# aggregation by date, sender
	agg_day_sender = chat_df.groupby(['date', 'sender']).agg(
	    cnt_msg = pd.NamedAgg('body', aggfunc = 'count')
	).reset_index()

	# aggregation by date, month
	agg_day = chat_df.groupby(['date', 'day', 'week', 'month']).agg(
	    cnt_msg = pd.NamedAgg('body', aggfunc = 'count')
	).reset_index()

	# aggregation by date, dow, hour
	agg_day_dow_hour = chat_df.groupby(['date', 'dow', 'hour']).agg(
	    cnt_msg = pd.NamedAgg('body', aggfunc = 'count')
	).reset_index()

	# complete list for hours with no message
	full_day = pd.DataFrame({'date': pd.date_range(start= agg_day['date'].min(), end = agg_day['date'].max()).date, 'key': 0})
	full_dow = pd.DataFrame({'dow': range(0,7), 'key': 0})
	full_hour = pd.DataFrame({'hour': range(0,24), 'key': 0})
	full_day_dow_hour = full_day.merge(full_dow, how = 'outer').merge(full_hour, how = 'outer').drop(columns = 'key')

	full_day_dow_hour_agg = full_day_dow_hour.merge(agg_day_dow_hour, how = 'left').fillna(0)

	# daily msg aggregation by sender
	sender_daily_agg = agg_day_sender.groupby('sender').agg(
	    sum_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum'),
	    avg_daily_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean'),
	).reset_index()

	# avg msg by day of week & hour
	dow_hour_agg = full_day_dow_hour_agg.groupby(['dow', 'hour']).agg(
	    avg_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean')
	).reset_index()

	# weekly summarize
	weekly_sum = agg_day.groupby('week', as_index = False).agg(
	    cnt_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum')
	)

	# aggregation to be displayed as cards
	sum_msg = agg_day_sender['cnt_msg'].sum()
	daily_avg = agg_day['cnt_msg'].mean()
	hourly_avg = agg_day_dow_hour['cnt_msg'].mean()
	min_date = agg_day['date'].min().strftime('%d-%m-%Y')
	max_date = agg_day['date'].max().strftime('%d-%m-%Y')
	active_days = agg_day['date'].count()
	interval_max_min = (agg_day['date'].max() - agg_day['date'].min()).days
	active_days_pct = active_days / interval_max_min

	return min_date, max_date, sum_msg, sender_daily_agg, daily_avg, active_days, interval_max_min, active_days_pct, weekly_sum, agg_day_dow_hour, dow_hour_agg, agg_day

def plot_sender_pie(sender_daily_agg):
	sender_pie = alt.Chart(sender_daily_agg).mark_arc(innerRadius=50).encode(
	    theta=alt.Theta(field="sum_msg", type="quantitative"),
	    color=alt.Color(field="sender", type="nominal"),
	    tooltip=['sender', 'sum_msg']
	)

	return sender_pie

def plot_weekly_sum(weekly_sum):
	# Plot weekly
	weekly_sum['week'] = pd.to_datetime(weekly_sum['week'])

	brush = alt.selection(type='interval', encodings=['x'])

	msg_timeseries = alt.Chart(weekly_sum).mark_line(
	    point=True
	).encode(
	    x = 'week',
	    y = 'cnt_msg',
	    tooltip = ['week','cnt_msg']
	).properties(
	    title={
	      "text": '', 
	      "subtitle": ''
	      # "text": 'Weekly # of message sent', 
	      # "subtitle": 'Red line is the average. Highlight chart to see average in different times.'
	      }
	).add_selection(
	    brush
	)

	msg_line = alt.Chart(weekly_sum).mark_rule(color='firebrick').encode(
	    y='mean(cnt_msg):Q',
	    size=alt.SizeValue(3)
	).transform_filter(
	    brush
	)

	weekly_sum_alt = alt.layer(msg_timeseries, msg_line)

	return weekly_sum_alt

def dow_aggregation(agg_day_dow_hour):
	# most active days
	sum_dow = agg_day_dow_hour.groupby(['date', 'dow']).agg(
	    cnt_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum')
	).groupby('dow').agg(
	    avg_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean'),
	    sum_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum')
	).reset_index()

	sum_dow['pct_msg'] = sum_dow['sum_msg'] / sum_dow['sum_msg'].sum()
	sum_dow['pct_msg_cumsum'] = sum_dow.sort_values(by = 'pct_msg', ascending = False)['pct_msg'].cumsum()

	# get pareto & highest avg for dow
	pareto_dow = sum_dow[sum_dow['pct_msg_cumsum'] < 0.6]
	max_pct_cumsum_dow = pareto_dow['pct_msg_cumsum'].max()
	days_pareto_dow = [dow_dict[dow] for dow in pareto_dow['dow'].tolist()]
	highest_avg_dow = dow_dict[sum_dow.nlargest(1, 'avg_msg')['dow'].item()]
	lowest_avg_dow = dow_dict[sum_dow.nsmallest(1, 'avg_msg')['dow'].item()]

	# dist plot
	dow_boxplot = agg_day_dow_hour.groupby(['date', 'dow']).agg(
	    cnt_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum')
	).reset_index()

	return sum_dow, max_pct_cumsum_dow, days_pareto_dow, highest_avg_dow, lowest_avg_dow, dow_boxplot

def plot_dow_sum(sum_dow):
	brush = alt.selection(type='interval', encodings=['x'])

	bars = alt.Chart(sum_dow).mark_bar().encode(
	    x='dow:O',
	    y='sum_msg:Q',
	    color = 'dow:N',
	    opacity=alt.condition(brush, alt.OpacityValue(1), alt.OpacityValue(0.7)),
	).add_selection(
	    brush
	)

	return bars

def plot_dow_dist(dow_boxplot):
	dow_boxplot['date'] = pd.to_datetime(dow_boxplot['date'])

	dow_dist_plot = alt.Chart(dow_boxplot).transform_density(
	    'cnt_msg',
	    as_=['cnt_msg', 'density'],
	    groupby=['dow']
	).mark_area().encode(
	    alt.X('cnt_msg:Q'),
	    alt.Y('density:Q', title = None),
	    alt.Row('dow:N'),
	    color = 'dow:N'
	).properties(
	    width=300, 
	    height=50
	)

	return dow_dist_plot

def hour_aggregation(agg_day_dow_hour):
	# most active hour
	avg_hour = agg_day_dow_hour.groupby('hour').agg(
	    avg_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean'),
	    sum_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum'),
	).reset_index()

	avg_hour['pct_msg'] = avg_hour['sum_msg'] / avg_hour['sum_msg'].sum()
	avg_hour['pct_msg_cumsum'] = avg_hour.sort_values(by = 'pct_msg', ascending = False)['pct_msg'].cumsum()

	# get pareto & cnt hour
	pareto_hour = avg_hour[avg_hour['pct_msg_cumsum'] < 0.6]
	max_pct_cumsum_hour = pareto_hour['pct_msg_cumsum'].max()
	cnt_pareto_hour = len(pareto_hour['pct_msg_cumsum'])
	highest_avg_hour = avg_hour.nlargest(1, 'avg_msg')['hour'].item()
	lowest_avg_hour = avg_hour.nsmallest(1, 'avg_msg')['hour'].item()

	return max_pct_cumsum_hour, cnt_pareto_hour, highest_avg_hour, lowest_avg_hour

def plot_hour_line(agg_day_dow_hour):
	mean_hour = agg_day_dow_hour.groupby('hour').agg(
	    sum_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean')
	).reset_index()

	brush = alt.selection(type='interval', encodings=['x'])

	mean_timeseries = alt.Chart(mean_hour).mark_line(point=True).encode(
	    x='hour:O',
	    y='sum_msg:Q',
	    tooltip=['hour', 'sum_msg'],
	    opacity=alt.condition(brush, alt.OpacityValue(1), alt.OpacityValue(0.7)),
	).add_selection(
	    brush
	)

	avg_line = alt.Chart(mean_hour).mark_rule(color='firebrick').encode(
	    y='mean(sum_msg):Q',
	    size=alt.SizeValue(3)
	).transform_filter(
	    brush
	)

	hour_line = alt.layer(mean_timeseries, avg_line)

	return hour_line

def plot_dow_hour_heatmap(dow_hour_agg):	
	dow_hour_heatmap = alt.Chart(dow_hour_agg).mark_rect().encode(
	    x='hour:O',
	    y='dow:O',
	    color='avg_msg',
	    tooltip = ['hour', 'dow', 'avg_msg']
	).properties(
	    height=300
	)

	return dow_hour_heatmap

def month_aggregation(agg_day):
	# most active month
	avg_month = agg_day.groupby('month').agg(
	    avg_msg = pd.NamedAgg('cnt_msg', aggfunc = 'mean'),
	    sum_msg = pd.NamedAgg('cnt_msg', aggfunc = 'sum'),
	).reset_index()

	avg_month['pct_msg'] = avg_month['sum_msg'] / avg_month['sum_msg'].sum()
	avg_month['pct_msg_cumsum'] = avg_month.sort_values(by = 'pct_msg', ascending = False)['pct_msg'].cumsum()

	# get pareto & cnt month
	pareto_month = avg_month[avg_month['pct_msg_cumsum'] < 0.6]
	max_pct_cumsum_month = pareto_month['pct_msg_cumsum'].max()
	cnt_pareto_month = pareto_month[['month']]
	len_pareto_month = len(cnt_pareto_month)
	len_active_month = len(avg_month['month'].unique())
	pct_pareto_month = len_pareto_month / len_active_month

	return max_pct_cumsum_month, cnt_pareto_month, len_pareto_month, len_active_month, pct_pareto_month

def plot_month_heatmap(agg_day):
	agg_day_heatmap = agg_day[agg_day['date'] >= agg_day['date'].max() - relativedelta(years = 1)]
	
	# Plot dow-hour
	month_heatmap = alt.Chart(agg_day_heatmap[['day', 'month', 'cnt_msg']]).mark_rect().encode(
	    x='month:O',
	    y='day:O',
	    color='cnt_msg',
	    tooltip = ['day', 'month', 'cnt_msg']
	).properties(
	    # title={
	    #   "text": '# message sent by day & month', 
	    #   "subtitle": 'Color scale represents the # message sent'},
	    height = 400
	)

	return month_heatmap

def gap_aggregation(chat_df):
	# create dataframe of replies between two users
	gap_analysis_dict = {
	    'timestamp': [],
	    'sender': []
	}

	for i in range(1, len(chat_df)):
	    prev_sender = chat_df['sender'].iloc[i-1]
	    sender = chat_df['sender'].iloc[i]
	    
	    if sender != prev_sender:
	        gap_analysis_dict['timestamp'].append(chat_df['timestamp'].iloc[i])
	        gap_analysis_dict['sender'].append(chat_df['sender'].iloc[i])

	gap_analysis_df = pd.DataFrame(gap_analysis_dict)

	# add day, week, hour column
	gap_analysis_df['day'] = gap_analysis_df['timestamp'].dt.date
	gap_analysis_df['week'] = gap_analysis_df['day'] - pd.to_timedelta(gap_analysis_df['timestamp'].dt.dayofweek, unit='d')
	gap_analysis_df['hour'] = gap_analysis_df['timestamp'].dt.hour

	# generate delta in second
	gap_analysis_df['time_delta'] = gap_analysis_df['timestamp'].diff(1).dt.total_seconds()

	# weekly aggregation of average gap
	gap_agg_week = gap_analysis_df.groupby('week', as_index = False).agg(
	    median_delta_sec = pd.NamedAgg('time_delta', aggfunc = 'median')
	)

	# overall avg gap by sender
	gap_agg_sender = gap_analysis_df.groupby('sender', as_index = False).agg(
	    avg_delta_sec = pd.NamedAgg('time_delta', aggfunc = 'mean')
	)

	sender_1_avg_gap = gap_agg_sender['avg_delta_sec'][0]
	sender_2_avg_gap = gap_agg_sender['avg_delta_sec'][1]

	return gap_agg_week

def plot_weekly_gap_timeseries(gap_agg_week):
	# Plot
	gap_agg_week['week'] = pd.to_datetime(gap_agg_week['week'])

	brush = alt.selection(type='interval', encodings=['x'])

	gap_time_series = alt.Chart(gap_agg_week).mark_line(
	    point=True
	).encode(
	    x = 'week',
	    y = 'median_delta_sec',
	    tooltip = ['week', 'median_delta_sec']
	).properties(
	    title={
	      "text": 'Weekly Median Gap between senders (in seconds)', 
	      "subtitle": 'Red line is the average. Highlight chart to see average in different times.'}
	).add_selection(
	    brush
	)

	gap_line = alt.Chart(gap_agg_week).mark_rule(color='firebrick').encode(
	    y='mean(median_delta_sec):Q',
	    size=alt.SizeValue(3)
	).transform_filter(
	    brush
	)

	weekly_gap_timeseries = alt.layer(gap_time_series, gap_line)

	return weekly_gap_timeseries

def gap_xplot_aggregation(gap_analysis_df):
	# create aggregation of median gap by sender
	sender_name = []
	sender_xplot_dict = {}
	median_gap_list_xplot = []

	for sender in gap_analysis_df['sender'].unique().tolist():
	    # save sender name
	    sender_name.append(sender)
	    
	    # subset one sender
	    gap_analysis_sender = gap_analysis_df[gap_analysis_df['sender'] == sender]

	    # do aggregation
	    gap_sender_summary = gap_analysis_sender.groupby(['sender', 'hour'], as_index = False).agg(
	        median_delta_sec = pd.NamedAgg('time_delta', aggfunc = 'median')
	    )
	    
	    # get median gap
	    median_gap_list_xplot.append(np.median(gap_sender_summary['median_delta_sec']))
	    
	    # drop sender column
	    gap_sender_summary = gap_sender_summary.drop('sender', axis = 1)
	    
	    # rename column
	    gap_sender_summary = gap_sender_summary.rename(columns = {'median_delta_sec': sender.lower().split()[0] + '_median_delta_sec'})
	    
	    # put into dictionary
	    sender_xplot_dict[sender] = gap_sender_summary
	    
	# i got this from ChatGPT.... it is a wonderful tool....
	# create an empty list to store the joined DataFrames
	gap_xplot_list = []

	# loop over the DataFrames in the dictionary
	for name, df in sender_xplot_dict.items():
	    # join the DataFrame with the first element in the list
	    if len(gap_xplot_list) == 0:
	        gap_xplot_list.append(df)
	    else:
	        gap_xplot_list.append(gap_xplot_list[0].merge(df, on = 'hour'))

	gap_xplot = gap_xplot_list[-1]

	sender_1_name = sender_name[0]
	sender_2_name = sender_name[1]

	sender_1_col = gap_xplot.columns[1]
	sender_2_col = gap_xplot.columns[2]

	sender_1_median_gap = median_gap_list_xplot[0]
	sender_2_median_gap = median_gap_list_xplot[1]

	gap_xplot['ampm'] = ['AM' if hour < 12 else 'PM' for hour in gap_xplot['hour']]

	return gap_xplot

def plot_gap_xplot(gap_xplot):
	# XPlot
	gap_xplot_fig = alt.Chart(gap_xplot).mark_circle(size=60).encode(
	    x=sender_1_col,
	    y=sender_2_col,
	    color = 'ampm',
	    tooltip=[sender_1_col, sender_2_col, 'hour']
	).properties(
	    title={
	      "text": 'Median Gap by senders by hour (in seconds)', 
	      "subtitle": 'Hover on points to see the time of day'}
	)

	vline = alt.Chart(gap_xplot).mark_rule(strokeDash = [6, 6], color = 'grey').encode(
	    x=alt.datum(sender_1_median_gap),
	)

	hline = alt.Chart(gap_xplot).mark_rule(strokeDash = [6, 6], color = 'grey').encode(
	    y=alt.datum(sender_2_median_gap),
	)

	text = gap_xplot_fig.mark_text(
	    align='left',
	    baseline='middle',
	    dx=7
	).encode(
	    text='hour'
	)

	gap_xplot = alt.layer(gap_xplot_fig, text, vline, hline)

	return gap_xplot





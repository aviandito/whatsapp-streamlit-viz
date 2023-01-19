import streamlit as st
from helper import *

# Title
st.sidebar.header("WhatsApp Chat Analysis")
st.sidebar.caption("Tap the contact's name in an individual chat, then tap 'Export Chat' to get the chat history in CSV.")
st.sidebar.caption("Tested for individual chat only. No data is stored by the app. Use at your own risk.")

# create a file uploader widget in the sidebar
chat_txt = st.sidebar.file_uploader("Upload a chat text file")

# create a sidebar with a radio button group
selected_tab = st.sidebar.radio(
    "Menu", 
    (
        "General Information", 
        "Message Sent by Day of Week", 
        "Message Sent by Hour",
        "Message Sent by Month", 
        "Gap Analysis",
        "Most Favorite Emoji",
        "Most Shared Link",
        )
    )

# display different content depending on the selected tab
if chat_txt is not None:
    # read txt file
    chat_df = read_chat_txt(chat_txt)
    
    # aggregation & plot for general info
    min_date, max_date, sum_msg, sender_daily_agg, daily_avg, active_days, interval_max_min, active_days_pct, weekly_sum, agg_day_dow_hour, dow_hour_agg, agg_day = general_aggregation(chat_df)
    sender_pie = plot_sender_pie(sender_daily_agg)
    weekly_sum_alt = plot_weekly_sum(weekly_sum)
    
    # aggregation & plot for dow
    sum_dow, max_pct_cumsum_dow, days_pareto_dow, highest_avg_dow, lowest_avg_dow, dow_boxplot = dow_aggregation(agg_day_dow_hour)
    dow_sum_plot = plot_dow_sum(sum_dow)
    dow_dist_plot = plot_dow_dist(dow_boxplot)

    # aggregation & plot for hour
    max_pct_cumsum_hour, cnt_pareto_hour, highest_avg_hour, lowest_avg_hour = hour_aggregation(agg_day_dow_hour)
    hour_line = plot_hour_line(agg_day_dow_hour)
    dow_hour_heatmap = plot_dow_hour_heatmap(dow_hour_agg)

    # aggregation & plot for month
    max_pct_cumsum_month, cnt_pareto_month, len_pareto_month, len_active_month, pct_pareto_month = month_aggregation(agg_day)
    month_heatmap = plot_month_heatmap(agg_day)

    # aggregation & plot for gap
    gap_agg_week = gap_aggregation(chat_df)
    weekly_gap_timeseries = plot_weekly_gap_timeseries(gap_agg_week)
    gap_xplot = gap_xplot_aggregation(gap_analysis_df)
    gap_xplot_plot = plot_gap_xplot(gap_xplot)

    # General
    if selected_tab == "General Information":
        st.title('General Information')
        st.subheader('Total message & active days')
        col1_1, col1_2, col1_3 = st.columns(3)
        col1_1.metric("Total Message", sum_msg)
        col1_2.metric("Min Date", min_date)
        col1_3.metric("Max Date", max_date)
        col1_4, col1_5, col1_6 = st.columns(3)
        col1_4.metric("Active Days", active_days)
        col1_5.metric("Average # of message per day", round(daily_avg, 2))
        col1_6.metric("Active Days % out of {interval_max_min} days".format(interval_max_min = interval_max_min), '{active_days_pct:.2%}'.format(active_days_pct = active_days_pct))
        st.write('Weekly number of message sent')
        st.caption('Red line is the average. Highlight chart to see average in different times.')
        st.altair_chart(weekly_sum_alt, use_container_width = True)
        st.subheader('Total Message by Sender')
        col1_7, col1_8 = st.columns(2)
        col1_7.metric("Message sent by {sender} (n = {sum_msg})".format(sender = sender_daily_agg['sender'][0], sum_msg = sender_daily_agg['sum_msg'][0]), "{pct_msg:.2%}".format(pct_msg = sender_daily_agg['sum_msg'][0] / sum(sender_daily_agg['sum_msg'])))
        col1_8.metric("Message sent by {sender} (n = {sum_msg})".format(sender = sender_daily_agg['sender'][1], sum_msg = sender_daily_agg['sum_msg'][1]), "{pct_msg:.2%}".format(pct_msg = sender_daily_agg['sum_msg'][1] / sum(sender_daily_agg['sum_msg'])))
        st.altair_chart(sender_pie)
    
    # Msg sent by day of week
    elif selected_tab == "Message Sent by Day of Week":
        st.title("Message by Day of Week")             
        st.subheader('Total message by Day of Week')   
        st.metric("% of Message sent in Top {len_days_pareto_dow} days (".format(len_days_pareto_dow = len(days_pareto_dow)) + ", ".join(days_pareto_dow) + ")", '{max_pct_cumsum_dow:.2%}'.format(max_pct_cumsum_dow = max_pct_cumsum_dow))
        st.write('Sum message by day of week (0 = Monday, 6 = Sunday)')
        st.altair_chart(dow_sum_plot, use_container_width = True)
        st.subheader('Distribution of average message by Day of Week')
        col2_1, col2_2 = st.columns(2)
        col2_1.metric("Day with the highest average message sent", highest_avg_dow)
        col2_2.metric("Day with the lowest average message sent", lowest_avg_dow)
        st.write('Message Distribution by Day of Week (0 = Monday, 6 = Sunday)')
        st.altair_chart(dow_dist_plot)

    # Msg sent by hour
    elif selected_tab == "Message Sent by Hour":
        st.title("Message by Hour")
        st.subheader('Average message by Hour')
        st.metric("% of Message sent in peak hours ({cnt_pareto_hour} out of 24 hours)".format(cnt_pareto_hour = cnt_pareto_hour), '{max_pct_cumsum_hour:.2%}'.format(max_pct_cumsum_hour = max_pct_cumsum_hour))
        st.write('Average number of message by hour')
        st.caption('Red line is the average. Highlight chart to see average in different times.')
        st.altair_chart(hour_line, use_container_width = True)
        st.subheader('Message distribution by day of week & hour')
        col3_1, col3_2 = st.columns(2)
        col3_1.metric("Hour with the highest average message sent", highest_avg_hour)
        col3_2.metric("Hour with the lowest average message sent", lowest_avg_hour)
        st.write('Average message sent by day of week & hour')
        st.caption('Color scale represents the average message sent')
        st.altair_chart(dow_hour_heatmap, use_container_width = True)
    
    # Msg sent by Month
    elif selected_tab == "Message Sent by Month":
        st.title("Message by Month")
        st.subheader('Average message by Hour')
        col4_1, col4_2 = st.columns(2)
        col4_1.metric('% of Message sent within {len_pareto_month} out of {len_active_month} active months'.format(len_pareto_month = len_pareto_month, len_active_month = len_active_month), '{max_pct_cumsum_month:.2%}'.format(max_pct_cumsum_month = max_pct_cumsum_month))
        col4_2.write('List of top months')
        col4_2.table(cnt_pareto_month.style)
        st.write('Total message sent by day & month')
        st.caption('Color scale represents the total message sent')
        st.altair_chart(month_heatmap, use_container_width = True)

    elif selected_tab == "Gap Analysis":
        st.title("Analysis of Gap Between Message")

else:
    st.write("Please upload a chat text file")
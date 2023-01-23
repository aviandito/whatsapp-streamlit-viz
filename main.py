import streamlit as st
from helper import *

# page config
st.set_page_config(
    page_title = "WhatsApp Chat Analysis",
    page_icon = "💌",
    layout = "centered",
    initial_sidebar_state = "expanded",
    menu_items={
        'About': "Created by Aviandito [[GitHub](https://github.com/aviandito)] [[LinkedIn](https://www.linkedin.com/in/aviandito/)] as a gift for Dyasanti on their wedding reception in Feb 5th 2023"
    }
)

# sidebar title & disclaimer
st.sidebar.header("💌 WhatsApp Chat Analysis")
st.sidebar.caption("Tap the contact's name in an individual WhatsApp chat, then tap 'Export Chat' to get the chat history in TXT.")
st.sidebar.caption("No data is stored by the app. It only reads the emojis, links, and metadata (sender and timestamp) from your messages for the visualization purposes. Tested for individual chat only. Use at your own risk.")

# create a file uploader widget in the sidebar
chat_txt = st.sidebar.file_uploader("Upload a chat text file", type = 'txt', label_visibility = 'collapsed')

# create a sidebar with a radio button group
selected_tab = st.sidebar.radio(
    "Menu", 
    (
        "📊 General Information", 
        "📅 Message Sent by Day of Week", 
        "⌛ Message Sent by Hour",
        "🗓️ Message Sent by Month", 
        "🕒 Gap Analysis",
        "💗 Most Favorite Emoji",
        "🔗 Most Shared Link",
        )
    )


try:
    # if uploaded file is valid
    if chat_txt is not None:

        ### DATA READ & AGGREGATION
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
        max_pct_cumsum_hour, cnt_pareto_hour, highest_avg_hour, lowest_avg_hour, peak_hour_list = hour_aggregation(agg_day_dow_hour)
        hour_line = plot_hour_line(agg_day_dow_hour)
        dow_hour_heatmap = plot_dow_hour_heatmap(dow_hour_agg)

        # aggregation & plot for month
        max_pct_cumsum_month, cnt_pareto_month, len_pareto_month, len_active_month, pct_pareto_month = month_aggregation(agg_day)
        month_heatmap = plot_month_heatmap(agg_day)

        # aggregation & plot for gap
        gap_analysis_df, gap_agg_week, gap_agg_sender, sender_1_avg_gap, sender_2_avg_gap, overall_median_gap = gap_aggregation(chat_df)
        weekly_gap_timeseries = plot_weekly_gap_timeseries(gap_agg_week)
        overall_gap_min = overall_median_gap // 60
        overall_gap_sec = overall_median_gap % 60
        gap_xplot, sender_1_name, sender_2_name, sender_1_col, sender_2_col, sender_1_median_gap, sender_2_median_gap = gap_xplot_aggregation(gap_analysis_df)
        gap_difference_note, gap_stat_test_note = gap_t_test(gap_analysis_df, sender_1_name, sender_2_name, sender_1_avg_gap, sender_2_avg_gap)
        gap_xplot_plot = plot_gap_xplot(gap_xplot, sender_1_col, sender_2_col, sender_1_median_gap, sender_2_median_gap)
        both_fast, sender_1_fast, sender_2_fast, both_slow = fastslow_gap(gap_xplot, sender_1_col, sender_2_col, sender_1_median_gap, sender_2_median_gap)

        # aggregation & plot for emoji
        overall_top_10_emoji, daily_emoji_cnt, monthly_emoji_cnt, top_emoji = emoji_aggregation(chat_df)
        emoji_bar = plot_emoji_bar(overall_top_10_emoji)
        fav_emoji_df, sender_1_first_month, sender_2_first_month, emoji_1_first_month, emoji_2_first_month, sender_1_last_month, sender_2_last_month, emoji_1_last_month, emoji_2_last_month = fav_emoji_by_sender(monthly_emoji_cnt)
        love_daily_avg, love_difference_note, love_stat_test_note = love_t_test(daily_emoji_cnt)

        # aggregation & plot for links
        overall_top_10_domain, sender_cnt_domain, top_domain = link_aggregation(chat_df)
        link_overall_bar = plot_link_overall_bar(overall_top_10_domain)
        link_sender_bar = plot_link_sender_bar(sender_cnt_domain)
        domain_avg, link_difference_note, link_stat_test_note = link_t_test(chat_df)

        ### UI
        # General
        if selected_tab == "📊 General Information":
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
        elif selected_tab == "📅 Message Sent by Day of Week":
            st.title("Message by Day of Week") 
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
        elif selected_tab == "⌛ Message Sent by Hour":
            st.title("Message by Hour")
            col3_1, col3_2 = st.columns(2)
            col3_1.metric("% of Message sent in peak hours ({cnt_pareto_hour} out of 24 hours)".format(cnt_pareto_hour = cnt_pareto_hour), '{max_pct_cumsum_hour:.2%}'.format(max_pct_cumsum_hour = max_pct_cumsum_hour))
            col3_2.metric('List of peak hours', ', '.join(peak_hour_list))
            st.write('Average number of message by hour')
            st.caption('Red line is the average. Highlight chart to see average in different times.')
            st.altair_chart(hour_line, use_container_width = True)
            st.subheader('Message distribution by day of week & hour')
            col3_3, col3_4 = st.columns(2)
            col3_3.metric("Hour with the highest average message sent", highest_avg_hour)
            col3_4.metric("Hour with the lowest average message sent", lowest_avg_hour)
            st.write('Average message sent by day of week & hour')
            st.caption('Color scale represents the average message sent')
            st.altair_chart(dow_hour_heatmap, use_container_width = True)
        
        # Msg sent by Month
        elif selected_tab == "🗓️ Message Sent by Month":
            st.title("Message by Month")
            col4_1, col4_2 = st.columns(2)
            col4_1.metric('% of Message sent within {len_pareto_month} out of {len_active_month} active months'.format(len_pareto_month = len_pareto_month, len_active_month = len_active_month), '{max_pct_cumsum_month:.2%}'.format(max_pct_cumsum_month = max_pct_cumsum_month))
            col4_2.write('List of top months')
            col4_2.table(cnt_pareto_month)
            st.write('Total message sent by day & month')
            st.caption('Color scale represents the total message sent')
            st.altair_chart(month_heatmap, use_container_width = True)

        # Gap analysis
        elif selected_tab == "🕒 Gap Analysis":
            st.title("Analysis of Gap Between Message")
            st.metric('Typical time gap between senders', '{overall_gap_min:.0f}m {overall_gap_sec:.0f}s'.format(overall_gap_min = overall_gap_min, overall_gap_sec = overall_gap_sec))
            st.write('Weekly Median Gap between senders (in seconds)')
            st.caption('Red line is the average. Highlight chart to see average in different times.')
            st.altair_chart(weekly_gap_timeseries, use_container_width = True)
            st.subheader('Average gap difference between Senders')
            st.table(gap_agg_sender)
            st.write('* ' + gap_difference_note)
            st.write('* ' + gap_stat_test_note)
            st.subheader('Median gap by Sender & Hour')
            st.caption('Hover on points to see the time of day')
            st.altair_chart(gap_xplot_plot, use_container_width = True)
            st.write('* Both senders respond quickly in the following hours: ' + ', '.join(str(hour) for hour in both_fast))
            st.write('* {sender_1_name} responds quickly in the following hours: '.format(sender_1_name = sender_1_name) + ', '.join(str(hour) for hour in sender_1_fast))
            st.write('* {sender_2_name} responds quickly in the following hours: '.format(sender_2_name = sender_2_name) + ', '.join(str(hour) for hour in sender_2_fast))
            st.write('* Both senders respond slowly in the following hours: ' + ', '.join(str(hour) for hour in both_slow))
        
        # Emoji analysis
        elif selected_tab == "💗 Most Favorite Emoji":
            st.title("Emoji Analysis")
            try:
                st.metric('Most used emoji', top_emoji)
                st.write('Top 10 Emoji')
                st.caption('Number denotes the total emoji sent by all users')
                st.altair_chart(emoji_bar, use_container_width = True)
                st.subheader('❤️ Emoji Per Day')
                try:
                    st.table(love_daily_avg)
                    st.write('* ' + love_difference_note)
                    st.write('* ' + love_stat_test_note)
                except:
                    st.write('No ❤️ emoji detected. Send more love to each other!')
                st.subheader('Top Emoji by Sender & Month')
                col6_1, col6_2 = st.columns(2)
                col6_1.metric("{sender_1_first_month}'s favorite emoji in the first month".format(sender_1_first_month = sender_1_first_month), emoji_1_first_month)
                col6_1.metric("{sender_1_last_month}'s favorite emoji in the last month".format(sender_1_last_month = sender_1_last_month), emoji_1_last_month)
                col6_2.metric("{sender_2_first_month}'s favorite emoji in the first month".format(sender_2_first_month = sender_2_first_month), emoji_2_first_month)
                col6_2.metric("{sender_2_last_month}'s favorite emoji in the last month".format(sender_2_last_month = sender_2_last_month), emoji_2_last_month)
                st.write('First three months')
                st.table(fav_emoji_df.head(6))
                st.write('Last three months')
                st.table(fav_emoji_df.tail(6))
            except Exception as e:
                st.write(e)
                st.write('No emoji were detected in the messages')

        # Link analysis
        elif selected_tab == "🔗 Most Shared Link":
            try:
                st.title('Shared Link Analysis')
                st.metric("Most shared domain", top_domain)
                st.altair_chart(link_overall_bar, use_container_width = True)
                st.subheader('Links shared per day')
                st.table(domain_avg)
                st.write('* ' + link_difference_note)
                st.write('* ' + link_stat_test_note)
                st.subheader('Top domains of shared links by sender')
                col7_1, col7_2 = st.columns(2)
                col7_1.altair_chart(link_sender_bar[0])
                col7_2.altair_chart(link_sender_bar[1])
            except Exception as e:
                st.write(e)
                st.write('No links were detected in the messages')
    
    # if no uploaded file is detected
    else:
        st.write("Please upload a chat text file")

# if uploaded file is invalid
except Exception as e:
    st.write(e)
    st.write("Please upload a valid Whatsapp chat text file")
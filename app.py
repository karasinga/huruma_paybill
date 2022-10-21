import base64
import calendar
import os
import glob
import re

import parse
import pdfplumber
from datetime import datetime
import streamlit as st

import pandas as pd
import plotly.express as px

st.set_page_config(page_title="AHGCC_PAYBILL_ANALYZER", layout="wide")
# To hide hamburger (top right corner) and “Made with Streamlit” footer,
hide_streamlit_style = """
                       <style>
                       #MainMenu {visibility: hidden;}
                       footer {visibility: hidden;}
                       </style>
                       """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown(
    "<h3 style='text-align: center; color: blue;'>AHGCC HURUMA PAYBILL STATEMENT ANALYZER</h3>",
    unsafe_allow_html=True)


def st_pandas_to_csv_download_link(_df: pd.DataFrame, file_name: str = "dataframe.csv"):
    """ This function decodes dataframe to downloadable cvs"""
    csv_exp = _df.to_csv(index=False)
    b64 = base64.b64encode(csv_exp.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}" > Download (.csv) </a>'
    st.markdown(href, unsafe_allow_html=True)


uploaded_file = st.file_uploader('Choose your .pdf file', type="pdf")


def side_bar():
    table_of_contents = st.sidebar.selectbox("Table of content",
                                             options=['Home', 'Summary',
                                                      # 'Trends',
                                                      'Clear all cache'
                                                      ],
                                             index=0)
    return table_of_contents


@st.experimental_memo
def prepared_data(non_duplicates_df,ids):
    non_duplicates_dfs = non_duplicates_df[~ids.isin(ids[ids.duplicated()])]
    dfs = non_duplicates_dfs.copy()
    # dfs = pd.concat([non_duplicates_dfs, dups_final_df])
    dfs = dfs[dfs['Paid In'] != ""]
    dfs['Paid In'] = dfs['Paid In'].astype(str).replace('\.00', '', regex=True)
    dfs['Paid In'] = dfs['Paid In'].astype(str).replace(',', '', regex=True)
    dfs['Paid In'] = dfs['Paid In'].astype(int)

    dfs['Completion\nTime'] = pd.to_datetime(dfs['Completion\nTime'], dayfirst=True)
    dfs['Dates'] = pd.to_datetime(dfs['Completion\nTime']).dt.date
    dfs['Time'] = pd.to_datetime(dfs['Completion\nTime']).dt.time
    dfs['month'] = pd.to_datetime(dfs['Completion\nTime']).dt.month

    dfs['month_'] = dfs['month'].apply(lambda x: calendar.month_abbr[x])
    return dfs


def trend_charts(trends):
    for i in trends['type'].unique():
        a = trends[trends['type'] == i]
        if len(a) != 0:
            del a['month']
            st.write(a.astype(str))
            st_pandas_to_csv_download_link(a.astype(str), file_name=f"{i} summary.csv")
            totals = sum(a['Paid In'])

            avg = int(a['Paid In'].mean())
            fig = px.line(a, x='month_', y='Paid In', text='Paid In',
                          title=f"{i.upper()} Total: {totals}  Monthly average:{avg}")
            fig.update_traces(textposition="top center")
            fig.update_layout(xaxis_title="Months", yaxis_title=f"{i}")
            fig.update_layout(
                # width=500,
                height=550,
                # title="Plot Title",
                # xaxis_title="Payment type",
                # yaxis_title="Y Axis Title",
                # legend_title="Legend Title",
                font=dict(
                    family="Courier New, monospace",
                    size=18,
                    color="RebeccaPurple"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("***")


# @st.experimental_memo
# def transform_data(uploaded_file, name):
#     # convert PDF into CSV file
#     tabula.convert_into(uploaded_file, f"data/{name}.csv", output_format="csv", pages='all')

def read_pdf_file(file):
    pdf = pdfplumber.open(file)
    dfs = []
    for page in pdf.pages:
        st.write(f"Reading {page} ...")
        dfs.append(pd.DataFrame(page.extract_table()))
    st.write("Done!")
    df = pd.concat(dfs)
    df.columns = df.iloc[0]
    df = df[1:]
    df = df[df['Paid In'] != ""]
    df = df[df['Details'] != 'Details']
    df['Paid In'] = df['Paid In'].astype(str).replace('\.00', '', regex=True)
    df['Paid In'] = df['Paid In'].astype(str).replace(',', '', regex=True)

    df['Paid In'] = df['Paid In'].astype(int)
    return df



@st.experimental_memo
def extract_statement_dates(file):
    line_re = re.compile(r'\d{2}-\d{2}-\d{4} (.*)')
    first_date = re.compile(r'\d{2}-\d{2}-\d{4}')
    line_re1 = re.compile(r'\d{2}-\d{2}-\d{4} (.*)')

    with pdfplumber.open(file) as pdf:
        # pages = pdf.pages
        for page in pdf.pages:
            text = page.extract_text()
            for line in text.split('\n'):
                # comp = line_re.search(line)
                if line.startswith('Time Period'):
                    start_date = first_date.search(f"{line}").group(0)
                    end_date = first_date.search(line_re1.search(f"{line}").group(1)).group(0)
            #                     print(start_date)
            #                     print(end_date)
            break
    return start_date, end_date


def time_taken_all(start_time):
    st.warning("To read and analyze all PDF pages, it took (hh:mm:ss) {}".format(
        datetime.now().replace(microsecond=0) - start_time))

if uploaded_file is not None:

    name = uploaded_file.name
    name = name.replace(".pdf", "")
    # print(uploaded_file)
    # print(uploaded_file.name)
    start_date, end_date = extract_statement_dates(uploaded_file)
    # print("______________________________________")
    # print(start_date)
    # print(end_date)
    # transform_data(uploaded_file, name)
    with st.expander("PDF pages read"):
        start_time = datetime.now().replace(microsecond=0)
        df=read_pdf_file(uploaded_file)
        time_taken_all(start_time)

    # df = pd.read_csv(f"data/{name}.csv", low_memory=False)


    # table_of_contents = side_bar()

    @st.experimental_memo
    def data_wrangle(df):
        # df = df[1:]
        # df = df[df['Details'] != 'Details']
        # df = df.copy()
        # df["Receipt No."] = df["Receipt No."].fillna(method="ffill").fillna(0)
        # df["Completion\nTime"] = df["Completion\nTime"].fillna(method="ffill").fillna(0)
        # df["Initiation Time"] = df["Initiation Time"].fillna(method="ffill").fillna(0)
        # df["Paid In"] = df["Paid In"].fillna(method="ffill").fillna(0)
        # df["Withdrawn"] = df["Withdrawn"].fillna(method="ffill").fillna(0)
        # df["Balance"] = df["Balance"].fillna(method="ffill").fillna(0)
        # df["Reason Type"] = df["Reason Type"].fillna(method="ffill").fillna(0)
        # df["Other Party Info"] = df["Other Party Info"].fillna(method="ffill").fillna(0)

        df['Details'] = df['Details'].str.lower()

        ids = df["Receipt No."]

        non_duplicates = df[~ids.isin(ids[ids.duplicated()])]
        dups = df[ids.isin(ids[ids.duplicated()])]
        return non_duplicates, dups


    non_duplicates, dups = data_wrangle(df)


    @st.experimental_memo
    def get_payment_method(non_duplicates):
        # TITHE
        tithe = non_duplicates[
            non_duplicates['Details'].str.contains("tith|tigh|10percnt|paym|pay m|tyth|tih|Thit|seed|tuthe",
                                                               na=False)]
        tithe = tithe.copy()
        tithe['type'] = "tithe"
        # THANGSGIVING
        thansgiving = non_duplicates[non_duplicates['Details'].str.contains("than|ngatho|other", na=False)]
        thansgiving = thansgiving.copy()
        thansgiving['type'] = "thanksgiving"
        # OFFERING
        offering = non_duplicates[non_duplicates['Details'].str.contains("off|muho|ofrg|ofee", na=False)]
        offering = offering.copy()
        offering['type'] = "offering"
        # HARAMBEE
        harambee = non_duplicates[non_duplicates['Details'].str.contains(
            "hall|fund|haram|ngenia|freearea|malindi|pcg|fd|kihoto|juja|proj", na=False)]
        harambee = harambee.copy()
        harambee['type'] = 'harambee'
        # pastor's GIFT
        pastors = non_duplicates[non_duplicates['Details'].str.contains("past", na=False)]
        pastors = pastors.copy()
        pastors['type'] = 'pastors day'
        # with names or without names
        others = non_duplicates[~non_duplicates['Details'].str.contains(
            "past|hall|fund|hara|ngenia|freearea|malindi|pcg|fd|kihoto|juja|proj|off|muho|ofrg|ofee|than|ngatho|other|tith|tigh|10percnt|paym|pay m|tyth|tih|Thit|seed|tuthe",
            na=False)]
        others = others.copy()
        others['type'] = 'others'
        return tithe, thansgiving, offering, harambee, pastors, others


    tithe, thansgiving, offering, harambee, pastors, others = get_payment_method(non_duplicates)


    # st.write(tithe.astype(str))

    # DUPLICATES
    # @st.experimental_memo
    # def work_on_duplicates(dups):
    #     tithes = []
    #     thansgivings = []
    #     offerings = []
    #     harambees = []
    #     pastors_gift = []
    #     others_ = []
    #
    #     for record in dups['Receipt No.'].unique():
    #         # MAKE DF FOR UNIQUE VALUES
    #         a = dups[dups['Receipt No.'] == record]
    #         # MAKE ALL POSSIBLE DFS
    #         tithe, thansgiving, offering, harambee, pastors, others = get_payment_method(a)
    #         # APPEND TO LIST
    #         tithes.append(tithe)
    #         thansgivings.append(thansgiving)
    #         harambees.append(harambee)
    #         offerings.append(offering)
    #         pastors_gift.append(pastors)
    #         others_.append(others)
    #     # MAKE DFS
    #     tithes_df = pd.concat(tithes)
    #     thansgivings_df = pd.concat(thansgivings)
    #     offerings_df = pd.concat(offerings)
    #     harambees_df = pd.concat(harambees)
    #     pastors_gift_df = pd.concat(pastors_gift)
    #     others_df = pd.concat(others_)
    #     return others_df, tithes_df, thansgivings_df, harambees_df, pastors_gift_df, offerings_df
    #
    #
    # others_df, tithes_df, thansgivings_df, harambees_df, pastors_gift_df, offerings_df = work_on_duplicates(dups)


    @st.experimental_memo
    def clean_others_list(others_df, tithes_df, thansgivings_df, harambees_df, pastors_gift_df, offerings_df):
        # MAKE LISTS
        others_lst = list(others_df['Receipt No.'].unique())

        tithe_lst = list(tithes_df['Receipt No.'].unique())
        thansgiving_lst = list(thansgivings_df['Receipt No.'].unique())
        harambee_lst = list(harambees_df['Receipt No.'].unique())
        pastors_lst = list(pastors_gift_df['Receipt No.'].unique())
        offerings_lst = list(offerings_df['Receipt No.'].unique())

        # ENSURE OTHERS LIST IN NOT IN THE OTHER LISTS
        others_lst = [x for x in others_lst if x not in tithe_lst]
        others_lst = [x for x in others_lst if x not in thansgiving_lst]
        others_lst = [x for x in others_lst if x not in harambee_lst]
        others_lst = [x for x in others_lst if x not in pastors_lst]
        others_lst = [x for x in others_lst if x not in offerings_lst]

        # Use a list of values to select rows from a Pandas dataframe
        others_df = others_df[others_df['Receipt No.'].isin(others_lst)]
        # DROP DUPLICATES AND KEEP LAST
        others_df = others_df.drop_duplicates(["Receipt No."], keep='last')
        # FINAL OTHERS DF/? OFFERING
        #     others_df
        return others_df


    # others_df = clean_others_list(others_df, tithes_df, thansgivings_df, harambees_df, pastors_gift_df, offerings_df)
    # st.write(others_df.astype(str))

    # dups_final_df = pd.concat([others_df, tithes_df, thansgivings_df, harambees_df, pastors_gift_df, offerings_df])
    # st.write(dups_final_df.shape)

    # NON DUPLICATES
    tithe, thansgiving, offering, harambee, pastors, others = get_payment_method(non_duplicates)
    # others.shape
    # CLEAN OTHERS
    others_df_non_duplicates = clean_others_list(others, tithe, thansgiving, harambee, pastors, offering)

    non_duplicates_df = pd.concat([thansgiving, harambee, pastors, offering, others_df_non_duplicates, tithe])

    # CLEAN THIS DATA
    ids = non_duplicates_df["Receipt No."]
    # if table_of_contents == "Home":
    dups_2_df = non_duplicates_df[ids.isin(ids[ids.duplicated()])].sort_values("Receipt No.")
    total_dups = sum(dups_2_df['Paid In'])

    list1 = list(non_duplicates_df['Receipt No.'].unique())

    list2 = list(non_duplicates['Receipt No.'].unique())

    set1 = set(list1)
    set2 = set(list2)

    missing = list(sorted(set1 - set2))
    added = list(sorted(set2 - set1))

    # print('missing:', missing)
    # print('added:', added)

    not_analyzed_df = non_duplicates[non_duplicates['Receipt No.'].isin(added)]
    not_analyzed_df=not_analyzed_df.copy()
    not_analyzed_df['type']=""
    total_not_analyzed_df = sum(not_analyzed_df['Paid In'])
    not_analyzed_dfs=pd.concat([dups_2_df,not_analyzed_df])



    if len(not_analyzed_dfs) != 0:
        st.error(
            f"This data needs manual cleaning. The statement has {(dups_2_df.shape[0]/2+not_analyzed_df.shape[0])} records that were not used in "
            f"this analysis. ({(total_dups/2)+total_not_analyzed_df})")
        if len(not_analyzed_dfs) != 0:
            with st.expander(
                    f"Please clean this data set. The records have a combination of these two:  {dups_2_df['type'].unique()}"
                    f"or not analyzed because of other reasons"):
                # st.write(dups_2_df.astype(str))
                st_pandas_to_csv_download_link(not_analyzed_dfs.astype(str), file_name="unclean data.csv")
        st.markdown("***")

    # SUMMARY
    # summary = pd.concat([non_duplicates_df, dups_final_df])
    # if len(summary) != 0:
    #     with st.expander(f"Download summary CSV"):
    #         st.success(f"The statement has {summary.shape[0]} records")
    #         # st.write(summary.astype(str))
    #         st_pandas_to_csv_download_link(summary.astype(str), file_name=f"{name} statement.csv")
    # st.markdown("***")
    with st.expander("SUMMARY",expanded=True):
        # if table_of_contents == "Summary":
        # ANALYSIS

        st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)
        st.markdown(
            f"<h5 style='text-align: center; color: green;"
            f"'>SUMMARY FOR TIME PERIOD: {start_date} TO {end_date}"
            f"</h5>",
            unsafe_allow_html=True)
        st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)

        dfs = prepared_data(non_duplicates_df,ids)
        all_df = dfs.groupby(['type']).sum()['Paid In'].reset_index().sort_values('Paid In')
        st.write(all_df.astype(str))
        st_pandas_to_csv_download_link(all_df.astype(str), file_name="summary.csv")

        trends = dfs.groupby(['type', 'month', 'month_']).sum()['Paid In'].reset_index().sort_values('month')

        total = sum(all_df['Paid In'])

        fig = px.bar(all_df, x='type', y='Paid In', text='Paid In',
                     title=f'Contribution so far  (Total: {total})')
        fig.update_layout(
            # title="Plot Title",
            xaxis_title="Payment type",
            # yaxis_title="Y Axis Title",
            # legend_title="Legend Title",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple"
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        fig = px.pie(trends, values='Paid In', names='type', title='Distribution of cash received',
                     )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            height=550,
            # title="Plot Title",
            xaxis_title="Payment type",
            # yaxis_title="Y Axis Title",
            # legend_title="Legend Title",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple"
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        # with st.expander("TRENDS"):
        # if table_of_contents == "Trends":
        # dfs = prepared_data(non_duplicates_df)
        st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)
        st.markdown(
            "<h5 style='text-align: center; color: green;'>TRENDS</h5>",
            unsafe_allow_html=True)
        st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """,
                    unsafe_allow_html=True)
        trends = dfs.groupby(['type', 'month', 'month_']).sum()['Paid In'].reset_index().sort_values('month')

        trend_charts(trends)
    # with st.expander("CLEAR CACHE"):
    #     analyze_button = st.button('Clear cache', on_click=None)
    #     if analyze_button == True:
    #         # if table_of_contents == "Clear all cache":
    #         # clear the content of a data folder
    #         files = glob.glob('data/*')
    #         for f in files:
    #             os.remove(f)
    #         # clear cache
    #         st.experimental_memo.clear()

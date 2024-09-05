from groq import Groq
import streamlit as st
import os
import tempfile
from crewai import Crew, Agent, Task, Process
import json
import os
import requests
from crewai_tools import tool
from crewai import Crew, Process
import tomllib
from langchain_groq import ChatGroq
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection
from crewai_tools import SerperDevTool
import time
from pyairtable import Table


# create title for the streamlit app

st.title('Startup Competitor Analysis and Optimization Tool')

# create description for the streamlit app

st.write('This app will help you to analyze the competitors of your startup and provide advice on how to optimize your value proposition, painpoint and target market based on the competitor analysis. Please take into account that executing the analysis will take several minutes. For more information, please contact Dries Faems, https://www.linkedin.com/in/dries-faems-0371569/')

# read excell file Access

access = st.text_input('Please enter your WHU email address').lower()

# Establish connection to Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

AIRTABLE_API_KEY = st.secrets["AIRTABLE_API_KEY"]
BASE_ID = st.secrets["BASE_ID"]
TABLE_NAME = st.secrets["TABLE_NAME"]  # Replace with your table name

airtable = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)

# Read existing data from the sheet
accessdata = conn.read(worksheet = "Sheet2")

# check if the access code is correct

accesslist = accessdata['Email'].tolist()

if len(access) == 0:
    st.write('')
elif access not in accesslist:
    st.write('Access code invalid; Please enter the correct WHU email address')
else:

    # user needs to input Groq API key

    groq_api_key = st.text_input('Please provide your Groq API Key. You can get and use the API key at https://groq.com/', type="password")

    # user needs to input Serper API key

    serper_api_key = st.text_input('Please provide your Serper API Key. You can get and use the API key at https://serper.dev/', type="password")

    # user needs to input the value proposition of the startup

    value_proposition = st.text_area('Please provide the value proposition of the startup')

    # user needs to input the painpoint of the startup

    painpoint = st.text_area('Please provide the painpoint of the startup')

    # user needs to input the target market of the startup

    target_market = st.text_area('Please provide the target market of the startup')

    # user needs to input the unfair advantage of the startup

    unfair_advantage = st.text_area('Please provide the unfair advantage of the startup')

    # click on the button to start the analysis

    if st.button('Start Analysis; THe analysis will take several minutes to complete'):
        os.environ['GROQ_API_KEY'] = groq_api_key
        os.environ['SERPER_API_KEY'] = serper_api_key

        # Create a new record as a DataFrame
        new_record = {
            'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'User': access,
            'Action': 'Clicked on Start Interview',
            'Value_Proposition': value_proposition,
            'Painpoint': painpoint,
            'Target_Market': target_market,
            'Unfair_Advantage': unfair_advantage
        }

        airtable.create(new_record)

        client = Groq()
        GROQ_LLM = ChatGroq(model="llama3-70b-8192")


        # Create the search tool
        search_tool = SerperDevTool()

        # Define the agent for first crew
        search_agent = Agent(
            role='Competition Finder',
            goal='Search on the internet for competing companies for a specific startup based on the value propositon, painpoint, and target market of the startup.',
            llm=GROQ_LLM,
            verbose=True,
            memory=True,
            backstory=(
            """You are a diligent researcher specialized in finding competitors based on a value proposition and a target market. 
            You have creative approaches to find companies that (i) provide a similar value proposition and/or (ii) try to solve a similar painpoint and/or (iii) target the same market segment."""  
            ),
            tools=[search_tool],
            max_iterations=3
        )

        # Define the task
        search_task = Task(
            description=(
            """Find companies that are competitors of a specific startup based on the value proposition, painpoint, and target market of the startup. 
            Here is the necessary information: Value proposition: {value_proposition}, Painpoint: {painpoint}, Target market: {target_market}.""" 
            ),
            expected_output='A list of companies that are competitors of the startup. For each company, the following information is provided: Name, Website, Description, and the reason why it is considered a competitor.',
            tools=[search_tool],
            agent=search_agent,
        )

        # Combine into a crew
        crew = Crew(
            agents=[search_agent], 
            tasks=[search_task],
            process=Process.sequential
        )

        # Execute the crew
        result = crew.kickoff(inputs={'value_proposition': value_proposition, 
                                        'painpoint': painpoint, 
                                        'target_market': target_market
                                        },)

        analysis = search_task.output.raw_output
        st.markdown('## Competitor Analysis ##')
        st.write(analysis)
        time.sleep(30)

        # Define the agent for the second crew

        optimization_agent = Agent(
            role='Optimization Advicer',
            goal='Use the competitor analsysis to provide advice on how to optimize the value proposition, painpoint and target market to make it as unique as possible.',
            llm=GROQ_LLM,
            verbose=True,
            memory=True,
            backstory=(
            """You are an expert in helping entrepreneurs in optimizing their value proposition, painpoint and target market based on the competitor analysis. 
            You have unique skills in helping startups in making their value proposition as unique as possible. The core objective is to provide advice, not to provide the ultimate solutions.
            Your role is mainly pedagogical, not operational. The user will provide you his/her own ideas about the unfair advantage of the startup. Your role is to help the user to make these ideas as unique as possible."""  
            ),
            max_iterations=3
        )

        optimization_task = Task(
            description=(
            """Provide advice on how to optimize the value proposition, painpoint and target market based on the competitor analysis and considering the unfair advantage as identified by the entrepreneur. 
            Here is the necessary information: Value proposition: {value_proposition}, Painpoint: {painpoint}, Target market: {target_market}, Unfair advantage: {unfair_advantage}, Competitor analsyis: {analysis}.""" 
            ),
            expected_output='Provide concrete advice on how the startup can differentiate itself from the competition. The advice should be based on the competitor analysis and the unfair advantage of the startup.',
            agent=optimization_agent,
        )
        # Combine into a crew
        crew = Crew(
            agents=[optimization_agent], 
            tasks=[optimization_task],
            process=Process.sequential
        )

        # Execute the crew
        result = crew.kickoff(inputs= {'value_proposition': value_proposition,
                                        'painpoint': painpoint, 
                                        'target_market': target_market,
                                        'unfair_advantage': unfair_advantage,
                                        'analysis': analysis
                                        },)

        optimization = optimization_task.output.raw_output

        st.markdown('## Optimization Advice ##')
        st.write(optimization)

    else:
        st.write('Please provide the necessary information and click on the button to start the analysis')
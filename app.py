# bls-api-explorer
# Author: Christopher Morris
# License: Non-Commercial, No-Derivatives License
#
# You may use this code for personal, educational, or non-commercial research purposes
# with proper attribution. Commercial use, redistribution, or modification is not allowed
# without explicit permission from the author.
#
# For full license terms, see the LICENSE file.

import streamlit as st
from datetime import datetime
import pandas as pd
from py_bls_api import get_surveys, get_bls_data, get_survey_metadata


@st.cache_data
def load_surveys():
    """
    Load and cache the list of available BLS surveys that py-bls-api supports.
    
    Returns:
        dict: Dictionary of survey abbreviations and their full names
    """    
    return get_surveys()


def configure_user_interface():
    """
    Configure the page layout and apply custom CSS styling.
    """    
    st.set_page_config(page_title="BLS API Explorer", page_icon="⚙️", layout="wide")
        
    st.markdown("""
        <style>
        [data-testid="baseButton-secondary"] {
            background-color: #17157a !important;
            color: white !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #f5f7fa;
        }
        
        </style>
    """, unsafe_allow_html=True)


def display_app_header():
    """
    Display the application header with custom styling.
    """    
    st.markdown("<h1 style='color: #006F96;'>BLS API Explorer</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 2px solid #006F96; margin-top: -10px; margin-bottom: 10px;'>", unsafe_allow_html=True)


def create_sidebar():
    """
    Create the sidebar with disclaimer, getting started information, and about sections.
    """
    # Display disclaimer about unofficial status
    st.sidebar.markdown("""
                        <p style="color:red;"> 📢 <b>DISCLAIMER:</b> <br>This app is not an offical BLS product. 
                        BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.</p>
                        """, unsafe_allow_html=True)

    # Getting started section with API key registration link
    st.sidebar.header("Getting Started")
    st.sidebar.markdown("""
        Register for a free [API Key](https://data.bls.gov/registrationEngine/) and follow the instructions in the app to begin.                            
        """)

    # About section explaining the BLS API
    st.sidebar.header("About the BLS API Explorer")
    st.sidebar.markdown("""
        The [BLS API](https://www.bls.gov/developers/) is a data service that provides on-demand access to machine readable metadata and data.
        This app offers a user-friendly interface for exploring the BLS API with **no coding experience required**. 
        
        It's designed for both beginners looking to easily browse data and developers who want dynamic Python code examples for integrating the API into analytical workflows.
                
        """)
    st.sidebar.header("About Me")
    st.sidebar.markdown("""
        I created this app because I am passionate about making open data more findable, accessible and usable for everyone. 
        Whether you are new to APIs or an experienced programmer, I hope this tool helps you to explore BLS data more easily.
                                
        Happy Data Exploration and Coding!
                        
        Connect with me:
        [Github](https://github.com/coding-with-chris/py-bls-api) 
        """)


def create_survey_picklist(datasets):
    """
    Create a picklist of available BLS datasets.
    
    Parameter:
        datasets (dict): Dictionary of survey abbreviations and their full names
        
    Returns:
        tuple: Selected survey abbreviation and full name
    """    
    st.markdown("<h3 style='color: #006F96;'>Explore Datasets</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns([.70, .30])
    with col1:
        options_survey = sorted(list(datasets.keys()))
        survey = st.selectbox('Select a dataset:', options_survey, index=0)    
        survey_name = datasets[survey]

    return survey, survey_name


def display_description(description):
    """
    Display the dataset description in a styled container.
    
    Parameter:
        description (str): Text description of the selected dataset
    """    
    st.markdown("<h5 style='color: #006F96;'>Dataset Description</h5>", unsafe_allow_html=True)

    # Create a styled box for the description with scrolling if needed
    st.markdown(
        f"""
        <div style="background-color: #e1f5fe; color: #000000; padding: 10px; border-left: 5px solid #2196f3;
                    max-height: 200px; overflow-y: auto; border-radius: 5px;">
            {description}
        </div>
        """,
        unsafe_allow_html=True
    )


def display_data_preview(metadata):
    """
    Display a preview of the survey data with sample data.
    
    Parameter:
        metadata (dict): Metadata dictionary containing data preview
    """    
    st.markdown("<h5 style='color: #006F96;'>Data Preview:</h5>", unsafe_allow_html=True)
    dataset_preview = pd.DataFrame(metadata['data_preview']).drop(columns=['survey_name','survey_abbreviation'])
    dataset_preview.set_index('series_id', inplace=True)
    st.dataframe(dataset_preview)


def prepare_series_picklist(metadata):    
    """
    Prepare the series picklist by combining Series IDs with their titles.
    
    Parameter:
        metadata (dict): Metadata dictionary containing series information
        
    Returns:
        list: Picklist of series IDs and titles
    """    
    # Extract series IDs and titles from metadata    
    series_ids = [series['id'] for series in metadata['series']]
    series_titles = [series.get('title', '') for series in metadata['series']]  

    # Combine IDs and titles for the picklist
    series_picklist = [f"{series_id}: {title}" for series_id, title in zip(series_ids, series_titles)]

    return series_picklist


def display_api_query_builder(series_picklist, minimum_year, maximum_year):
    """
    Display the API query builder form with input fields for API parameters.
    
    Parameters:
        series_picklist (list): List of series IDs and title strings
        minimum_year (str): Earliest available year for the dataset
        maximum_year (str): Latest available year for the dataset
        
    Returns:
        tuple: Form submission status, API key, start year, end year, and selected series IDs
    """        
    st.markdown("<h3 style='color: #006F96;'>API Query Builder: Build Your Own Request</h3>", unsafe_allow_html=True)

    # Create a form to batch inputs and prevent unnecessary reruns
    with st.form(key='api_query_builder'):
        col3, col4 = st.columns([.42, .58])

        # Create text input for users API key        
        with col3:
            # Load the demo (default) key from Streamlit secrets
            demo_registrationkey = st.secrets.get("bls_api_key", "")
            
            # Initialize session state for the registration key if it doesn't exist yet
            if "user_registrationkey" not in st.session_state:
                st.session_state.user_registrationkey = ""            
            
            user_registrationkey = st.text_input("Enter Your BLS API Key", 
                                                 value=st.session_state.user_registrationkey, 
                                                 help="Register for an API key at https://data.bls.gov/registrationEngine/.")

            # Update session state if the user changed the input
            if user_registrationkey.strip() and user_registrationkey.strip() != st.session_state.user_registrationkey:
                st.session_state.user_registrationkey = user_registrationkey.strip()
            
            # Final key to use
            registrationkey = st.session_state.user_registrationkey or demo_registrationkey

        # Create year slider
        with col4:
            year_range = st.slider('Select Year Range', int(minimum_year), int(maximum_year), (int(maximum_year)-5, int(maximum_year)), help="The min and max on the year slider apply to the dataset and not to individual series.")
            startyear = year_range[0]
            endyear = year_range[1]

        # Create multi-select for series IDs with default selection and help text
        selected_seriesids = st.multiselect(f'Select 1 or more series ({len(series_picklist)} available)', series_picklist, default=[series_picklist[0]], help="For more information about series formats, visit https://www.bls.gov/help/hlpforma.htm.")
                  
        # Submit button to trigger the API request        
        submit_button = st.form_submit_button('Get Data')

    # Extract just the series IDs from the selected options (remove titles)        
    seriesids = [series_id.split(':')[0] for series_id in selected_seriesids]

    return submit_button, registrationkey, startyear, endyear, seriesids


def display_output(data, log, survey):
    """
    Display the API response data or log messages.
    
    Parameters:
        data (pd.DataFrame): DataFrame containing the API response data
        log (pd.DataFrame): DataFrame containing any log messages or errors
        survey (str): Survey abbreviation for naming the download file
    """    
    # If there are log messages, display them    
    if not log.empty:        
        st.write(log)
        
    else:
        # Show success animation (balloons) once
        if st.session_state.get("show_balloons", False):
              st.balloons()
              st.session_state["show_balloons"] = False
        
        # Display success message        
        st.markdown("""
        <div style="
            background-color: #d4edda;
            color: #155724;
            padding: 10px 15px;
            border-left: 5px solid #28a745;
            border-radius: 5px;
            font-size: 16px;">
            SUCCESS! No log messages returned from the API.
        </div>
        """, unsafe_allow_html=True)    
                
        st.write("")

        # Display the data table        
        st.markdown("<h5 style='color: #006F96;'>Output:</h5>", unsafe_allow_html=True)
        st.write(data)   
        
        # Add CSV download button if data is a DataFrame        
        if isinstance(data, pd.DataFrame):
            csv_data = data.to_csv(index=False)
            todays_date = datetime.today().strftime('%Y-%m-%d')
                    
            st.download_button(
                label="Download CSV File",
                data=csv_data,
                file_name=f"{todays_date} {survey}.csv",
                mime="text/csv",
                key="download_button",
                use_container_width=False,
                help="Click to download the data as a CSV file"
            )    

        st.write("")
        

def display_code(data, seriesids, startyear, endyear, registrationkey, survey_name):
    """
      Display Python code examples for reproducing the API request using the py-bls-api wrapper.
        
      Parameters:
          data (pd.DataFrame): DataFrame to check if empty
          seriesids (list): List of selected series IDs
          startyear (int): Start year for the data request
          endyear (int): End year for the data request
          registrationkey (str): BLS API key
          survey_name (str): Full name of the selected survey
      """    
    # Only show code examples if data was successfully retrieved      
    if not data.empty:
        st.markdown("<h5 style='color: #006F96;'>Python Code:</h5>", unsafe_allow_html=True)
    
        # Create tabs for different code examples    
        tab1, tab2, tab3 = st.tabs(["Data", "Metadata", "License"])

        # Only show API key if it is the users.
        api_key_to_show = "your_api_key" if registrationkey == st.secrets.get("bls_api_key") else registrationkey

        # Code example for retrieving data    
        with tab1:
            python_script = f"""
            # First, install the required package:
            # pip install py-bls-api
            
            import pandas as pd
            from py_bls_api import get_surveys, get_bls_data, get_survey_metadata
        
            data, log = get_bls_data(seriesids={seriesids}, 
                                     startyear={startyear}, 
                                     endyear={endyear}, 
                                     registrationkey='{api_key_to_show}', 
                                     return_logs=True)
        
            """        
            st.code(python_script, language="python")

        # Code example for retrieving metadata            
        with tab2:
            python_script = f"""
            import pandas as pd
            from py_bls_api import get_surveys, get_survey_metadata, get_data_preview, get_seriesid_metadata, get_popular_seriesids
    
            # Returns a dictionary of BLS surveys supported by py-bls-api.
            surveys = get_surveys()
               
            # Returns a dictionary containing metadata for a given survey
            survey_metadata = get_survey_metadata('{survey_name}')
            
            # Returns a dataframe containing a data preview for a given survey        
            data_preview = get_data_preview('{survey_name}')
            
            # Returns a dataframe containing Series ID metadata for a given survey.
            seriesid_metadata = get_seriesid_metadata('{survey_name}')        
            
            # Returns a list of popular BLS Series IDs for a given survey.
            popular_seriesids = get_popular_seriesids('{survey_name}', '{api_key_to_show}')  
            
            """        
            st.code(python_script, language="python")       

        # Display license information           
        with tab3:
            st.markdown(
                """
                <div style="
                background-color: #fff3cd;
                color: #856404;
                padding: 10px 15px;
                border-left: 5px solid #ffc107;
                border-radius: 5px;
                font-size: 16px;">
                    
                Non-Commercial License for [py-bls-api](https://github.com/coding-with-chris/py-bls-api/)
    
                Copyright (c) 2025 Christopher Morris
                
                Permission is hereby granted to any person obtaining a copy of this software and associated documentation files (the “Software”), to use the Software for personal, educational, or non-commercial research purposes only, subject to the following conditions:
                
                <b>Non-Commercial Use Only</b>
                
                This Software may not be used, in whole or in part, for commercial purposes. Commercial purposes include, but are not limited to, selling the Software, integrating it into paid services or products, or using it to generate revenue directly or indirectly.
                
                <b>No Modification or Redistribution</b>
                
                You may not modify, distribute, sublicense, or rebrand the Software. You may fork the repository for personal or educational use, but redistribution in any form, modified or unmodified, is prohibited without prior written permission.
                
                <b>Attribution Required</b>
                
                Any use of this Software must include clear attribution to the original author and this GitHub repository. You may not claim authorship or imply endorsement by the original author.
                
                <b>No Warranty</b>
                
                The Software is provided "as is", without warranty of any kind, express or implied. In no event shall the author be liable for any claim, damages, or other liability arising from the use of the Software.
                
                <b>Termination</b>
                
                Any breach of this license automatically terminates your rights under it.
                
                </div>
                """, 
                unsafe_allow_html=True
            )
    

def main():
    """
    Main function that orchestrates the BLS API Explorer workflow.
    """        
    # Setup the UI components
    configure_user_interface()
    display_app_header()
    create_sidebar()        

    # Load and display survey selection    
    survey = load_surveys()
    survey, survey_name = create_survey_picklist(survey)

    # Cache metadata to improve performance
    @st.cache_data
    def load_metadata(survey):
        return get_survey_metadata(survey)

    # Load metadata and display information
    metadata = load_metadata(survey_name)
    display_description(metadata['survey_description'])
    minimum_year = metadata['survey_minimum_year']
    maximum_year = metadata['survey_maximum_year']
    display_data_preview(metadata)
    
    # Prepare and display the series selection and API query builder    
    series_picklist = prepare_series_picklist(metadata)
    submitted, registrationkey, startyear, endyear, seriesids = display_api_query_builder(series_picklist, minimum_year, maximum_year)

    # Handle form submission
    if submitted:
        with st.spinner("Fetching data from the BLS API..."):
            # Make API request            
            data, log = get_bls_data(seriesids=seriesids, 
                                     catalog=True, 
                                     startyear=startyear, 
                                     endyear=endyear, 
                                     registrationkey=registrationkey, 
                                     return_logs=True)

            # Store results in session state for persistence
            st.session_state["bls_data"] = data
            st.session_state["bls_log"] = log
            st.session_state["bls_params"] = {
                "seriesids": seriesids,
                "startyear": startyear,
                "endyear": endyear,
                "registrationkey": registrationkey,
                "survey_name": survey_name,
                "survey": survey
            }
            
        # Trigger balloons animation on successful data fetch            
        st.session_state["show_balloons"] = True

    # Display results if data exists in session state
    if "bls_data" in st.session_state and isinstance(st.session_state["bls_data"], pd.DataFrame):
        display_output(
            st.session_state["bls_data"],
            st.session_state.get("bls_log", pd.DataFrame()),
            st.session_state["bls_params"]["survey"]
        )
        display_code(
            st.session_state["bls_data"],            
            st.session_state["bls_params"]["seriesids"],
            st.session_state["bls_params"]["startyear"],
            st.session_state["bls_params"]["endyear"],
            st.session_state["bls_params"]["registrationkey"],
            st.session_state["bls_params"]["survey_name"]
        )
        
main()        

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_timeline import timeline
from plotly_calplot import calplot
import plotly.graph_objects as go
import datetime
from datetime import datetime as dt
from collections import Counter
import re
import requests
from io import StringIO

# Set page configuration
st.set_page_config(
    page_title="Client Journey Map",
    layout="wide"
)

def fetch_csv_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def plot_housing_periods():
    # Reading the CSV data
    data_csv = fetch_csv_from_url('https://raw.githubusercontent.com/qawaki/tt/main/housed_date.csv')
    data_df = pd.read_csv(pd.StringIO(data_csv))

    # Parsing the data using the correct column names and calculating the total days housed
    parsed_data = []
    total_days_housed = {}

    for _, row in data_df.iterrows():
        client = row['client']
        date_ranges_str = row['housed_date']

        if not isinstance(date_ranges_str, str):  # Check if the value is a valid string
            continue

        date_ranges = date_ranges_str.split(',')
        total_days = 0
        for r in date_ranges:
            start_date, end_date = r[:10], r[11:]
            start, end = dt.fromisoformat(start_date), dt.fromisoformat(end_date)

            days = (end - start).days + 1  # Including both start and end date
            total_days += days

            parsed_data.append({
                "Client": client,
                "Start": start,
                "End": end,
                "Days": days
            })

        total_days_housed[client] = total_days

    # Convert parsed data to DataFrame
    parsed_df = pd.DataFrame(parsed_data)


    # Plotting
    fig = px.timeline(parsed_df, x_start="Start", x_end="End", y="Client", color="Client", title="Housing Periods")
    fig.update_yaxes(categoryorder="total ascending")
    return fig, total_days_housed

def plot_visits_from_csv(csv_path):
    # Read the data from the CSV file
    data_csv = fetch_csv_from_url(csv_path)
    data = pd.read_csv(pd.StringIO(data_csv))
    
    # Drop rows with NaN values in the 'Reason' or 'Visits' columns
    cleaned_data = data.dropna(subset=['Reason', 'Visits'])

    # Group by 'Reason' and sum the 'Visits' to get the total number of visits for each reason
    grouped_data = cleaned_data.groupby('Reason').sum()['Visits'].reset_index()

    # Create a bar chart using Plotly with different colors for each reason
    fig = px.bar(grouped_data, 
                 x='Reason', 
                 y='Visits', 
                 title='Programs Over Number Accessed Chart', 
                 color='Reason',
                 labels={'Reason': 'Programs', 'Visits': 'Number Accessed'},
                 height=600,
                 width=900)
    
    return fig


def plot_radar_chart_for_patient(patient_id, data):

    # Filter data for the selected patient
    patient_data = data[data['Client'] == patient_id]
    
    # Create the radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=patient_data['Visits'],
        theta=patient_data['Reason'],
        fill='toself',
        name='Number of Visits'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, patient_data['Visits'].max() + 2]
            )),
        showlegend=True
    )

    return fig

def generate_patient_visits_radar(csv_path, selected_client_name):
    # 1. Load the data from the CSV file
    data = pd.read_csv(csv_path)

    # Create a mapping of patient.ID to Client names
    id_to_name_mapping = {
        8858: "Nathan Lunn (Adrian)",
        16555: "Kelly Baswick",
        52896: "Less Four Horns",
        66275: "Darlene Auger",
        72287: "Dawson Jarvis",
        73033: "Patricia Chapman (Dawn)",
        74545: "David Thok (Kuany)",
        75724: "Erin Burris (Isabelle)",
        76579: "Michael Goodfeather (Roy)",
        77463: "Graham Miles (Douglas)",
        84999: "Courtney Bird",
        85880: "Carrie Saikkonen (Lynn)"
    }

    # Add a new column for client names
    data['Client'] = data['Patient.ID'].map(id_to_name_mapping)

    cleaned_data = data.dropna(subset=['Reason', 'Visits'])
    client_grouped_data = cleaned_data.groupby(['Client', 'Reason']).sum()['Visits'].reset_index()

    # Generate the radar chart for the selected client name
    fig = plot_radar_chart_for_patient(selected_client_name, client_grouped_data)

    return fig


def generate_service_usage_pie_chart(selected_client):
    # Load the data from the CSV file
    data_csv = fetch_csv_from_url('https://raw.githubusercontent.com/qawaki/tt/main/storage.csv')
    data = pd.read_csv(pd.StringIO(data_csv))
    
    # Filter data for the selected client
    client_data = data[data['Client'] == selected_client]
    
    # Sum the usage of each service for the selected client
    service_totals = client_data.sum(numeric_only=True)
    
    # Create the pie chart
    fig = px.pie(data_frame=service_totals, names=service_totals.index, values=service_totals.values, hole=0.3, title=f"Storage Usage of {selected_client}")
    
    return fig

def generate_service_usage_stacked_bar_chart(selected_client):
    # Load the data from the CSV file
    data_csv = fetch_csv_from_url('https://raw.githubusercontent.com/qawaki/tt/main/storage.csv')
    data = pd.read_csv(pd.StringIO(data_csv))
    
    # Filter data for the selected client
    client_data = data[data['Client'] == selected_client]
    
    # Pivot the data to have services as columns, clients as rows, and usage as values
    client_data_pivot = client_data.melt(id_vars=['Client'], var_name='Service', value_name='Usage')
    
    # Create the stacked bar chart
    fig = px.bar(client_data_pivot, x='Client', y='Usage', color='Service', title=f"Bars and Logs Data for {selected_client}")
    
    return fig


def display_main_page():

    st.title("Client Dashboard")

    csv_path = 'https://raw.githubusercontent.com/qawaki/tt/main/bar_stack.csv'


    fig, total_days_housed = plot_housing_periods()

    # Adjusting the figure size using the sidebar slider values
    chart_width = st.sidebar.slider("Select Housing Chart Width", 300, 1500, 800)
    chart_height = st.sidebar.slider("Select Housing Chart Height", 300, 1000, 450)
    fig.update_layout(autosize=True, paper_bgcolor= "#262730", plot_bgcolor="#262730", width=chart_width, height=chart_height)

    # Determine the ratio of the Gantt chart width to the total page width
    total_page_width = 1500  # Assuming a typical total page width, adjust as needed
    chart_ratio = chart_width / total_page_width
    table_ratio = 1 - chart_ratio

    # Create two columns: one for the Gantt chart and one for the table
    col1, col2 = st.columns([0.8, 0.2])

    # Display the Gantt chart in the left column
    col1.plotly_chart(fig, use_container_width= True)
    
    # Create a DataFrame from total_days_housed and display it as a table in the right column
    df_total_days = pd.DataFrame.from_dict(total_days_housed, orient='index', columns=['Total Days Housed']).reset_index()
    df_total_days.columns = ['Client', 'Total Days Housed']
    col2.write(df_total_days, use_container_width= True)

   # Create two columns: one for the bar plot and one for the radar chart
    col3, col4 = st.columns([chart_ratio, table_ratio])

    # Display the bar plot in the first column
    visits_by_reason_chart = plot_visits_from_csv(csv_path)
    col3.plotly_chart(visits_by_reason_chart, use_container_width=True)

    id_to_name_mapping = {
    8858: "Nathan Lunn (Adrian)",
    16555: "Kelly Baswick",
    52896: "Less Four Horns",
    66275: "Darlene Auger",
    72287: "Dawson Jarvis",
    73033: "Patricia Chapman (Dawn)",
    74545: "David Thok (Kuany)",
    75724: "Erin Burris (Isabelle)",
    76579: "Michael Goodfeather (Roy)",
    77463: "Graham Miles (Douglas)",
    84999: "Courtney Bird",
    85880: "Carrie Saikkonen (Lynn)"
}

    # Create the selectbox in the second column
    data = pd.read_csv(csv_path)
    cleaned_data = data.dropna(subset=['Reason', 'Visits'])
    client_names = cleaned_data['Patient.ID'].map(id_to_name_mapping).unique()
    selected_client_name = col4.selectbox('Select Client:', client_names)


    col4.plotly_chart(generate_patient_visits_radar(csv_path, selected_client_name), use_container_width=True)
    # Column creation
    col5, col6 = st.columns([chart_ratio, table_ratio])

    # Create the select box in col5
    data = pd.read_csv('https://raw.githubusercontent.com/qawaki/tt/main/storage.csv')
    
    client_options = data['Client'].unique().tolist()
    selected_client_for_pie = col5.selectbox('Select Client :', client_options)

    # Generate and display the pie chart below the select box in col5
    pie_chart = generate_service_usage_pie_chart(selected_client_for_pie)
    col5.plotly_chart(pie_chart, use_container_width=True)

    # Col6 stacked bar plot
    selected_client_for_bar = col6.selectbox('Select Client Bar:', client_options)
    bar_chart = generate_service_usage_stacked_bar_chart(selected_client_for_bar)
    col6.plotly_chart(bar_chart, use_container_width=True)
    

def generate_word_treemap(csv_path):
    # Read the client file
    data_csv = fetch_csv_from_url(csv_path)
    df = pd.read_csv(pd.StringIO(data_csv))

    # Extract the 'text' column
    text_data = " ".join(df['text'].tolist())

    # Clean the text and split into words
    words = re.findall(r'\w+', text_data.lower())

    stopwords = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "my", "myself", "nor", "of", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "she'd", "she'll",
    "she's", "should", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "we'd", "we'll", "we're",
    "we've", "were", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "would", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "less",
    "writer", "acw", "will", "go", "s", "a", "went", "well", "not", "get", "said", "going", "ACW", "no", "also", "off", "told", "come", "came", "t", "1",
    "c", "above", "afterwards", "again", "all", "almost", "alone", "along", "already", "also", "although", "always",
    "among", "amongst", "amoungst", "amount", "another", "anyhow", "anyone", "anything", "anyway", "around",
    "became", "because", "become", "becomes", "becoming", "been", "beforehand", "behind", "being", "beside",
    "besides", "between", "beyond", "bill", "both", "bottom", "but", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "describe", "detail", "do", "done", "due", "during", "each", "eg", "eight", "either",
    "eleven", "else", "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone", "everything",
    "everywhere", "except", "few", "fifteen", "fifty", "fill", "find", "fire", "first", "five", "for", "former",
    "formerly", "forty", "found", "four", "from", "front", "full", "further", "get", "give", "go", "had", "has",
    "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself",
    "him", "himself", "his", "how", "however", "hundred", "ie", "inc", "indeed", "interest", "into", "is", "it",
    "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself",
    "name", "namely", "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone", "nor", "not",
    "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other", "others",
    "otherwise", "our", "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps", "please", "put", "rather",
    "re", "same", "see", "seem", "seemed", "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime", "sometimes",
    "somewhere", "still", "such", "system", "take", "ten", "than", "that", "the", "their", "them", "themselves", "then",
    "thence", "there", "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "thick", "thin",
    "third", "this", "those", "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "top",
    "toward", "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us", "very", "via", "was",
    "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose",
    "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves", "cm", "im",
    "like", "m", "ab", "ll", "Carrie", "Saikkonen", "(Lynn)", "Colin", "Anderson", "(D)", "Courtney", "Bird", "Darlene", "Auger", "David", 
    "Thok", "(Kuany)", "Dawson", "Jarvis", "Erin", "Burris", "(Isabelle)", "Graham", "Miles", "(Douglas)", "Kelly", "Baswick",
    "Kual", "Kual", "(Kual)", "Lambert", "MedicineTraveller", "Less", "Four", "Horns", "Michael", "Goodfeather", "(Roy)",
    "Nathan", "Lunn", "(Adrian)", "Patricia", "Chapman", "(Dawn)", "carrie", "saikkonen", "(lynn)", "colin", "anderson", "(d)", "courtney",
    "bird", "darlene", "auger", "david", "thok", "(kuany)", "dawson", "jarvis", "erin", "burris", "(isabelle)", "graham",
    "miles", "(douglas)", "kelly", "baswick", "kual", "kual", "(kual)", "lambert", "medicinetraveller", "less",
    "four", "horns", "michael", "goodfeather", "(roy)", "nathan", "lunn", "(adrian)", "patricia", "chapman", "(dawn)", "client", "clients", 
    "anisa", "armstrong", "able", "leslie", "les", "floor", "victoria", "diandra", "called", "asked", "back", "later"
])
    # Detect client names by looking for consecutive capitalized words
    # This is a simple heuristic and may not catch all client names.
    

    # Remove stopwords from the list of words
    filtered_words = [word for word in words if word not in stopwords and not re.search(r'\d', word)]

    # Count the frequency of each word
    word_counts = Counter(filtered_words)

    # Sort the words by frequency and get the top 50
    top_50_words = word_counts.most_common(50)

    # Extract words and their counts for the treemap
    top_words = [word[0] for word in top_50_words]
    top_counts = [word[1] for word in top_50_words]

    # Create a treemap using plotly for the top 50 words
    fig = px.treemap(names=top_words, path=[top_words], values=top_counts, title= "Frequent Fifty Words In Log")
    
    return fig

def fetch_json_from_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
    
def display_client_journey():
    # List of clients
    clients = [
        'Carrie Saikkonen (Lynn)', 'Colin Anderson (D)', 'Courtney Bird', 'Darlene Auger', 'David Thok (Kuany)',
    'Dawson Jarvis', 'Erin Burris (Isabelle)', 'Graham Miles (Douglas)', 'Kelly Baswick', 'Kual Kual (Kual)',
    'Lambert MedicineTraveller', 'Less Four Horns', 'Michael Goodfeather (Roy)', 'Nathan Lunn (Adrian)',
    'Patricia Chapman (Dawn)'
    ]

    # Selectbox for clients
    selected_client = st.selectbox('Search or Select client', clients)
    
    timeline_data_url = f'https://raw.githubusercontent.com/qawaki/tt/main/{selected_client}.json'
    timeline_data = fetch_json_from_url(timeline_data_url)
    # Read timeline data for the selected client
    #timeline_data = ''
    #with open(f'https://raw.githubusercontent.com/qawaki/tt/main/{selected_client}.json', 'r') as f:
        #timeline_data = f.read()

    # Render client journey map timeline
    st.write("# From Arrival to Progress: A Holistic View of The DI Services and Outcomes")
    st.markdown('---')
    st.write("## Client Journey Map Timeline")
    timeline(timeline_data, height=800)

    st.empty()

    # Mapping between client name and CSV file path
    csv_files = {
        'Carrie Saikkonen (Lynn)': 'https://raw.githubusercontent.com/qawaki/tt/main/carrie.csv',
    'Colin Anderson (D)': 'https://raw.githubusercontent.com/qawaki/tt/main/colin.csv',
    'Courtney Bird': 'https://raw.githubusercontent.com/qawaki/tt/main/courtney.csv',
    'Darlene Auger':'https://raw.githubusercontent.com/qawaki/tt/main/darlene.csv', 
    'David Thok (Kuany)':'https://raw.githubusercontent.com/qawaki/tt/main/david.csv',
    'Dawson Jarvis':'https://raw.githubusercontent.com/qawaki/tt/main/dawson.csv', 
    'Erin Burris (Isabelle)':'https://raw.githubusercontent.com/qawaki/tt/main/erin.csv',
    'Graham Miles (Douglas)':'https://raw.githubusercontent.com/qawaki/tt/main/graham.csv', 
    'Kelly Baswick':'https://raw.githubusercontent.com/qawaki/tt/main/kelly.csv', 
    'Kual Kual (Kual)':'https://raw.githubusercontent.com/qawaki/tt/main/kual.csv',
    'Lambert MedicineTraveller':'https://raw.githubusercontent.com/qawaki/tt/main/lambert.csv', 
    'Less Four Horns':'https://raw.githubusercontent.com/qawaki/tt/main/less.csv', 
    'Michael Goodfeather (Roy)':'https://raw.githubusercontent.com/qawaki/tt/main/michael.csv', 
    'Nathan Lunn (Adrian)':'https://raw.githubusercontent.com/qawaki/tt/main/nathan.csv',
    'Patricia Chapman (Dawn)':'https://raw.githubusercontent.com/qawaki/tt/main/patricia.csv',
    }

    # Get the CSV file path for the selected client
    csv_file = csv_files[selected_client]

    # Load sleep data
    df = pd.read_csv(csv_file)

    # Convert the 'Sleep' column to datetime format
    df['Sleep'] = pd.to_datetime(df['Sleep']).dt.normalize()

    # Add artificial min and max rows
    df = df.append({"Sleep": df["Sleep"].min() - pd.Timedelta(days=1), "Program": "day", "value": 1}, ignore_index=True)
    df = df.append({"Sleep": df["Sleep"].max() + pd.Timedelta(days=1), "Program": "night", "value": 60}, ignore_index=True)

    # Create a new column 'value' based on 'Program' column
    df['value'] = df['Program'].apply(lambda x: 1 if isinstance(x,str) and 'day' in x.lower() else 30)

    # Aggregate the data by date
    df_agg = df.groupby('Sleep').sum().reset_index()

    # Modify 'value' based on its current value
    df_agg['value'] = df_agg['value'].apply(lambda x: 15 if x == 31 else (30 if x > 35 else x))

    st.markdown('---')


    height = st.slider('Select Calendar Height', 300, 1000, 450)

    # Create a calplot figure
    fig = calplot(
        df_agg,
        x="Sleep",
        y="value",
        dark_theme=True,
        years_title=True,
        gap=2,
        name="Sleep",
        colorscale=[[0, '#2596BE'], [0.5, '#FFE0B3'], [1, '#FF9800']],
        month_lines_width=2,
        month_lines_color="#fff"
    )

    fig.update_layout(
        autosize=True,
        width=800,
        height=height
    )

    st.write("## Sleep Check-ins")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('---')

    st.write("## Word Treemap")

    # Assuming similar mapping as timeline data
    word_treemap_data_path = f'https://raw.githubusercontent.com/qawaki/tt/main/{selected_client}.csv'
    fig = generate_word_treemap(word_treemap_data_path)
    st.plotly_chart(fig, use_container_width=True)



# Sidebar navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to:", ["Client Dashboard", "Client Journey Map"])

if selection == "Client Dashboard":
    display_main_page()
elif selection == "Client Journey Map":
    display_client_journey()

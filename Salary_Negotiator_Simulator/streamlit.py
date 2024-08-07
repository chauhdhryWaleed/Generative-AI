import streamlit as st
import requests
import json
import plotly.graph_objects as go
import re

# Define a custom color palette
COLOR_PALETTE = {
    'primary': '#1E88E5',
    'secondary': '#FFC107',
    'background': '#F5F5F5',
    'text': '#212121',
    'low': '#FF5252',
    'medium': '#FFA000',
    'high': '#4CAF50',
    'zero': '#FF5252',
    'non_zero': '#4CAF50'
}

# Function to get all chat logs with IDs and names
# @st.cache_data(ttl=600)
def get_all_sessions():
    url = 'http://localhost:5000/chat_logs'  # The backend route is still named chat_logs
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('sessions', [])  # Changed from 'chat_logs' to 'sessions'
    else:
        st.error(f"Failed to retrieve sessions. Status code: {response.status_code}")
        return []

# Function to get feedback from API by feedback ID
@st.cache_data(ttl=600)
def get_session_result(session_id):
    url = f'http://localhost:5000/session/{session_id}/result'
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        return result.get('feedback'), result.get('score')
    else:
        st.error(f"Failed to retrieve session result. Status code: {response.status_code}")
        return None, None
# @st.cache_data(ttl=600)
def get_chat_history(session_id):
    url = f'http://localhost:5000/session/{session_id}/history'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('history', [])
    else:
        st.error(f"Failed to retrieve chat history. Status code: {response.status_code}")
        return []
    

def send_message(session_id, message):
    url = f'http://localhost:5000/session/{session_id}/message'
    response = requests.post(url, json={"message": message})
    if response.status_code == 200:
        return response.json().get('response', '')
    else:
        st.error(f"Failed to send message. Status code: {response.status_code}")
        return ''

# Function to extract metrics scores and reasoning
def extract_metrics_scores_and_reasoning(text):
    pattern = re.compile(r'\d+\.\s+\*\*(.*?)\*\*:\s+(\d+)/10\s+\*\s+Reasoning:\s+(.*?)(?=\n\d+\.|\n\*\*Suggestions for Improvement\*\*|$)', re.DOTALL)
    matches = pattern.findall(text)
    return [(match[0], int(match[1]), match[2].strip()) for match in matches]



# Function to extract suggestions
def extract_suggestions(text):
    start_pattern = re.compile(r'\*\*Suggestions for Improvement\*\*:', re.IGNORECASE)
    start_match = start_pattern.search(text)
    
    if not start_match:
        return []

    start_index = start_match.end()
    relevant_text = text[start_index:].strip()

    suggestions = []
    pattern = re.compile(r'(\d+)\.\s+\*\*(.*?)\*\*:\s+(.*?)(?=\n\d+\.|\Z)', re.DOTALL)
    matches = pattern.findall(relevant_text)
    
    for match in matches:
        number = match[0]
        heading = match[1].strip()
        description = match[2].strip()
        suggestions.append((number, heading, description))

    return suggestions

# Function to get color based on score
def get_score_color(score):
    if score == 0:
        return COLOR_PALETTE['low']
    else:
        return COLOR_PALETTE['high']
    
def get_score_color1(score):
    if score <=5:
        return COLOR_PALETTE['low']
    elif score <= 8:
        return COLOR_PALETTE['medium']
    else:
        return COLOR_PALETTE['high']
    
def get_totalscore_color(score):
    if score <= 10:
        return COLOR_PALETTE['low']
    elif score <= 20:
        return COLOR_PALETTE['medium']
    else:
        return COLOR_PALETTE['high']

def extract_detailed_score(score_text):
    criteria = re.findall(r'(\d+\.\s+(.*?):)\s+(.*?)\(Score:\s+(\d+)\s+points\)', score_text, re.DOTALL)

    # Convert the extracted data into the format expected by the rest of the code
    formatted_criteria = [(item[1].strip(), int(item[3]), item[2].strip()) for item in criteria]

    # Calculate total score by summing individual scores
    total_score = sum(score for _, score, _ in formatted_criteria)

    return formatted_criteria, total_score

def send_message_callback():
    if st.session_state.user_message and not st.session_state.get('offer_accepted', False):
        assistant_response = send_message(st.session_state.session_id, st.session_state.user_message)
        if assistant_response:
            st.session_state.chat_history.append({'role': 'user', 'content': st.session_state.user_message})
            st.session_state.chat_history.append({'role': 'assistant', 'content': assistant_response})
            
            # Clear the input by setting it to an empty string
            st.session_state.user_message = ""
            
            # Check if the offer was accepted
            if "OFFER WAS ACCEPTED" in assistant_response:
                st.session_state.offer_accepted = True
                st.rerun()  # Rerun to update the UI
            else:
                st.rerun()  # Rerun to update the chat display



# Main function to render Streamlit app
def main():
    st.set_page_config(page_title="Negotiation Skills Feedback", layout="wide")

    # Custom CSS
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {COLOR_PALETTE['background']};
            color: {COLOR_PALETTE['text']};
        }}
        .main {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            color: {COLOR_PALETTE['primary']};
        }}
        .metric-card, .suggestion-card {{
            animation: fadeIn 0.5s ease-in-out;
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title("Negotiation Skills Feedback")

    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Select Feedback", "Create New Session", "Chat Log","Evaluation Metrics", "Suggestions for Improvement", "Detailed Score Breakdown"])

    
    if page == "Create New Session":
        st.header("Create New Session")
        with st.form("create_session_form"):
            session_name = st.text_input("Session Name")
            job_roles = ["office_boy", "software_engineer", "senior_software_engineer", "ai_engineer", "ml_engineer"]
            job_role = st.selectbox("Job Role", job_roles)
            prompt = st.text_area("Prompt", value="")
            submitted = st.form_submit_button("Create Session")

            if submitted:
                st.session_state.offer_accepted = False
                data = {
                    "name": session_name,
                    "job_role": job_role,
                    "prompt": prompt
                }
                response = requests.post("http://localhost:5000/session", json=data)
                if response.status_code == 201:
                    session_data = response.json()
                    session_id = session_data['session_id']
                    st.success(f"Session '{session_name}' created successfully!")

                    # Initialize session state for chat history
                    st.session_state.chat_history = get_chat_history(session_id)
                    st.session_state.session_id = session_id
                    st.session_state.session_name = session_name

        if 'session_id' in st.session_state:
            st.header(f"Chat with LLM for Session: {st.session_state.session_name}")

            # Display the chat history
            for message in st.session_state.chat_history:
                role = message['role']
                content = message['content']
                
                st.markdown(f"""
                    <div style="background-color: {'#E1F5FE' if role == 'user' else '#F1F8E9'}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <strong style="color: {'#0277BD' if role == 'user' else '#33691E'};">{role.capitalize()}:</strong>
                        <p style="margin: 5px 0 0 0;">{content}</p>
                    </div>
                """, unsafe_allow_html=True)

            # Check if offer has been accepted
            if st.session_state.get('offer_accepted', False):
                st.success("Offer accepted! You can now view your feedback.")
                # send_message(st.session_state.session_id,"I accept your offer")
                if st.button("View Feedback"):
                    feedback, score = get_session_result(st.session_state.session_id)
                    
                    if feedback is not None and score is not None:
                        st.session_state.feedback_text = feedback
                        st.session_state.score = score
                        st.session_state.selected_id = st.session_state.session_id
                        st.session_state.selected_name = st.session_state.session_name
                        st.rerun()  # Rerun to show the feedback page
            else:
                # Only show the input field if the offer hasn't been accepted
                user_message = st.text_input("Your message:", key="user_message", on_change=send_message_callback)
    if page == "Select Feedback":
        all_sessions = get_all_sessions()
        st.header("Select Session to View")
        if not all_sessions:
            st.warning("No sessions available.")
        else:
            session_options = {f"{session['name']} ": session['id'] for session in all_sessions}
            selected_option = st.selectbox("Choose a session:", list(session_options.keys()))

            if selected_option:
                selected_id = session_options[selected_option]
                selected_name = selected_option.split(" (ID: ")[0]

                if st.button("View Feedback"):
                    st.session_state.selected_id = selected_id
                    st.session_state.selected_name = selected_name
                    feedback, score = get_session_result(selected_id)
                    if feedback is not None and score is not None:
                        st.session_state.feedback_text = feedback
                        st.session_state.score = score
                        st.success(f"Feedback loaded for session: {selected_name}")
                    else:
                        st.error("Failed to load feedback for the selected session.")
            else:
                st.warning("Please select a session.")

    if 'selected_id' in st.session_state and 'feedback_text' in st.session_state:
        feedback_text = st.session_state.feedback_text
        score_text = st.session_state.score
        if feedback_text:
            metrics_data = extract_metrics_scores_and_reasoning(feedback_text)
            suggestions = extract_suggestions(feedback_text)
            detailed_score, total_score = extract_detailed_score(score_text)

            if page == "Evaluation Metrics":
                st.header(f"Evaluation Metrics for Session: {st.session_state.selected_name}")

                # Create a radar chart
                categories = [metric for metric, _, _ in metrics_data]
                scores = [score for _, score, _ in metrics_data]

                fig = go.Figure(data=go.Scatterpolar(
                    r=scores,
                    theta=categories,
                    fill='toself',
                    line_color=COLOR_PALETTE['primary']
                ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10]),
                        bgcolor=COLOR_PALETTE['background']
                    ),
                    paper_bgcolor=COLOR_PALETTE['background'],
                    plot_bgcolor=COLOR_PALETTE['background'],
                    font_color=COLOR_PALETTE['text'],
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

                # Display metrics with new style
                for metric, score, reasoning in metrics_data:
                    with st.container():
                        st.markdown(f"""
                            <div class="metric-card">
                                <h3 style="color: {COLOR_PALETTE['primary']};">{metric}</h3>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <p style="flex: 1;">{reasoning}</p>
                                    <div style="
                                        background-color: {get_score_color1(score)};
                                        color: white;
                                        font-size: 24px;
                                        font-weight: bold;
                                        padding: 10px 20px;
                                        border-radius: 5px;
                                        margin-left: 20px;
                                    ">
                                        {score}/10
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

            elif page == "Suggestions for Improvement":
                st.header(f"Suggestions for Improvement for Session: {st.session_state.selected_name}")
            
                if not suggestions:
                    st.write("Raw feedback text:", feedback_text)  # Debugging
                for number, heading, description in suggestions:
                    st.markdown(f"""
                        <div class="suggestion-card">
                            <h3 style="color: {COLOR_PALETTE['secondary']};">{number}. {heading}</h3>
                            <p>{description}</p>
                        </div>
                    """, unsafe_allow_html=True)

            elif page == "Detailed Score Breakdown":
                st.header(f"Detailed Score Breakdown for Session: {st.session_state.selected_name}")

                # Display the total score at the top
                st.markdown(f"""
                    <div style="background-color: {get_totalscore_color(total_score)}; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h2 style="color: white; margin: 0;">Total Score: <span style="font-size: 32px;">{total_score}/30</span></h2>
                    </div>
                """, unsafe_allow_html=True)

                # Display criteria in a grid
                col1, col2, col3 = st.columns(3)
                for idx, (criterion, score, explanation) in enumerate(detailed_score):
                    with [col1, col2, col3][idx % 3]:
                        st.markdown(f"""
                            <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <h3 style="color: {COLOR_PALETTE['primary']}; margin-top: 0;">{criterion}</h3>
                                <p>{explanation}</p>
                                <div style="
                                    background-color: {get_score_color(score)};
                                    color: white;
                                    font-size: 24px;
                                    font-weight: bold;
                                    padding: 5px 10px;
                                    border-radius: 5px;
                                    display: inline-block;
                                ">
                                    {score} points
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

            # Modify the Chat Log section
            elif page == "Chat Log":
                st.header(f"Chat Log for Session: {st.session_state.selected_name}")

                if 'selected_id' in st.session_state:
                    chat_history = get_chat_history(st.session_state.selected_id)

                    if chat_history:
                        for message in chat_history:
                            role = message.get('role', 'User')
                            content = message.get('content', '')
                            
                            if role.lower() == 'user':
                                st.markdown(f"""
                                    <div style="background-color: #E1F5FE; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                                        <strong style="color: #0277BD;">User:</strong>
                                        <p style="margin: 5px 0 0 0;">{content}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                    <div style="background-color: #F1F8E9; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                                        <strong style="color: #33691E;">Assistant:</strong>
                                        <p style="margin: 5px 0 0 0;">{content}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("No chat history available for this session.")
                else:
                    st.warning("Please select a session first.")
if __name__ == "__main__":
    main()

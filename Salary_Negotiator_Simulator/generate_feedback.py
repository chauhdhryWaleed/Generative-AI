import requests
class NegotiationSimulator:
    def __init__(self):
        self.chat_log1 = []

    def read_chat_log(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def load_chat_log_from_file(self, filename):
        chat_log1 = []
        current_role = None
        current_message = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                parts = line.split(': ', 1)
                if len(parts) == 2:
                    # If we have a role and message from previous lines, add it to the chat log
                    if current_role and current_message:
                        chat_log1.append((current_role, '\n'.join(current_message)))
                        current_message = []
                    
                    current_role, message = parts
                    current_message.append(message)
                else:
                    # This line is a continuation of the previous message
                    current_message.append(line)
        
        # Add the last message if there is one
        if current_role and current_message:
            chat_log1.append((current_role, '\n'.join(current_message)))
        
        self.chat_log1 = chat_log1

        # print(self.format_chat_log1())

    def format_chat_log1(self):
        return "\n".join([f"{role} {message}" for role, message in self.chat_log1])
    
    def return_score(self, count):
        if count < 10:
            score = 1 + (count * 4 // 10)  # Scale from 1 to 5 based on count
        elif 10 <= count < 20:
            score = 6 + ((count - 10) * 2 // 10)  # Scale from 6 to 8 based on count
        else:
            score = 9 + ((count - 20) // 10)  # Scale from 9 to 10 based on count

        return min(score, 10)  # Ensure the score does not exceed 10

    def read_data(self):
        print("Inside read data")
        file_path = '3.1_ML2_NewAPI.txt'  # Replace with the actual path to your chat log file
        chat_log_content = self.read_chat_log(file_path)
        self.send_chat_log(chat_log_content)
    def generate_feedback(self,chat_log_content):
        
        
        # Store chat log content in self.chat_log1
        self.chat_log1 = [(entry['role'], entry['content']) for entry in chat_log_content]

        # Count the number of messages
        message_count = len(self.chat_log1)
        # Prepare prompt for feedback generation
        prompt = f"""
        Chat log:
        *********************************

        {chat_log_content}

        ********************************

        """

        sample_format = """
        Feedback on your negotiation skills:

        **Evaluation Metrics**

        1. **Effectiveness of the candidate's tactics**: [X]/10
                * Reasoning: [Brief explanation based on the chat log]

        2. **Communication clarity**: [X]/10
                * Reasoning: [Brief explanation based on the chat log]

        3. **Professionalism**: [X]/10
                * Reasoning: [Brief explanation based on the chat log]

        4. **Alignment with negotiation best practices**: [X]/10
                * Reasoning: [Brief explanation based on the chat log]

        5. **Negotiation duration**: [X]/10
                * Reasoning: [Brief explanation based on the chat log without mentioning number of messages]


        **Suggestions for Improvement**:

        1. [First suggestion with heading and reasoning]
        2. [Second suggestion with heading and reasoning]
        3. [Third suggestion with heading and reasoning]

        """

        system_prompt = f"""
        You are an expert in evaluating negotiation skills. Analyze the negotiation chat log and provide detailed feedback based on Evaluation Criteria given below:

        Evaluation Criteria:
        Provide SCORE against each metric OUT OF 10

        1. Effectiveness of the candidate's tactics:
        - Score 0-5 : If the candidate Shows basic understanding but fails to apply tactics effectively.
        - Score 6-8 : If the candidate Applies some effective tactics with good understanding, but with room for improvement.
        - Score 9-10  : If the candidate Uses advanced tactics effectively and strategically, showing a deep understanding of negotiation principles.

        2. Communication clarity:
        - Score 0-5 : If the candidate Communication is often unclear or confusing.
        - Score 6-8 : If the candidate Communicates clearly most of the time but may occasionally be vague.
        - Score 9-10 : If the candidate Communicates with exceptional clarity and precision, making points easily understood and persuasive.

        3. Professionalism:
        - Score 0-5 : If the candidate Displays unprofessional behavior or responses.
        - Score 6-8 : If the candidate Generally professional with minor lapses in etiquette or tone.
        - Score 9-10 : If the candidate Maintains a high level of professionalism throughout, exhibiting excellent etiquette and respect.

        4. Alignment with negotiation best practices:
        - Score 0-5 : If the Actions and decisions do not align well with established best practices.
        - Score 6-8 : If the Aligns with best practices in most areas but may miss key aspects.
        - Score 9-10 : If the Actions and decisions consistently align with best practices, showing thorough understanding and application.

        5. Negotiation duration:
            Messages Count = {message_count}
            -Score = {self.return_score(message_count)}

        **Critical Instructions:**
        1. Offer three specific, actionable suggestions for improvement based on the weakest areas identified in the evaluation.
        2. Evaluate Negotiation Duration based on Messages Count

        Use EXACTLY the following format for your feedback:

        ********************************

        {sample_format}

        ********************************

        Ensure that your evaluation strictly follows the Critical Instructions, scores each metric out of 10, and adheres to the specified guidelines. Failing to do so will result in a breach of company rules.
        """

        url = "your_Api_key"
        headers = {
            "Content-Type": "application/json"
        }
        formatted_history = [[],[]]
        data = {
            "system": system_prompt,
            "message": prompt,
            "history": formatted_history,  # Assuming chat_log1 is in the correct format
            "temperature": 0.5,
            "max_new_tokens": 600,
            "frequency_penalty": 0.65,  # Adjust as needed
            "num_ctx": 4000
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_json = response.json()
            assistant_response = response_json['response'].split('assistant\n')[-1].strip()
            
            return assistant_response
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Fallback to ollama if API fails

    def get_chat_log(self, id):
        url = f'http://localhost:5000/chat_log/{id}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['content']
        else:
            print(f"Failed to retrieve chat log. Status code: {response.status_code}")
            return None
    def feedback_to_file(self, feedback):
        filename = "FeedbackML1.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(feedback)
    def get_latest_chat_log_id(self):
        url = 'http://localhost:5000/latest_chat_log'  # Replace with your actual API endpoint


        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('id')
        else:
            print(f"Failed to retrieve the latest chat log ID. Status code: {response.status_code}")
            return None

    def send_feedback_to_api(self, chat_log_id, feedback):
        url = 'http://localhost:5000/feedback'  # Ensure this matches the Flask API endpoint
        data = {
            'chat_log_id': chat_log_id,
            'feedback': feedback
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 201:
            print(f"Feedback sent successfully for chat log ID: {chat_log_id}")
        else:
            print(f"Failed to send feedback. Status code: {response.status_code}")
        return response.json()['id']
    

    
    def get_feedback_from_api(self, feed_back_id):
        url = f'http://localhost:5000/feedback/{feed_back_id}'
        print(f"Sending GET request to: {url}")
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            feedback_data = response.json()
            # print(f"Feedback data received: {feedback_data}")
            return feedback_data.get('feedback', None)  # Use get() to handle missing keys
        else:
            print(f"Failed to retrieve feedback. Status code: {response.status_code}")
            return None
        
    def send_feedback_to_api_and_receive(self, chat_log_id, feedback):
        url = 'http://localhost:5000/feedbackGenerate_Return'  # Ensure this matches the Flask API endpoint
        data = {
            'chat_log_id': chat_log_id,
            'feedback': feedback
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 200: #meaning the feedback was successfully stored 
            feedback_data = response.json()
            # print(f"Feedback data received: {feedback_data}")
            return feedback_data.get('feedback', None)
        else:
            print(f"Failed to send and receive feedback. Status code: {response.status_code}")
            return None
        

    def send_chat_log(self,content):
        url = 'http://localhost:5000/chat_log'
        response = requests.post(url, json={'content': content})
        if response.status_code == 201:
            print(f"Chat log sent successfully. ID: {response.json()['id']}")
            return response.json()['id']  # Return the ID of the sent chat log for further operations if needed
        else:
            print(f"Failed to send chat log. Status code: {response.status_code}")

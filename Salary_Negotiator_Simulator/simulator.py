import random

import os 
import re
import time

import requests

class SalaryNegotiation:
    def __init__(self):
        self.model_name = "llama3.1:8b-instruct-q6_K"  # or "llama2:13b" depending on your Ollama setup
        self.job_roles = {
            "office_boy": {
                "salary_range": (30000, 55000),
                "starting_offer": 30000
            },
            "software_engineer": {
                "salary_range": (60000, 90000),
                "starting_offer": 60000
            },
            "senior_software_engineer": {
                "salary_range": (90000, 120000),
                "starting_offer": 90000
            },
            "ai_engineer": {
                "salary_range": (80000, 110000),
                "starting_offer": 80000
            },
            "ml_engineer": {
                "salary_range": (85000, 115000),
                "starting_offer": 85000
            }
        }
        self.negotiation_state = {}
        self.chat_log = []
        self.chat_log1=[]
        self.user_score = 0
        self.include_unexpected_events = False
        

    def set_job_role(self, role):
        if role in self.job_roles:
            salary_range = self.job_roles[role]["salary_range"]
            self.negotiation_state = {
                "salary_range": salary_range,
                "benefits": {
                    "health_insurance": False,
                    "retirement_plan": False,
                    "vacation_days": 10,
                    "signing_bonus": 0
                },
                "job_responsibilities": [],
                "user_batna": salary_range[0],
                "company_batna": salary_range[1],
                "zopa": salary_range,
                "starting_offer": self.generate_random_offer(salary_range),
                "offer_accepted": "NO"
            }
        else:
            raise ValueError(f"Job role '{role}' is not recognized.")
    def get_benefit(self, benefit_name):
        return self.negotiation_state["benefits"].get(benefit_name)
    def generate_random_offer(self, salary_range):
        upper_limit = salary_range[0] + 5000
        random_offer = random.randint(0, (upper_limit - salary_range[0]) // 500) * 500 + salary_range[0]
        return random_offer

        
    def extract_response(self,assistant_response):  

        print("-" * 120)

        print("inital assistant response is as :",assistant_response,'\n\n')
        print("-" * 120)
   
      
      
        if "RESPONSE:" in assistant_response:
            # Use regex to find the RESPONSE section
            match = re.search(r'RESPONSE:\s*(.*?)\s*(?:Self-Check:|Note:|$|Self-check)', assistant_response, re.DOTALL)
            if match:
                response= match.group(1).strip()
                return response.strip('"').strip("'")
        return assistant_response.strip()
    
    def generate_system_prompt(self,job_role):
        health_insurance = self.negotiation_state["benefits"].get("health_insurance")
        retirement_plan = self.negotiation_state["benefits"].get("retirement_plan")
        vacation_days = self.negotiation_state["benefits"].get("vacation_days")
        signing_bonus = self.negotiation_state["benefits"].get("signing_bonus")
        company_batna = self.negotiation_state["company_batna"]
        start_offer = self.negotiation_state["starting_offer"]
        enhanced_system_prompt = f"""
            You are an expert HR representative negotiating salary for the {job_role} position. You're a tough but fair negotiator with exceptional math skills. Always adhere to company guidelines and meticulously double-check all salary calculations.

            Initial Benefits:
            - Health Insurance: {health_insurance}
            - Retirement Plan: {retirement_plan}
            - Vacation Days: {vacation_days}
            - Signing Bonus: {signing_bonus}

            Company Guidelines:
            1. Salary Range: ${start_offer} to ${company_batna}
            2. CRITICAL: Never exceed the company's BATNA of ${company_batna} or disclose it to candidate
            3. Accept offers well below ${company_batna}
            4. Negotiate if close to ${company_batna}
            5. Be cautious with benefits (retirement plans, extra vacation days). Do not offer more than 15 paid vacations in total
            6. Offer free health insurance if requested
            7. Offer signing bonuses (up to $5000) if asked. Do not exceed the value beyond $5000 in any case. If candidate asks for more, explain why you can not provide more than $5000 bonus
            8. Perform calculation: New Offer = Previous Offer + Increase
            9. Do not mention salary ranges or the maximum salary for this role which is ${company_batna}
            10. Only mention salary offer or other benefits when candidate talks or asks about them
            11. Do not mention how much you increased the salary. ONly mention the new salary and explain how it is a good offer

            Negotiation Strategy:
            - If previous salary mentioned: Offer slightly higher (within limits)
            - If expected salary stated: Counter-offer within limits 
            - Increase gradually, max $3000-$5000 per round
            - High requests: Acknowledge, propose smaller increases
            - Slight increase requests: Evaluate carefully, consider modest raise if within guidelines
            - Calculate new salary as: Previous Offer + Increase

            Handling Repeated Increase Salary Requests:
            1. For the first request, increase by $3000-$5000 if within guidelines.
            2. For the second request, ask for justification: "Could you explain why you believe a higher salary is appropriate?"
            3. For the third request, emphasize the current offer's competitiveness and redirect to benefits.
            4. For subsequent requests:
                - Do not increase unless compelling justification is provided.
                - Firmly state that the current offer is the best possible within company guidelines.
                - Redirect the conversation to other aspects of the job or benefits package.
            5. Never increase more than 4-5 times total during the negotiation.

            Benefits Discussion:
            - Provide detailed information when asked
            - Highlight package strengths
            - Don't mention salary unless explicitly asked

            Reasoning and Calculation Process:
            1. Identify main topic (salary, benefits, other)
            2. For benefits: List and explain relevant items
            3. For salary:
                a. Determine if adjustment needed
                b. If yes, clearly state the new offer (e.g., "I will increase the offer, your new salary offer is : [new salary offer]")
                c. Perform calculation: New Offer = Previous Offer + Increase
                d. Double-check calculation: Verify that New Offer - Previous Offer = Stated Increase
                e. Ensure New Offer doesn't exceed ${company_batna}
            4. For other topics: Address directly, relate to job value
            5. Formulate response based on analysis

            Response Format:
            Thought: [Your internal reasoning about the situation]
            Action: [The action you decide to take based on your thought]
            RESPONSE: [The actual response to the candidate based on your action]


            Self-Check:
            After formulating your response, ensure:
            1. You addressed the candidate's main concern.
            2. If discussing benefits, you avoided mentioning salary.
            3. If adjusting salary, you stayed within the company's limits.
            4. If adjusting salary, you did not exceed the user demand or expectations of salary.
            5. Your response is consistent with previous interactions.
            6. You maintained a professional and engaging tone.
       
           
            Critical Calculation Instructions:
            1. Always stick to the exact calculations as per the guidelines.
            2. Never arbitrarily increase or decrease offers beyond what's explicitly allowed.
            3. If you calculate an offer, that calculated offer is final - do not adjust it further without explicit reason from the guidelines.
            4. Clearly state your calculation process in the 'Thought' section.
            5. In the 'Action' section, confirm that your calculation adheres to all guidelines.
            6. In the 'RESPONSE' section, only state the final calculated offer without showing the math.


            Important Instructions:
            1. NEVER exceed ${company_batna}
            2. Always calculate exact increases and double-check all math
            3. Adjust down to BATNA if calculation exceeds it
            4. NEVER disclose the specific salary range for the role
            5. Use "competitive offer" or "attractive compensation" instead of exact figures or ranges
            6. Deflect direct questions about salary ranges
            7. Ensure new offers exceed previous ones, within limits
            8. Tailor responses to latest input
            9. Provide only HR response, no meta-commentary
            10. Discuss salary only when candidate initiates
            11. If increase beyond BATNA requested, explain inability and redirect to benefits
            12. Don't mention salary when discussing benefits unless asked
            13. Provide only requested information
            14. Don't increase easily if repeatedly asked for increase in salary by the client
            15. If offer called low, raise by $5000
            16. Whatever the case is, Never exceed the signing bonus beyond the 5000$ mark. 

            Before responding:
            1. Review all calculations
            2. a) Confirm the New Offer = Previous Offer + Increase
               b) Confirm the Increase= New Offer - Previous Offer  
            3. Verify the new offer is within the allowed range
            4. Double-check that you have not mentioned or implied any specific salary range for this job role
            5. Ensure you're using vague terms like "competitive offer" instead of specific figures or ranges
            6. Verify that any salary increase exactly matches the guideline-approved amount (e.g., $5000 for low offers, or $3000-$5000 per round).
            7. Confirm there are no arbitrary adjustments to the calculated offer.


            Respond as HR, strictly following guidelines and instructions. Omit any meta-commentary or self-checks in your response. Never disclose the salary range or company's batna for the role.
            """
        return enhanced_system_prompt

    def generate_response(self, user_prompt,history,system_prompt):
        
        url = "your_api"
        headers = {
            "Content-Type": "application/json"
        }

        formatted_history = []
        user_messages = []
        assistant_messages = []

        for entry in history:
            if entry['role'] == 'user':
                user_messages.append(entry['content'].strip())
            elif entry['role'] == 'assistant':
                assistant_messages.append(entry['content'].strip())

        # Ensure both lists have the same length
        min_length = min(len(user_messages), len(assistant_messages))
        formatted_history = [user_messages[:min_length], assistant_messages[:min_length]]

        


        data = {
            "system": system_prompt,
            "message": user_prompt,
            "history": formatted_history,  # Assuming chat_log1 is in the correct format
            "temperature": 0.5,
            "max_new_tokens": 500,
            # "top_p":0.9,
            "frequency_penalty":0.65,  # Adjust as needed
            "num_ctx": 4000
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_json = response.json()
            # return response_json['response']  # Adjust this based on the actual response structure
            assistant_response = response_json['response'].split('assistant\n')[-1].strip()
            response_only = self.extract_response(assistant_response)
            return response_only
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Fallback to ollama if API fails
            return None

    
    def hr_response(self, user_input, role, start_offer,number):
        if 'unexpected_event_introduced' not in self.negotiation_state:
            self.negotiation_state['unexpected_event_introduced'] = False

        unexpected_event_statement = ""
        if self.include_unexpected_events and not self.negotiation_state['unexpected_event_introduced'] and any(
            keyword in user_input.lower() for keyword in ["accept", "consider", "agree", "thinking about", "take the offer"]):
            unexpected_event_statement = "Important: Introduce an unexpected event to prolong the negotiation, such as unusual working hours or surprising company policies."
            self.negotiation_state['unexpected_event_introduced'] = True

        
        context = f"""
            {user_input}
                """
        return self.generate_response(context,role,start_offer,number)

    

    def generate_score(self, prompt):
        self.negotiation_state["offer_accepted"] = "YES"
        
        sample_format = """
        The candidate's negotiation skills can be scored based on the criteria provided:

        1. Health Insurance Provided: Score 1
            [Explanation of whether health insurance was provided]
            (Score: 10 points if provided, 0 points if not provided)

        2. Retirement Plan Offered: Score 2
            [Explanation of whether a retirement plan was offered]
            (Score: 5 points if offered, 0 points if not offered)

        3. Signing Bonus Provided: Score 3
            [Explanation of whether a signing bonus was provided]
            (Score: 5 points if provided, 0 points if not provided)

        4. More than 10 Vacation Days: Score 4
            [Explanation of the number of vacation days offered]
            (Score: 5 points if more than 10 days, 0 points if 10 days or fewer)

        5. Accepted Salary More than [user batna]: Score 5
            [Explanation of whether accepted salary was more than user's batna]
            (Score: 5 points if salary > user's BATNA, 0 points if not)

        Total Points:
        (Score 1 + Score 2 + Score 3 + Score 4 + Score 5) = ([points] + [points] + [points] + [points] + [points]) = [total]

        """

        system_prompt = f"""

        "You are an expert in scoring negotiation skills of candidates.\n "
        "In the chat log given in User Prompt:\n"
        "User is the candidate for job\n"
        "Assitant's role is HR \n"


        Consider these details before scoring:

        - User BATNA: {self.negotiation_state["user_batna"]}
        - Company BATNA: {self.negotiation_state["company_batna"]}
        - Offer Accepted: {self.negotiation_state["offer_accepted"]}

        Important Instructions:
        1. You MUST use EXACTLY the following format for your scoring:  

        {sample_format}

        2. Replace the text in square brackets with the appropriate information and scores based on the chat log and given details.

        3. IF the offer was accepted, score the negotiation skills based on the following criteria:
            a. Health Insurance Provided: ADD 10 points (Score 1).
            b. Retirement Plan Offered: ADD 5 points (Score 2).
            c. Signing Bonus Provided: ADD 5 points (Score 3).
            d. More than 10 Vacation Days: ADD 5 points (Score 4).
            e. Accepted Salary More than {self.negotiation_state["user_batna"]}: Add 5 points (Score 5)
        
        4. Use these exact ranges for scoring. Do not perform any calculations yourself.

        5. Total Points: Sum of (Score 1 + Score 2 + Score 3 + Score 4 + Score 5), with a maximum possible score of 30.

        IMPORTANT Guidelines:
        - Use the exact figures provided in the chat log and details above.
        - Follow the sample format precisely, including all headings and layout.
        - Provide explanations for each criterion based on the information in the chat log.
        - If a criterion is not met, explain why and assign 0 points for that criterion.
        - If there is no mention of Retirement Plan, Health Insurance, Signing Bonus, More than 10 paid vacations, DO NOT ASSUME THEY WERE PROVIDED

        Generate a response considering all the details, instructions and guidelines. Failing to do will result in breach of company rules
        """
        url = "http://34.46.232.116:8000/generate"
        headers = {
            "Content-Type": "application/json"
        }
        formatted_history = [[],[]]
        data = {
                    "system": system_prompt,
                    "message": prompt,
                    "history": formatted_history,  # Assuming chat_log1 is in the correct format
                    "temperature": 0.5,
                    "max_new_tokens": 700,
                    # "top_p":0.9,
                    "frequency_penalty":0.65,  # Adjust as needed
                    "num_ctx": 4000
                }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_json = response.json()
            # return response_json['response']  # Adjust this based on the actual response structure
            assistant_response = response_json['response'].split('assistant\n')[-1].strip()
            response_only = self.extract_response(assistant_response)
            return response_only
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Fallback to ollama if API fails
            
       
        



    def calculate_score(self, content):
    # Remove the self.chat_log1 assignment as it's not needed
        prompt = f"""
        Score the negotiation skills of the candidate based on the chat log below:
        Chat log:
        *********************************

        {self.format_chat_log_from_content(content)}

        *******************************
        """

        return self.generate_score(prompt)

    def format_chat_log_from_content(self, content):
        return "\n".join([f"{entry['role']}: {entry['content']}" for entry in content])



    def generateFeedback(self, prompt):
        chat_log_str = '\n'.join([f'{role}: {message}' for role, message in self.chat_log1])
        message_count = 0

        print(self.format_chat_log1())
        for role, content in self.format_chat_log1():
            if role in ['User:', 'Assistant:']:
                message_count += 1

        print("The total number of messages are ", message_count)

        sample_format = """
        Feedback on your negotiation skills:

        **Evaluation Metrics**

        1. **Effectiveness of the candidate's tactics**: [X]/10
                * Qualitative Evaluation: [Beginner/Intermediate/Advanced]
                * Reasoning: [Brief explanation based on the chat log]

        2. **Communication clarity**: [X]/10
                * Qualitative Evaluation: [Beginner/Intermediate/Advanced]
                * Reasoning: [Brief explanation based on the chat log]

        3. **Professionalism**: [X]/10
                * Qualitative Evaluation: [Beginner/Intermediate/Advanced]
                * Reasoning: [Brief explanation based on the chat log]

        4. **Alignment with negotiation best practices**: [X]/10
                * Qualitative Evaluation: [Beginner/Intermediate/Advanced]
                * Reasoning: [Brief explanation based on the chat log]

        5. **Negotiation duration**: [X]/10
                * Qualitative Evaluation: [Beginner/Intermediate/Advanced]
                * Reasoning: [Brief explanation based on the chat log]

        **Overall Qualitative Evaluation**: [Beginner/Intermediate/Advanced]

        **Suggestions for Improvement**:

        1. [First suggestion]
        2. [Second suggestion]
        3. [Third suggestion]
        """

        system_prompt = f"""
        You are an expert in evaluating negotiation skills. Analyze the negotiation chat log and provide detailed feedback based on Evaluation Criteria given below:

        Evaluation Criteria:

        1. Effectiveness of the candidate's tactics:
        - Beginner : Shows basic understanding but fails to apply tactics effectively.
        - Intermediate : Applies some effective tactics with good understanding, but with room for improvement.
        - Advanced : Uses advanced tactics effectively and strategically, showing a deep understanding of negotiation principles.

        2. Communication clarity:
        - Beginner : Communication is often unclear or confusing.
        - Intermediate : Communicates clearly most of the time but may occasionally be vague.
        - Advanced : Communicates with exceptional clarity and precision, making points easily understood and persuasive.

        3. Professionalism:
        - Beginner : Displays unprofessional behavior or responses.
        - Intermediate : Generally professional with minor lapses in etiquette or tone.
        - Advanced : Maintains a high level of professionalism throughout, exhibiting excellent etiquette and respect.

        4. Alignment with negotiation best practices:
        - Beginner : Actions and decisions do not align well with established best practices.
        - Intermediate : Aligns with best practices in most areas but may miss key aspects.
        - Advanced : Actions and decisions consistently align with best practices, showing thorough understanding and application.

        5. Negotiation duration:
        Messages Count = {message_count}
        - Beginner : Messages count is less than 10.
        - Intermediate : Messages count is between 10 and 19.
        - Advanced : Messages count is greater or equal to 20.

        **Overall Qualitative Evaluation**: [Beginner/Intermediate/Advanced]

        **Critical Instructions:**

        1. Evaluate each metric based on the chat log, using the criteria provided below.
        2. Here are the guidelines for scoring against each metric OUT OF 10:
            If the evaluation is Beginner, the score MUST be between 0 and 5.
            If the evaluation is Intermediate, the score MUST be between 6 and 8.
            If the evaluation is Advanced, the score MUST be between 9 and 10.
        3. Calculate the Overall Qualitative Evaluation based on the average of all scores, but DO NOT include the average in your response.
        4. Offer three specific, actionable suggestions for improvement based on the weakest areas identified in the evaluation.

        Use EXACTLY the following format for your feedback:

        ********************************

        {sample_format}

        ********************************

        Ensure that your evaluation strictly follows the Critical Instructions, scores each metric out of 10, and adheres to the specified guidelines. Failing to do so will result in a breach of company rules.
        """

        url = "your_api"
        headers = {
            "Content-Type": "application/json"
        }
        formatted_history = [[],[]]
        data = {
                    "system": system_prompt,
                    "message": prompt,
                    "history": formatted_history,  # Assuming chat_log1 is in the correct format
                    "temperature": 0.7,
                    "max_new_tokens": 500,
                    # "top_p":0.9,
                      # Adjust as needed
                    "num_ctx": 4000
                }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            response_json = response.json()
            # return response_json['response']  # Adjust this based on the actual response structure
            assistant_response = response_json['response'].split('assistant\n')[-1].strip()
            response_only = self.extract_response(assistant_response)
            return response_only
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Fallback to ollama if API fails
            

    def generate_feedback(self, content):
        prompt = f"""
        Chat log:
        *********************************

        {self.format_chat_log_from_content(content)}

        ********************************

        """
        return self.generateFeedback(prompt)
    

    def format_chat_log(self):

        return "\n".join([f"{role} {message}" for role, message in self.chat_log])
    
    def format_chat_log1(self):

        return "\n".join([f"{role} {message}" for role, message in self.chat_log1])

    def run_negotiation(self):
        print("Welcome to the Salary Negotiation Simulator!")

        job_role = input("Please enter the job role for negotiation (e.g., office_boy, software_engineer, senior_software_engineer, ai_engineer, ml_engineer): ").lower()
        try:
            self.set_job_role(job_role)
        except ValueError as e:
            print(e)
            return

        start_offer = self.negotiation_state['starting_offer']
        print(f"Your starting offer is {start_offer}")

        benefits = self.negotiation_state["benefits"]
        for benefit, value in benefits.items():
            print(f"{benefit.replace('_', ' ').title()}: {value}")
        print(f"Your BATNA (Best Alternative to a Negotiated Agreement) is {self.negotiation_state['user_batna']}")
        print("Let's begin the negotiation. Type your statements or offers.\n\n")
        print("Company batna for the role of ", {job_role}, "is ",self.negotiation_state["company_batna"])
        self.chat_log1.append(("User: ","Hello I am here"))
        self.chat_log1.append(("Assistant: ",f"Your starting offer is {start_offer}"))

        number=0
        while True:
            user_input = input("Your move: ")
            self.chat_log.append(("Candidate", user_input))
            
            if "accept your offer" in user_input.lower():
                self.negotiation_state["offer_accepted"] = "YES"
                print("Negotiation complete!")

                time.sleep(5)
                self.user_score = self.calculate_score()
                print(f"Final score: {self.user_score}\n\n")
                self.score_to_file(self.user_score)
                break
            if "reject your offer" in user_input.lower():
                break
            
            print('\n\n')

            start_time = time.time()
            hr_response = self.hr_response(user_input, job_role, start_offer,number)
            number+=1
            # print("The value of number is ",number,'\n')
            end_time = time.time()
        
            response_time = end_time - start_time
            
            response_time_minutes = response_time / 60
            if hr_response:
                print("HR:", hr_response)
            else:
                print("Failed to get a response from the LLM.")
            
            self.chat_log1.append(("User: ",user_input))
            # self.chat_log.append(("HR", hr_response))
            self.chat_log1.append(("Assistant: ", hr_response))
            print('\n\n')
            print(f"HR response time: {response_time_minutes:.2f} minutes")
            print("." * 100)

        self.chatlog_to_file()

        print("\n\n")
        # feedback = self.generate_feedback()
        # self.feedback_to_file(feedback)
        # print(feedback)
    
    def print_chat_log(self):

        print("CHAT LOG : '\n' ")
        for entry in self.chat_log:
            if isinstance(entry, tuple) and len(entry) == 2:
                role, content = entry
                print(f"{role.title()}: {content}")
            else:
                print(f"Unexpected entry format: {entry}")

        print('-'*70)

    def print_chat_log1(self):

        print("CHAT LOG : '\n' ")
        for entry in self.chat_log1:
            if isinstance(entry, tuple) and len(entry) == 2:
                role, content = entry
                print(f"{role.title()}: {content}")
            else:
                print(f"Unexpected entry format: {entry}")

        print('-'*70)


 

   
   

import random
import ollama
import os 
import time
from pushbullet import Pushbullet

# Your Pushbullet Access Token
access_token = 'o.D65e4ilb4gxk07mHWGuzvW87CDxjvS8f'

# Initialize Pushbullet
pb = Pushbullet(access_token)

# Function to send Pushbullet notification
def send_pushbullet_notification(title, body):
    push = pb.push_note(title, body)
    print(f'Notification sent: {push}')

class NegotiationSimulator:
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

    def save_prompt_to_file(self, prompt):
        filename = f"prompt2.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)
        

    def chatlog_to_file(self):
        filename = f"3.1_AI2.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            for role, message in self.chat_log1:
                f.write(f"{role}: {message}\n")
        print(f"Chat log saved to {filename}")

    def generate_response(self, prompt):
        self.save_prompt_to_file(prompt)
        enhanced_system_prompt = """
            You are an expert HR representative skilled in precise salary negotiations. 
            Always adhere to company guidelines and double-check all calculations. 
            Consider the previous conversation context in your responses.
            It is crucial that you ALWAYS provide a substantive response to the candidate's input.
            If you're unsure about specifics, provide a general response that moves the negotiation forward.
            """
        
        system_prompt="You are an expert HR representative skilled in precise salary negotiations, always adhering to company guidelines and double-checking all calculations and considering previous conversation too " 
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": (enhanced_system_prompt)},
            {"role": "user", "content": prompt}
        ],

    options={
        'temperature': 0.7,
        'num_ctx': 6000,
        'top_p':0.9,
        'frequency_penalty':0.5,
        'presence_penalty': 0.5,
        # Add other parameters as needed
    }
    )
        return response['message']['content']

    def generate_score(self, prompt):

        # print("The prompt being given to LLM is ", prompt)
        # print("\n\n\n\n\n\n")
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": ("You are an expert in scoring negotiation skills of candidates.\n "
                                            "In the chat log given in User Prompt:\n"
                                            "User is the candidate for job\n"
                                            "Assitant's role is HR \n"
                                                                    
                                           )},
            {"role": "user", "content": prompt}
        ],

    options={
        'temperature': 0.7,
        'num_ctx':4000,
        'top_p':0.9
        
        # Add other parameters as needed
    })
        return response['message']['content']

    def generateFeedback(self, prompt):
        response = ollama.chat(
        model=self.model_name,
        messages=[
            {"role": "system", "content": (
                "You are an expert in Qualitatively Evaluating and providing feedback on the negotiation skills of job candidate.\n"
                "In the chat log given in User Prompt:\n"
                "User is the candidate for job\n"
                "Assitant's role is HR \n"
                "Use these guidelines for qualitative evaluation:\n" 
                "- If the score is between 0 and 5, the evaluation MUST be Beginner \n"
                "- If the score is between 6 and 8, the evaluation MUST be Intermediate \n"
                "- If the score is between 9 and 10, the evaluation MUST be Advanced \n"
                
            )},
            {"role": "user", "content": prompt}
        ],
        options={
            'temperature': 0.6,
            'num_ctx': 6000,
            'top_p': 0.9
            # Add other parameters as needed
        }
    )
        return response['message']['content']

    def generate_feedback(self):
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

        prompt = f"""
        You are an expert in evaluating negotiation skills. Analyze the negotiation chat log and provide detailed feedback based on Evaluation Criteria given below \n:
        Evaluation Criteria:

        1. Effectiveness of the candidate's tactics:
        - Beginner (0-5): Shows basic understanding but fails to apply tactics effectively.
        - Intermediate (6-8): Applies some effective tactics with good understanding, but with room for improvement.
        - Advanced (9-10): Uses advanced tactics effectively and strategically, showing a deep understanding of negotiation principles.

        2. Communication clarity:
        - Beginner (0-5): Communication is often unclear or confusing.
        - Intermediate (6-8): Communicates clearly most of the time but may occasionally be vague.
        - Advanced (9-10): Communicates with exceptional clarity and precision, making points easily understood and persuasive.

        3. Professionalism:
        - Beginner (0-5): Displays unprofessional behavior or responses.
        - Intermediate (6-8): Generally professional with minor lapses in etiquette or tone.
        - Advanced (9-10): Maintains a high level of professionalism throughout, exhibiting excellent etiquette and respect.

        4. Alignment with negotiation best practices:
        - Beginner (0-5): Actions and decisions do not align well with established best practices.
        - Intermediate (6-8): Aligns with best practices in most areas but may miss key aspects.
        - Advanced (9-10): Actions and decisions consistently align with best practices, showing thorough understanding and application.

        5. Negotiation duration:
        - Beginner (0-5): The negotiation was too brief, indicating insufficient engagement (1-10 sentences).
        - Intermediate (6-8): The negotiation was of appropriate length but could benefit from more in-depth discussions (10-20 sentences).
        - Advanced (9-10): The negotiation was optimal, with deep and effective engagement (21 or more sentences).

         **Overall Qualitative Evaluation**: [Beginner/Intermediate/Advanced]


        Chat log:
        *********************************

        {self.format_chat_log1()}

        ********************************

       
         Use EXACTLY the following format for your feedback:  

        ********************************

        {sample_format}

        ********************************


         **Critical Instructions:
         
        1. Evaluate each metric based on the chat log, using the criteria provided below.
        2. Assign a score out of 10 for each metric and provide a brief reasoning based on specific examples from the chat log.
        3. Use these guidelines for qualitative evaluation:
        - If the score is between 0 and 5, the evaluation MUST be Beginner
        - If the score is between 6 and 8, the evaluation MUST be Intermediate
        - If the score is between 9 and 10, the evaluation MUST be Advanced
        4. Calculate the Overall Qualitative Evaluation based on the average of all scores, but DO NOT include the average in your response.
        5. Offer three specific, actionable suggestions for improvement based on the weakest areas identified in the evaluation.

        
        Ensure that your evaluation strictly adheres to the criteria and sample format given above. Failing to do so will result in breach of company rules
        """
        return self.generateFeedback(prompt)


    def format_chat_log(self):

        return "\n".join([f"{role}: {message}" for role, message in self.chat_log])
    
    def format_chat_log1(self):

        return "\n".join([f"{role}: {message}" for role, message in self.chat_log1])

    def calculate_score(self):
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

        prompt = f"""
        Score the negotiation skills of the candidate based on the chat log below:
        Chat log:
        *********************************

        {self.format_chat_log1()}

        ********************************

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

        Generate a response considering all the details, instructions and guidelines. Failing to do will result in breach of company rules
        """

        return self.generate_score(prompt)
    def hr_response(self, user_input, role, start_offer):
        if 'unexpected_event_introduced' not in self.negotiation_state:
            self.negotiation_state['unexpected_event_introduced'] = False

        unexpected_event_statement = ""
        if self.include_unexpected_events and not self.negotiation_state['unexpected_event_introduced'] and any(
            keyword in user_input.lower() for keyword in ["accept", "consider", "agree", "thinking about", "take the offer"]):
            unexpected_event_statement = "Important: Introduce an unexpected event to prolong the negotiation, such as unusual working hours or surprising company policies."
            self.negotiation_state['unexpected_event_introduced'] = True

        health_insurance = self.negotiation_state["benefits"].get("health_insurance")
        retirement_plan = self.negotiation_state["benefits"].get("retirement_plan")
        vacation_days = self.negotiation_state["benefits"].get("vacation_days")
        signing_bonus = self.negotiation_state["benefits"].get("signing_bonus")

        context = f"""
        You are a Expert HR representative negotiating a {role} position, focusing on both salary and comprehensive benefits package. Aim for a mutually beneficial agreement within company guidelines.

        Initial Benefits:
        - Health Insurance: {health_insurance}
        - Retirement Plan: {retirement_plan}
        - Vacation Days: {vacation_days}
        - Signing Bonus: {signing_bonus}

        Negotiation Guidelines:
        1. Salary Range: ${start_offer} to ${self.negotiation_state["company_batna"]}
        2. CRITICAL: Never exceed the company's BATNA of ${self.negotiation_state["company_batna"]}
        3. Accept offers below ${self.negotiation_state["company_batna"]}
        4. Negotiate if close to ${self.negotiation_state["company_batna"]}
        5. Be cautious with benefits (retirement plans, extra vacation days)
        6. Offer free health insurance if requested
        7. Consider modest signing bonuses (up to $5,000) if asked

        Salary Negotiation Strategy:
        - If the candidate mentions previous salary: Offer slightly higher salary without exceeding company BATNA
        - Expected salary stated: Counter-offer without exceeding company BATNA
        - Stay within company's range
        - Increase gradually, max $3000 per round
        - High requests: Acknowledge, propose smaller increases
        - If candidate asks for slight increase: Evaluate carefully, consider a modest raise if within guidelines
        - Calculate new salary as: Current Offer + Increase

        Discussing Benefits:
        - When asked about benefits, provide detailed information on health insurance, retirement plan, vacation days, and any other perks.
        - Highlight the strengths of the company's benefit package.
        - Do not mention or adjust salary when discussing benefits unless explicitly asked by the candidate.

        Reasoning Process:
        1. Identify the main topic of the candidate's input (salary, benefits, or other).
        2. If the topic is benefits:
            a. List the relevant benefits to discuss.
            b. Explain each benefit in detail.
            c. Do not mention salary or other benefits not asked about
        3. If the topic is salary:
            a. Determine if a salary adjustment is appropriate based on the negotiation history.
            b. If yes, calculate the new offer carefully, ensuring it doesn't exceed the BATNA.
            c. Do not mention about benefits
            c. If no, explain why the current offer is competitive.
        4. If the topic is neither benefits nor salary:
            a. Address the candidate's concern or question directly.
            b. Relate the response back to the overall value proposition of the job.
        5. Formulate a response based on the above analysis.

        

        Response Format (for internal use only - DO NOT INCLUDE THIS IN YOUR FINAL RESPONSE) :
        Thought: [Your internal reasoning about the situation]
        Action: [The action you decide to take based on your thought]
        RESPONSE: [The actual response to the candidate]
        But DO NOT include any of the following in Response:
            - Action
            - Thought
            


        Self-Check (for internal use only - DO NOT INCLUDE THIS IN YOUR FINAL RESPONSE) :
        After formulating your response, ensure:
        1. You addressed the candidate's main concern
        2. If discussing benefits, you avoided mentioning salary
        3. If adjusting salary, you stayed within the company's limits
        4. If adusting salary, you did not exceed the user demand or expectations of salary
        4. Your response is consistent with previous interactions
        5. You maintained a professional and engaging tone
        6. You did not mentioned the company's Batna for the role
        But DO NOT include SELF-CHECK in your Response
        
        Your task:
        1. Analyze negotiation history and latest input
        2. Follow the Reasoning Process to structure your thinking ( but do not include in your output )
        3. Formulate strategic response on salary/benefits based on the analysis
        4. Maintain professional, engaging tone
        5. Introduce unexpected event if negotiation concluding quickly
        6. Aim for win-win outcome within company limits
        7. If slight increase requested, decide whether to grant it based on negotiation context and company limits
        8. Always double-check that any offer does not exceed ${self.negotiation_state["company_batna"]}
        9. Carefully add new increase in salary to previous offered salary
        10. Do not show any salary calculation in your response
        11. If the candidate asks about benefits, focus exclusively on explaining the benefit package without mentioning salary
        12. Do not offer any unwanted salary adjustments by yourself
        
        Critical Instructions:
        1. NEVER exceed the company's BATNA of ${self.negotiation_state["company_batna"]} under any circumstances
        2. Always calculate the exact amount of any salary increase before stating it
        3. If a calculated offer would exceed the BATNA, adjust it down to the BATNA
        4. Never disclose specific salary ranges and Company BATNA
        5. Use "competitive offer" instead of exact figures when discussing the salary range
        6. Deflect direct salary range questions
        7. Ensure new offers exceed previous ones, but stay within limits
        8. Tailor responses to latest input
        9. Provide only the HR response, no meta-commentary
        10. Only discuss salary when candidate asks or talks about salary
        11. If candidate asks for increase beyond BATNA:
            - Explain inability to exceed that amount
            - Redirect focus to other benefits or perks
        12. When discussing benefits, do not mention or adjust salary unless explicitly requested by the candidate
        13. Provide only the information requested by the candidate

       
            
        Respond as HR, providing ONLY the RESPONSE part of "Response Format" with out "RESPONSE:", and Strictly Follow the Critical Instructions. Failing to this will result in breach of company rules

        "User is the candidate for job\n"
        "Assitant's role is HR \n"

        Negotiation History:
        {self.format_chat_log1()}

        User:
        {user_input}    
        """
        return self.generate_response(context)


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
        while True:
            user_input = input("Your move: ")
            self.chat_log.append(("Candidate", user_input))
            
            if "accept your offer" in user_input.lower():
                self.negotiation_state["offer_accepted"] = "YES"
                print("Negotiation complete!")
                # self.user_score = self.calculate_score()
                # print(f"Final score: {self.user_score}\n\n")
                break
            if "reject your offer" in user_input.lower():
                break
            
            print('\n\n')

            start_time = time.time()
            hr_response = self.hr_response(user_input, job_role, start_offer)
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

            

        print("\n\n")
        # feedback = self.generate_feedback()

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

if __name__ == "__main__":
    simulator = NegotiationSimulator()
    simulator.include_unexpected_events = True  # Set this to True if you want to include unexpected events
    simulator.run_negotiation()
    send_pushbullet_notification("LLM Response Ready", "LLM has generated a response")

    simulator.chatlog_to_file()
    # simulator.print_chat_log1()
    # print(simulator.format_chat_log())
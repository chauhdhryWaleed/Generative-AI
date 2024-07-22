import random
import ollama

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
        self.model_name = "llama3:8b-instruct-q4_K_M"  # or "llama2:13b" depending on your Ollama setup
        self.job_roles = {
            "office_boy": {
                "salary_range": (30000, 550000),
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

    def generate_response(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert HR representative in salary negotiations."},
            {"role": "user", "content": prompt}
        ],

    options={
        'temperature': 0.3,
        'num_ctx': 4096
        # Add other parameters as needed
    }
    )
        return response['message']['content']

    def generate_score(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert in scoring the negotiation skills of candidates."},
            {"role": "user", "content": prompt}
        ],

    options={
        'temperature': 0.5,
        'num_ctx':4000
        
        # Add other parameters as needed
    })
        return response['message']['content']

    def generateFeedback(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert in providing feedback on the negotiation skills of job candidates."},
            {"role": "user", "content": prompt}
        ],

    options={
        'temperature': 0.7,
        'num_ctx':6000
        
        # Add other parameters as needed
    })
        return response['message']['content']

    def generate_feedback(self):
        prompt = f"""
        Evaluate the following negotiation based on the chat log:

        {self.format_chat_log()}

        Please provide feedback focusing solely on the candidate's contributions. For each of the following criteria, score out of 10 and provide a qualitative evaluation (Beginner, Intermediate, or Advanced). Here are the evaluation metrics, guidelines, and examples:

        1. **Effectiveness of the candidate's tactics**: Score for this metric = Score 1
        - **Beginner (0-5)**: Shows basic understanding but fails to apply tactics effectively.
            - *Example*: The candidate made a single counteroffer without considering the employer’s constraints or negotiating for additional benefits.
        - **Intermediate (6-8)**: Applies some effective tactics with good understanding, but with room for improvement.
            - *Example*: The candidate used effective tactics like asking for a higher salary but missed opportunities to negotiate other benefits or terms.
        - **Advanced (9-10)**: Uses advanced tactics effectively and strategically, showing a deep understanding of negotiation principles.
            - *Example*: The candidate demonstrated thorough research, offered multiple alternatives, and effectively used concessions to reach a favorable agreement.

        2. **Communication clarity**: Score for this metric = Score 2
        - **Beginner (0-5)**: Communication is often unclear or confusing.
            - *Example*: The candidate used ambiguous language, made unclear demands, or frequently changed their position, making it difficult to understand their goals.
        - **Intermediate (6-8)**: Communicates clearly most of the time but may occasionally be vague.
            - *Example*: The candidate generally communicated their points well but occasionally used jargon or did not fully elaborate on key aspects of their requests.
        - **Advanced (9-10)**: Communicates with exceptional clarity and precision, making points easily understood and persuasive.
            - *Example*: The candidate articulated their requests and counteroffers with precision, using clear and persuasive language to ensure mutual understanding.

        3. **Professionalism**: Score for this metric = Score 3
        - **Beginner (0-5)**: Displays unprofessional behavior or responses.
            - *Example*: The candidate used inappropriate language, showed impatience, or displayed a lack of respect toward the other party.
        - **Intermediate (6-8)**: Generally professional with minor lapses in etiquette or tone.
            - *Example*: The candidate maintained a professional demeanor but occasionally made comments that could be perceived as slightly unprofessional or overly aggressive.
        - **Advanced (9-10)**: Maintains a high level of professionalism throughout, exhibiting excellent etiquette and respect.
            - *Example*: The candidate consistently demonstrated respect, politeness, and professionalism, handling all interactions with a high degree of courtesy.

        4. **Alignment with negotiation best practices**: Score for this metric = Score 4
        - **Beginner (0-5)**: Actions and decisions do not align well with established best practices.
            - *Example*: The candidate made unrealistic demands or failed to address key negotiation principles such as understanding the other party’s needs.
        - **Intermediate (6-8)**: Aligns with best practices in most areas but may miss key aspects.
            - *Example*: The candidate followed most best practices but overlooked some important strategies, such as not adequately preparing for objections.
        - **Advanced (9-10)**: Actions and decisions consistently align with best practices, showing thorough understanding and application.
            - *Example*: The candidate demonstrated a thorough understanding of best practices, such as effective preparation, problem-solving, and mutual gains negotiation.

        5. **Negotiation duration**: Score for this metric = Score 5
        - **Beginner (0-5)**: Negotiation was too brief, indicating insufficient engagement.
            - *Example*: The entire negotiation concluded with a single sentence or a brief exchange, showing minimal effort to explore the terms or engage in discussion.
        - **Intermediate (6-8)**: Duration was appropriate but could benefit from more in-depth discussions.
            - *Example*: The negotiation lasted for a reasonable amount of time but lacked in-depth discussion or exploration of additional terms and conditions.
        - **Advanced (9-10)**: Duration was optimal, with deep and effective engagement.
            - *Example*: The negotiation involved multiple rounds of discussion, with thorough examination of terms, detailed exchanges, and effective problem-solving.

        **Calculation of Overall Qualitative Evaluation**:
        - Average = (Score 1 + Score 2 + Score 3 + Score 4 + Score 5) / 5
        - **Average 0-5**: Beginner
        - **Average 6-8**: Intermediate
        - **Average 9-10**: Advanced

        **Examples**:

        1. **Beginner**:
        - **Scores**: 2, 4, 3, 5, 1
        - **Sum**: 2 + 4 + 3 + 5 + 1 = 15
        - **Average**: 15 / 5 = 3
        - **Overall Qualitative Evaluation**: Beginner (since the average is less than 6)

        2. **Intermediate**:
        - **Scores**: 6, 7, 8, 7, 6
        - **Sum**: 6 + 7 + 8 + 7 + 6 = 34
        - **Average**: 34 / 5 = 6.8
        - **Overall Qualitative Evaluation**: Intermediate (since the average is between 6 and 8)

        3. **Advanced**:
        - **Scores**: 9, 10, 9, 10, 9
        - **Sum**: 9 + 10 + 9 + 10 + 9 = 47
        - **Average**: 47 / 5 = 9.4
        - **Overall Qualitative Evaluation**: Advanced (since the average is between 9 and 10)

        **Overall Qualitative Evaluation**: (Beginner, Intermediate, or Advanced)

        **NOTE: DO NOT GIVE THE AVERAGE IN YOUR RESPONSE

        **Suggestions for Improvement**: Provide specific suggestions to help the candidate improve their negotiation skills, if applicable.
        """
        return self.generateFeedback(prompt)


    def format_chat_log(self):
        return "\n".join([f"{role}: {message}" for role, message in self.chat_log])

    def calculate_score(self):
        prompt = f"""
        Score the negotiation skills of the candidate based on the chat log:
        Chat log: {self.format_chat_log()} 

        Consider these details before scoring:
        - User BATNA: {self.negotiation_state["user_batna"]}
        - Offer Accepted: {self.negotiation_state["offer_accepted"]}

        IF the offer was accepted, score the negotiation skills based on the following criteria:

        1. **Health Insurance Provided**: ADD 10 points (Score 1).
        2. **Retirement Plan Offered**: ADD 10 points (Score 2).
        3. **Signing Bonus Provided**: ADD 5 points (Score 3).
        4. **More than 10 Vacation Days**: ADD 5 points (Score 4).
        5. **Salary Relative to BATNA**: 
        - If the accepted salary exceeds the user’s BATNA ({self.negotiation_state["user_batna"]}), award points based on how close is Accepted Salary to the company’s BATNA ({self.negotiation_state["company_batna"]}), with a maximum of 10 points (Score 5).
          To determine points for the salary, use the following approach:
            1-If the accepted salary is very close to the company’s BATNA, award 10 points.
            2-If the salary is moderately close, award a proportionate score (e.g., 7 points if it’s somewhat close but not exact).
            3-If the salary is only slightly higher than the user’s BATNA, and far from the company’s BATNA, award fewer points

        **Total Points**: Sum of (Score 1 + Score 2 + Score 3 + Score 4 + Score 5), with a maximum possible score of 40.

        **NOTE**: DO NOT PROVIDE ANY ADDITIONAL FEEDBACK BESIDES CALCULATING THE SCORE.

          IF the offer was not accepted, give a score of 0.
        """

        return self.generate_score(prompt)

    def hr_response(self, user_input, role, start_offer):
    # Conditional statement based on the include_unexpected_events flag
        unexpected_event_statement = ""
        if self.include_unexpected_events:
            unexpected_event_statement = "Important note: Only when the candidate talks about accepting the offer or considering the offer then introduce some unexpected events that will prolong the negotiation, such as unusual working hours or other surprising company policies."

        health_insurance = self.negotiation_state["benefits"].get("health_insurance")
        retirement_plan = self.negotiation_state["benefits"].get("retirement_plan")
        vacation_days = self.negotiation_state["benefits"].get("vacation_days")
        signing_bonus = self.negotiation_state["benefits"].get("signing_bonus")

        context = f"""
        You are an HR representative in a salary negotiation for a {role}. Consider the following points in your response:
        1. If the candidate's offer is less than {self.negotiation_state["company_batna"]}, provide a response that accepts their offer.
        2. If the candidate's offer is close to {self.negotiation_state["company_batna"]}, provide a response that negotiates slightly with them. If they talk about their long experience and skills than accept their salary offer.
        3. Avoid easily granting benefits like retirement plans and more than 10 paid vacation days.
        4. If the candidate requests free health insurance than offer a free health insurance plan.
        5. If the candidate requests signing bonus,  offer a modest signing bonus ( up to 5k), but be prepared to negotiate these terms.
        

        Negotiation context:
        Starting offer: {start_offer}

        Intial Benefits Being provided:
        Health Insurance: {health_insurance}
        Retirement Plan: {retirement_plan}
        Vacation Days: {vacation_days}
        Signing Bonus: {signing_bonus}
       
        
        Chat history:
        {self.format_chat_log()}

        Candidate's statement or offer:
        {user_input}

        {unexpected_event_statement}

        Provide a response as the HR representative, focusing on discussing salary and benefits without formalities.
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
                self.user_score = self.calculate_score()
                print(f"Final score: {self.user_score}\n\n")
                break
            if "reject your offer" in user_input.lower():
                break
            
            print('\n\n')
            hr_response = self.hr_response(user_input, job_role, start_offer)
            print("HR:", hr_response)
            self.chat_log.append(("HR", hr_response))
            print("." * 50)

        print("\n\n")
        feedback = self.generate_feedback()

        print("Feedback on your negotiation skills:\n\n")
        print(feedback)

if __name__ == "__main__":
    simulator = NegotiationSimulator()
    simulator.include_unexpected_events = True  # Set this to True if you want to include unexpected events
    simulator.run_negotiation()
    send_pushbullet_notification("LLM Response Ready", "LLM has generated a response")

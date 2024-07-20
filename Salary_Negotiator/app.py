import random
import ollama

class NegotiationSimulator:
    def __init__(self):
        self.model_name = "llama3:8b-instruct-q4_K_M"  # or "llama2:13b" depending on your Ollama setup
        self.job_roles = {
            "office_boy": {
                "salary_range": (30000, 40000),
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
        'temperature': 0.5
        
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
        
        # Add other parameters as needed
    })
        return response['message']['content']

    def generate_feedback(self):
       prompt = f"""
        Evaluate the following negotiation based on the chat log:

        {self.format_chat_log()}

        Please provide feedback focusing solely on the candidate's contributions. For each of the following criteria, score out of 10 and provide a qualitative evaluation (Beginner, Intermediate, or Advanced) against each of the evaluation metrics below. Here are some guidelines and examples to help you with the qualitative evaluation:

        1. **Effectiveness of the candidate's tactics**: 
        - **Beginner**: The candidate shows basic understanding of negotiation tactics but fails to apply them effectively.
        - **Intermediate**: The candidate applies some effective tactics and demonstrates a good understanding, but there is room for improvement.
        - **Advanced**: The candidate uses advanced tactics effectively and strategically, showing a deep understanding of negotiation principles.

        2. **Communication clarity**:
        - **Beginner**: The candidate's communication is often unclear or confusing, making it hard to follow their points.
        - **Intermediate**: The candidate communicates clearly most of the time but may occasionally be vague or need further elaboration.
        - **Advanced**: The candidate communicates with exceptional clarity and precision, making their points easily understood and persuasive.

        3. **Professionalism**:
        - **Beginner**: The candidate displays unprofessional behavior or responses, lacking in etiquette or respect.
        - **Intermediate**: The candidate demonstrates professional behavior generally but may have minor lapses in etiquette or tone.
        - **Advanced**: The candidate maintains a high level of professionalism throughout, exhibiting excellent etiquette and respect.

        4. **Alignment with negotiation best practices**:
        - **Beginner**: The candidate's actions and decisions do not align well with established negotiation best practices.
        - **Intermediate**: The candidate aligns with best practices in most areas but may miss some key aspects.
        - **Advanced**: The candidate’s actions and decisions are consistently aligned with best practices, showing a thorough understanding and application.

        5. **Negotiation duration**:
        - **Beginner**: The negotiation was too brief, indicating that the candidate did not engage in sufficient negotiation.
        - **Intermediate**: The negotiation duration was appropriate but could benefit from more in-depth discussions.
        - **Advanced**: The negotiation duration was optimal, with the candidate engaging deeply and effectively.

        **Overall Qualitative Evaluation**: Based on the individual evaluations above, provide one overall qualitative evaluation for the candidate's negotiation skills (Beginner, Intermediate, or Advanced).

        **Suggestions for Improvement**: Provide specific suggestions to help the candidate improve their negotiation skills, if applicable.
        """

       return self.generateFeedback(prompt)


    def format_chat_log(self):
        return "\n".join([f"{role}: {message}" for role, message in self.chat_log])

    def calculate_score(self):
        prompt = f"""
        Score the negotiation skills of the candidate based on the chat log:
        Chat log: {self.format_chat_log()} 

        Consider these before scoring the negotiation skills:
        User BATNA: {self.negotiation_state["user_batna"]}
        Offer Accepted: {self.negotiation_state["offer_accepted"]}

        IF the offer was accepted, then also consider if the candidate was able to secure the following based on the chat log:
        Score the skills on the strictly on basis of these 5 evaluation metrices below:
        
        1. If Health Insurance was provided, ADD 10 points (score 1).
        2. If Retirement plan was offered, ADD 10 points (score 2).
        3. If Signing Bonus was provided, ADD 5 points (score 3).
        4. If more than 10 Vacation Days were provided, ADD 5 points (score 4).
        5. If the accepted salary in the chat log is more than the user BATNA {self.negotiation_state["user_batna"]}, ADD points accordingly out of 20 (score 5).
        
        Total Points = (score 1 + score 2 + score 3 + score 4 + score 5) out of 50.

        NOTE:
        "DO NOT PROVIDE ANY ADDITIONAL FEEDBACK BESIDES CALCULATING SCORE"


        IF the offer was not accepted, then give 0 points.
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

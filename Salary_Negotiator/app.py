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
        
       
        
        # Default parameter to include unexpected events
        self.include_unexpected_events = False

    def set_job_role(self, role):
        if role in self.job_roles:
            salary_range = self.job_roles[role]["salary_range"]
            self.negotiation_state = {
                "salary_range": salary_range,
                
                "benefits": {
                    "health_insurance": False,
                    "401k": False,
                    "vacation_days": 10,
                    "signing_bonus": 0
                },
                "job_responsibilities": [],
                "user_batna": salary_range[0],
                "company_batna": salary_range[1],
                "zopa": salary_range,
                "starting_offer": self.generate_random_offer(salary_range),  # Random starting offer within the lower range
                "offer_accepted": "NO"
            }
        else:
            raise ValueError(f"Job role '{role}' is not recognized.")
    
    def generate_random_offer(self, salary_range):
        
        upper_limit = salary_range[0] + 5000
    
    # Generate a random number in multiples of 500
        random_offer = random.randint(0, (upper_limit - salary_range[0]) // 500) * 500 + salary_range[0]
        
        return random_offer


    def generate_response(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert HR representative in salary negotiations."},
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']
    
    def generate_score(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert in scoring the negotiation skills of candidates."},
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']
    def generate_feedback(self):
        prompt = f"""
        Evaluate this negotiation based on the chat log:
        
        {self.format_chat_log()}

        Provide feedback on:
        1. Effectiveness of the candidate's tactics
        2. Communication clarity
        3. Professionalism
        4. Alignment with negotiation best practices
        5. Size of chat log. If the candidate did not negotiated much. 
        Suggest improvements if necessary.
        """
        return self.generate_response(prompt)
    def format_chat_log(self):
        return "\n".join([f"{role}: {message}" for role, message in self.chat_log])
    def calculate_score(self):
        prompt = f"""
        Score the negotiation skills of Candidate based on the chat log:
        Chat log: {self.format_chat_log()} 

        Consider these before scoring the negotiation skills:
        User BATNA: {self.negotiation_state["user_batna"]}
        Offer Accepted: {self.negotiation_state["offer_accepted"]}

        IF the offer was accepted then also consider if candidate was able to get these things based on the chat log
        Score the skills on the basis of this:
        
        1. If Health Insurance  Provided  ADD 10 points
        2. If 401K Bonus  provided ADD 10 points if instead of 401k other retirements plan offered add 5 points
        3. If Signing Bonus provided  ADD 5 points
        4. If more than 10 Vacation Days provided Add 5 points
        5. If the accepted salary in CHAT LOG is more than user BATNA {self.negotiation_state["user_batna"]} add points accordingly out of 20 .
        
        Total Points = Calculated Points from above criteria out of 50
        IF the offer was not accepted then give 0 points.
        """
        return self.generate_score(prompt)
    def hr_response(self, user_input, role, start_offer):
        
        
        # Conditional statement based on the include_unexpected_events flag
        unexpected_event_statement = ""
        if self.include_unexpected_events:
            unexpected_event_statement = "Important note: When the candidate talks about accepting the offer than introduce some unexpected events event which will Prolong the negotiation deal like Strange working hours or longer than usual working hours more than 8"

        context = f"""
        You are an HR representative in a salary negotiation for a {role}. Consider the following points in your response:
        1. If the offer made by the candidate  is above company's Salary range then do not accept the offer and negotiate the salary below salary range.
        2. If the candidate asks for salary which is less than the upper limit of salary range. Then accept their offer after slight negotiation. 
        3. Avoid easily granting benefits like 401k or more than 10 paid vacation days.
        4. If the candidate asks for health insurance, signing bonus. Then give him health insurance and 5k joining bonus
        5. If the candidate is persistent in getting these benefits, then grant him after some negotiation.
        6. Respond to the candidate's offer or request while considering the company's BATNA and ZOPA.
        7. While giving a response to the candidate DO NOT MENTION ABOUT company's BATNA and ZOPA and Salary Range.

        Negotiation context:
        Salary range: {self.negotiation_state['salary_range']}
        Starting offer: {start_offer}
        ZOPA: {self.negotiation_state['zopa']}
        Company’s BATNA: {self.negotiation_state['company_batna']}
    
        
        
        Chat history:
        {self.format_chat_log()}

        Candidate's statement or offer:
        {user_input}
        
        {unexpected_event_statement}
        
        Provide a response as the HR representative:
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
        start_offer=self.negotiation_state['starting_offer']
        print(f"Your starting offer is {start_offer}")

        benefits = self.negotiation_state["benefits"]
        for benefit, value in benefits.items():
            print(f"{benefit.replace('_', ' ').title()}: {value}")
        print(f"Your BATNA (Best Alternative to a Negotiated Agreement) is {self.negotiation_state['user_batna']}")
        print("Let's begin the negotiation. Type your statements or offers.\n\n")

        while True:
            user_input = input("Your move: ")
            self.chat_log.append(("Candidate", user_input))
            if "accept your offer" in user_input.lower():
                self.negotiation_state["offer_accepted"] = "YES"
                print("Negotiation complete!")
                self.user_score = self.calculate_score()
                print(f"Final score: {self.user_score}")
                break
            if "reject your offer" in user_input.lower():
                break

            hr_response = self.hr_response(user_input, job_role,start_offer)
            print("HR:", hr_response)
            self.chat_log.append(("HR", hr_response))

        
        feedback = self.generate_feedback()

        print("Feedback on your negotiation skills:")
        print(feedback)

if __name__ == "__main__":
    simulator = NegotiationSimulator()
    simulator.include_unexpected_events = True  # Set this to True if you want to include unexpected events
    simulator.run_negotiation()

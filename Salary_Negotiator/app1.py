import random
import ollama

class NegotiationSimulator:
    def __init__(self):
        self.model_name = "llama3:8b-instruct-q4_K_M"  # or "llama2:13b" depending on your Ollama setup
        self.negotiation_state = {
            "salary_range": (80000, 100000),  # Adjusted to match company BATNA
            "current_offer": 0,
            "benefits": {
                "health_insurance": False,
                "401k": False,
                "vacation_days": 10,
                "signing_bonus": 0
            },
            "job_responsibilities": [],
            "user_batna": 75000,
            "company_batna": 100000,  # Company BATNA set to 100000
            "zopa": (80000, 100000)  # Adjusted to match the new salary range
        }
        self.chat_log = []
        self.user_score = 0
        self.unexpected_events = [
            "The company just received a large investment and has more budget for salaries.",
            "A competitor has made you an offer.",
            "The company is implementing cost-cutting measures.",
            "Your unique skills are in high demand in the industry."
        ]
        self.negotiation_complete = False  # Flag to indicate if the negotiation is complete

    def generate_response(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert HR representative in salary negotiations."},
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']

    def hr_response(self, user_input):
        context = f"""
        You are an HR representative in a salary negotiation. 
        Negotiation context:
        Salary range: {self.negotiation_state['salary_range']}
        Current offer: {self.negotiation_state['current_offer']}
        Benefits: {self.negotiation_state['benefits']}
        Job responsibilities: {self.negotiation_state['job_responsibilities']}

        Chat history:
        {self.format_chat_log()}

        Candidate: {user_input}

        Respond as the HR representative, considering the BATNA and ZOPA:
        Company's BATNA: {self.negotiation_state['company_batna']}
        ZOPA: {self.negotiation_state['zopa']}

        HR:
        """
        return self.generate_response(context)

    def evaluate_offer(self, offer):
        prompt = f"""
        Evaluate this salary offer:
        Offer: {offer}
        Salary range: {self.negotiation_state['salary_range']}
        Current offer: {self.negotiation_state['current_offer']}
        ZOPA: {self.negotiation_state['zopa']}

        Provide a brief assessment of whether this is a good offer and why.
        """
        return self.generate_response(prompt)

    def generate_feedback(self, user_input):
        prompt = f"""
        Evaluate this negotiation tactic:
        Candidate's statement: '{user_input}'

        Provide feedback on:
        1. Effectiveness of the tactic
        2. Communication clarity
        3. Professionalism
        4. Alignment with negotiation best practices

        Suggest improvements if necessary.
        """
        return self.generate_response(prompt)

    def format_chat_log(self):
        return "\n".join([f"{role}: {message}" for role, message in self.chat_log])

    def update_negotiation_state(self, hr_response):
        # Extract the offer from the HR response
        try:
            offer = int(''.join(filter(str.isdigit, hr_response)))
            if offer <= self.negotiation_state["company_batna"]:
                self.negotiation_state["current_offer"] = offer
            else:
                print(f"HR: I'm sorry, but we cannot exceed our BATNA of {self.negotiation_state['company_batna']}.")
                self.negotiation_state["current_offer"] = self.negotiation_state["company_batna"]
        except ValueError:
            pass

        if "health insurance" in hr_response.lower():
            self.negotiation_state["benefits"]["health_insurance"] = True
        if "401k" in hr_response.lower():
            self.negotiation_state["benefits"]["401k"] = True
        if "vacation" in hr_response.lower():
            self.negotiation_state["benefits"]["vacation_days"] += 5
        if "signing bonus" in hr_response.lower():
            self.negotiation_state["benefits"]["signing_bonus"] += 5000
        if "responsibility" in hr_response.lower():
            self.negotiation_state["job_responsibilities"].append(hr_response)

    def calculate_score(self):
        base_score = 50
        if self.negotiation_state["current_offer"] > self.negotiation_state["user_batna"]:
            base_score += 20
        if self.negotiation_state["current_offer"] > self.negotiation_state["zopa"][0]:
            base_score += 10
        if self.negotiation_state["benefits"]["health_insurance"]:
            base_score += 5
        if self.negotiation_state["benefits"]["401k"]:
            base_score += 5
        base_score += self.negotiation_state["benefits"]["vacation_days"] // 2
        base_score += self.negotiation_state["benefits"]["signing_bonus"] // 1000
        return min(base_score, 100)

    def trigger_unexpected_event(self):
        if random.random() < 0.2:  # 20% chance of unexpected event
            event = random.choice(self.unexpected_events)
            print(f"Unexpected event: {event}")
            return event
        return None

    def run_negotiation(self):
        print("Welcome to the Salary Negotiation Simulator!")
        print(f"Your salary range is {self.negotiation_state['salary_range']}")
        print(f"Your BATNA (Best Alternative to a Negotiated Agreement) is {self.negotiation_state['user_batna']}")
        print(f"The ZOPA (Zone of Possible Agreement) is {self.negotiation_state['zopa']}")
        print("Let's begin the negotiation. Type your statements or offers.")

        while not self.negotiation_complete:
            user_input = input("Your move: ")
            self.chat_log.append(("Candidate", user_input))

            # Check if the user accepted or rejected an offer
            if any(term in user_input.lower() for term in ["accept", "agree", "decline", "reject"]):
                if "accept" in user_input.lower() or "agree" in user_input.lower():
                    self.negotiation_complete = True
                    print("You have accepted the offer!")
                elif "decline" in user_input.lower() or "reject" in user_input.lower():
                    self.negotiation_complete = True
                    print("You have declined the offer.")
                continue

            hr_response = self.hr_response(user_input)
            print("HR:", hr_response)
            self.chat_log.append(("HR", hr_response))

            self.update_negotiation_state(hr_response)  # Updated to pass HR response

            if 'offer' in hr_response.lower():  # Updated to check HR response
                evaluation = self.evaluate_offer(self.negotiation_state["current_offer"])
                print("Offer Evaluation:", evaluation)

            feedback = self.generate_feedback(user_input)
            print("Feedback:", feedback)

            self.user_score = self.calculate_score()
            print(f"Current negotiation score: {self.user_score}/100")

        print("Negotiation complete!")
        print("Final negotiation state:")
        print(self.negotiation_state)
        print(f"Final score: {self.user_score}/100")

if __name__ == "__main__":
    simulator = NegotiationSimulator()
    simulator.run_negotiation()

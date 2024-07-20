import streamlit as st
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
        self.reset_simulation()

    def reset_simulation(self):
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
                    "401k": False,
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

    def generate_random_offer(self, salary_range):
        upper_limit = salary_range[0] + 5000
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

    def generateFeedback(self, prompt):
        response = ollama.chat(model=self.model_name, messages=[
            {"role": "system", "content": "You are an expert in providing Feedback to negotiation skills of Job Candidate."},
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']

    def generate_feedback(self):
        prompt = f"""
        Evaluate this negotiation based on the chat log:
        
        {self.format_chat_log()}

        Provide feedback only on Candidate chat from the Chatlog and score each of these points out of 10:
        1. Effectiveness of the candidate's tactics
        2. Communication clarity of candidate
        3. Professionalism of candidate
        4. Alignment with negotiation best practices 
        5. If the Negotiation Duration is short, it indicates that the candidate did not negotiate much, but they should have. If the Negotiation Duration is adequate, the feedback will be positive.

        According to the negotiation skills give Qualitative Evaluation
        Beginner , Intermediate or Advanced 
        
        Suggest improvements if necessary.
        """
        return self.generateFeedback(prompt)

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
        
        1. If Health Insurance Provided ADD 10 points (score 1)
        2. If Retirement plan offered add 10 points (score 2)
        3. If Signing Bonus provided ADD 5 points (score 3)
        4. If more than 10 Vacation Days provided Add 5 points (score 4)
        5. If the accepted salary in CHAT LOG is more than user BATNA {self.negotiation_state["user_batna"]} add points accordingly out of 20 .(score 5)
        
        Total Points = (score 1+score 2+score 3+score 4+score 5) out of 50
        IF the offer was not accepted then give 0 points.
        """
        return self.generate_score(prompt)

    def hr_response(self, user_input, role, start_offer):
        unexpected_event_statement = ""
        if self.include_unexpected_events:
            unexpected_event_statement = "Important note: Only when the candidate talks about accepting the offer or considering the offer than introduce some unexpected events event which will Prolong the negotiation deal like Strange working hours or longer than usual working hours more than 8"

        context = f"""
        You are an HR representative in a salary negotiation for a {role}. Consider the following points in your response:
        1. If the offer made by the candidate is above company's Salary range then do not accept the offer and negotiate the salary below the UPPER END of salary range.
        2. If the candidate asks for salary which is less than the upper limit of salary range. Then accept their offer after slight negotiation. 
        3. Avoid easily granting benefits like retirement plan and more than 10 paid vacation days.
        4. If the candidate asks for health insurance, signing bonus. Then give him health insurance and 5k joining bonus strictly no more than 5k joining bonus
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

    def run_negotiation(self, user_input, job_role):
        if job_role not in self.job_roles:
            raise ValueError(f"Job role '{job_role}' is not recognized.")
        
        if not self.negotiation_state:
            self.set_job_role(job_role)
        
        start_offer = self.negotiation_state['starting_offer']

        self.chat_log.append(("Candidate", user_input))
        hr_response = self.hr_response(user_input, job_role, start_offer)
        self.chat_log.append(("HR", hr_response))

        if "accept your offer" in user_input.lower():
            self.negotiation_state["offer_accepted"] = "YES"
            self.user_score = self.calculate_score()
            feedback = self.generate_feedback()
            return hr_response, self.user_score, feedback, True
        if "reject your offer" in user_input.lower():
            feedback = self.generate_feedback()
            return hr_response, None, feedback, True
        return hr_response, None, None, False


def main():
    st.title("Salary Negotiation Simulator")

    if 'simulator' not in st.session_state:
        st.session_state.simulator = NegotiationSimulator()

    simulator = st.session_state.simulator

    if 'job_role' not in st.session_state:
        st.session_state.job_role = None

    job_role = st.selectbox("Select Job Role", [
        "office_boy", "software_engineer", "senior_software_engineer", "ai_engineer", "ml_engineer"
    ])

    # Update session state with the selected job role
    st.session_state.job_role = job_role

    user_input = st.text_area("Your Statement or Offer", "")

    if st.button("Submit"):
        if user_input and st.session_state.job_role:
            hr_response, score, feedback, negotiation_ended = simulator.run_negotiation(user_input, st.session_state.job_role)
            st.subheader("Chat History:")
            st.write(simulator.format_chat_log())
            st.subheader("HR Response:")
            st.write(hr_response)
            if score is not None:
                st.subheader("Final Score:")
                st.write(score)
            st.subheader("Feedback:")
            st.write(feedback)

            if negotiation_ended:
                st.success("Negotiation has ended. Click 'Start New Negotiation' to begin again.")
        else:
            st.warning("Please enter your statement or offer and select a job role.")

    if st.button("Start New Negotiation"):
        st.session_state.simulator.reset_simulation()
        st.session_state.job_role = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()

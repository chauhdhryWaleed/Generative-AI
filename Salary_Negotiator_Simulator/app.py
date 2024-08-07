from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from generate_feedback import NegotiationSimulator
from simulator import SalaryNegotiation
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG)
class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Change to Integer
    name = db.Column(db.String(100), nullable=False)  # Add this line
    job_role = db.Column(db.String(100), nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)  # Add this line
    feedback = db.Column(db.Text)  # Add this line
    score = db.Column(db.Text)  # Add this line

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)  # Change to Integer
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship('Session', backref=db.backref('messages', lazy=True))
@app.route('/chat_logs', methods=['GET'])
def get_all_chat_log_ids():
    # Filter sessions to only include those that are completed
    completed_sessions = Session.query.filter_by(completed=True).all()
    
    # Log each completed session's ID
    for session in completed_sessions:
        app.logger.info(f"id {session.id}")

    # Prepare the data to be sent back
    session_data = [{'id': session.id, 'name': session.name, 'completed': session.completed} for session in completed_sessions]

    # Debug log for the data being sent back
    app.logger.debug(f"data being sent back is this: {session_data}")

    return jsonify({'sessions': session_data})

@app.route('/session', methods=['POST'])
def create_session():
    data = request.get_json()
    job_role = data.get('job_role')
    name = data.get('name')  # Add this line
    if not job_role or not name:  # Modify this line
        return jsonify({'error': 'Job role and name are required'}), 400

    simulator1 = SalaryNegotiation()

    try:
        simulator1.set_job_role(job_role) 
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    session = Session.query.order_by(Session.id.desc()).first()
    if session:
        session_id = session.id + 1
    else:
        session_id = 1

    system_prompt=data.get('prompt')
    if system_prompt=="":
        system_prompt = simulator1.generate_system_prompt(job_role)
    
    app.logger.info("System prompt is : %s", system_prompt)
    

    new_session = Session(id=session_id, name=name, job_role=job_role, system_prompt=system_prompt)  # Modify this line
    new_session.completed = False
    db.session.add(new_session)
    starting_offer = simulator1.negotiation_state['starting_offer']
    user_msg = Message(session_id=session_id, role='user', content="Hello I am here")
    assistant_msg = Message(session_id=session_id, role='assistant', content=f"Your starting offer is {starting_offer}")
    db.session.add(user_msg)
    db.session.add(assistant_msg)

    db.session.commit()

    return jsonify({
        'session_id': session_id,
        'name': name,  # Add this line
        'starting_offer': starting_offer,
        'benefits': simulator1.negotiation_state['benefits'],
        'user_batna': simulator1.negotiation_state['user_batna']
    }), 201

@app.route('/session/<int:session_id>/message', methods=['POST'])
def send_message(session_id):
    
        session = Session.query.get_or_404(session_id)
        data = request.get_json()
        user_message = data.get('message', '')
        simulator1 = SalaryNegotiation()
        simulator1.set_job_role(session.job_role)

        if "accept your offer" in user_message.lower():
            simulator1.negotiation_state["offer_accepted"] = "YES"
        
            # Generate feedback and score
            chat_history = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
            formatted_history = [{'role': msg.role, 'content': msg.content} for msg in chat_history]
            
            simulator = NegotiationSimulator()
            
            feedback = simulator.generate_feedback(formatted_history)
            score = simulator1.calculate_score(formatted_history)
        
            
            # Store feedback and score in the session
            session.feedback = feedback
            session.score = score
            session.completed = True
            app.logger.debug("Feedback, and score are addded in data base")
            user_msg = Message(session_id=session_id, role='user', content="I accept your offer")
            db.session.add(user_msg)
            db.session.commit()
            return jsonify({'response': "OFFER WAS ACCEPTED", 'feedback': feedback, 'score': score}), 200
            
        


        # Save user message
        user_msg = Message(session_id=session_id, role='user', content=user_message)
        db.session.add(user_msg)

        # Get chat history
        chat_history = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
        formatted_history = [{'role': msg.role, 'content': msg.content} for msg in chat_history]

        # Generate LLM response
        
        llm_response = simulator1.generate_response(user_message, formatted_history, session.system_prompt)

        # Save LLM response
        llm_msg = Message(session_id=session_id, role='assistant', content=llm_response)
        db.session.add(llm_msg)

        db.session.commit()

        return jsonify({'response': llm_response}), 200
   

@app.route('/session/<int:session_id>/history', methods=['GET'])
def get_chat_history(session_id):
    session = Session.query.get_or_404(session_id)
    chat_history = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    formatted_history = [{'role': msg.role, 'content': msg.content, 'timestamp': msg.created_at.isoformat()} for msg in chat_history]

    return jsonify({'history': formatted_history}), 200

@app.route('/session/<int:session_id>/feedback', methods=['GET'])
def get_feedback(session_id):
    session = Session.query.get_or_404(session_id)
    chat_history = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    formatted_history = [{'role': msg.role, 'content': msg.content} for msg in chat_history]

    simulator = NegotiationSimulator()
    
    feedback = simulator.generate_feedback(formatted_history)
    
    simulator1 = SalaryNegotiation()
    simulator1.set_job_role(session.job_role)
    score = simulator1.calculate_score(formatted_history)

    return jsonify({'feedback': feedback, 'score': score}), 200

@app.route('/session/<int:session_id>/result', methods=['GET'])
def get_session_result(session_id):
    session = Session.query.get_or_404(session_id)
    if not session.completed:
        return jsonify({'error': 'Session is not completed yet'}), 400
    
    return jsonify({
        'id': session.id,
        'name': session.name,
        'feedback': session.feedback,
        'score': session.score
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
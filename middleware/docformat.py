from dotenv import load_dotenv
import os
import openai
import uuid
from app import db
from app.models import Conversation

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = os.getenv("OPENAI_API_TYPE")

def ai_search(query, conversation):
    try:
        conversation.append({"role": "user", "content": query})
        response = openai.ChatCompletion.create(
            engine="HRbot",  # Assuming you have your OpenAI engine set up
            messages=conversation,
            temperature=0.7,
            max_tokens=1000
        )
        assistant_response = response.choices[0].message['content'].strip() if response.choices else ""
        conversation.append({"role": "assistant", "content": assistant_response}) 
        return [assistant_response, conversation]
    except Exception as e:
        print(f"Error querying OpenAI: {e}")
        return None

def generate_conversation_id():
    return str(uuid.uuid4())

def get_unique_conversation_id():
    # Loop until a unique conversation_id is found
    while True:
        conversation_id = generate_conversation_id()
        check_conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
        
        if not check_conversation:  # If no conversation with this ID exists
            return conversation_id

def get_conversation(document_text):
    conversation_id = get_unique_conversation_id()
    conversation = [
                {
                 "role": "system", 
                 "content": f"You are an assistant that helps in finding specific information, summarization and queries on documents and inidicate to user when info is not avalable. This is the document {document_text}"
                }
            ]
    # print(conversation_id)
    return [conversation, conversation_id]
    
def set_conversation(conversation, conversation_id):
    # global conversation
    stored_conversation = Conversation.query.filter_by(conversation_id=conversation_id).first()
    if stored_conversation:
        stored_conversation.update_access_time()
        stored_conversation.content = conversation
        db.session.commit()

def new_conversation(user_id, username, conversation, conversation_id, document_id):
    new_conversation = Conversation(user_id=user_id, username = username, content=conversation, conversation_id=conversation_id, document_id=document_id)
    db.session.add(new_conversation)
    db.session.commit()

    # return jsonify({'message': 'Conversation stored successfully'})



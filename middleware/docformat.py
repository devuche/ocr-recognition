from dotenv import load_dotenv
import os
import openai
import uuid
from app import db
import json
from .docfreader import intelligent_response
from app.models import Conversation

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = os.getenv("OPENAI_API_TYPE")

def ai_search(query, conversation):
    try:
        if query['document'] is not None:
            print(query['document'])
            conversation.append({"role": "user", "content": f"This is my query:{query['user_input']} this is my uploaded document: {query['document']}, please respond to my query"} )
        else:
            print(query)
            conversation.append({"role": "user", "content": query['user_input']} )
        response = openai.ChatCompletion.create(
            engine="HRbot",  # Assuming you have your OpenAI engine set up
            messages=conversation,
            temperature=0.7,
            functions=[
                {
                    #function to check if the solution is within available documents
                    "name": "intelligent_response",  # Name of the function
                    "description": "Check the knowledge base using this function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                                "prompts": {
                                    "type": "string",
                                    "description": "This is problem the user is facing"
                                },
                            },
                            "required": ["prompts"],
                    },
                } # Add more functions here if needed
            ],
        function_call="auto", 
            max_tokens=1000
        )
        check_response = response["choices"][0]["message"]
        if check_response.get("function_call"):
            function_name = check_response["function_call"]["name"]
            if function_name == "intelligent_response":
                available_functions = {
                    "intelligent_response": intelligent_response,
                }
                function_to_call = available_functions[function_name]
                function_args = json.loads(check_response["function_call"]["arguments"])
                function_response = function_to_call(
                    prompts= function_args.get("prompts"),
                )
                if isinstance(function_response, list):
                    conversation.append(
                        {
                            "role":"function",
                            "name": function_name,
                            "content": function_response[0],
                        }
                    )
                else:
                    conversation.append(
                        {
                            "role":"function",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                
                return [function_response, conversation]
        else:
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

def get_conversation():
    conversation_id = get_unique_conversation_id()
    conversation = [
                {
                 "role": "system", 
                 "content": f"You are an HR assistant that can also help in finding specific information, summarization and queries on documents and inidicate to user when info is not avalable."
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

def new_conversation(user_id, username, conversation, conversation_id, subject):
    new_conversation = Conversation(user_id=user_id, username = username, content=conversation, conversation_id=conversation_id, subject=subject)
    db.session.add(new_conversation)
    db.session.commit()

    # return jsonify({'message': 'Conversation stored successfully'})



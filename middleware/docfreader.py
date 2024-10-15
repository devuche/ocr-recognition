from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import os
import json
import requests
import logging
from logging.handlers import RotatingFileHandler
from .getdocument import generate_blob_url
# from .openaiauth import ChatCompletion
import openai
#though the function is not used in this file, it is used in the sendemail.py file
load_dotenv()

BING_SEARCH_KEY = os.environ.get('BING_SEARCH_KEY')

file_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
file_handler.setLevel(logging.DEBUG)

# Create a handler that logs messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Set the format for logging
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set up Azure Cognitive Search credentials
service_name = os.environ.get('SERVICE_NAME')
index_name = os.environ.get('INDEX_NAME')
api_key = os.environ.get('SERVICE_KEY')
endpoint = "https://{0}.search.windows.net/".format(service_name)
credential = AzureKeyCredential(api_key)
client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)


def query_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            engine="HRbot",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant, you make a prompt a simple and concise."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"Error querying ChatGPT: {e}")
        return "I have no information at this point regarding this"
    
def search_internet(query, subscription_key):
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()  # Ensure we raise an error for bad responses
    search_results = response.json()
    
    # Extract the snippet from the first search result
    if 'webPages' in search_results and 'value' in search_results['webPages'] and len(search_results['webPages']['value']) > 0:
        snippet = search_results['webPages']['value'][0]['snippet']
        return {'content':snippet, 
                'url':search_results['webPages']['value'][0]['url']
        }
    else:
        return None
    
def search_documents(query):
    # Execute search query
    result = client.search(search_text=query)

    # Process search results
    for i, document in enumerate(result):
        # Access extracted information from the document
        link = generate_blob_url(document['metadata_storage_name'])
        output = {'content': document['content'], 
                  'document_name': document['metadata_storage_name'],
                  'author': document["metadata_author"], 
                  'document_link': link
        }
        if i == 0:
            break
    return output
# print(search_documents("how can i access nnpc workplace")[0])

def finetune(question, prompt):
    response = openai.ChatCompletion.create(
        engine="HRbot",
        messages=[
            {"role": "system", 
            "content": "1. Only if the answer provided to the question is not related to the question, then you will provide this response which should always be 'No information'. 2. If the answer is related to the question, make the prompt more concise, human friendly and exclude quotation marks."},
            {"role": "user", "content": f"question: {question}, answer: {prompt['content']}"}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    # print(response)
    if response['choices'] and response['choices'][0]['message']['content']:
        message = response['choices'][0]['message']['content'].strip()
        if "No information" in message:
            search_info = search_internet(question, BING_SEARCH_KEY)
            if search_info:
                chatgpt_info = query_chatgpt(search_info['content'])
                message = [chatgpt_info, search_info['url']]
                return message
            else:
                message = "I have no information at this point regarding this"
                return message
        else:
            message = [message, prompt['author'], prompt['document_name'], prompt['document_link']]
            return message
     
def intelligent_response(prompts):
    response = openai.ChatCompletion.create(
        engine="HRbot",
        messages=[
            {"role": "system", 
            "content": "1. You help determine if it is a prompt you get. If it is you will run the function search_document"},
            {"role": "user", "content": prompts}
        ],
        temperature=0.7,
        functions=[
        {
            "name": "search_documents",  # Name of the function
            "description": "Check through document to provide solution to questions",
            "parameters": {
                "type": "object",
                "properties": {
                        "query": {
                            "type": "string",
                            "description": "This is concise query the user is asking"
                        },
                    },
                    "required": ["query"],
                },
            }
    ],
        function_call="auto", 
        max_tokens=1000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    check_response = response["choices"][0]["message"]
    if check_response.get("function_call"):
        function_name = check_response["function_call"]["name"]
        if function_name == "search_documents":
            available_functions = {
                "search_documents": search_documents,
            }
            function_to_call = available_functions[function_name]
            function_args = json.loads(check_response["function_call"]["arguments"])
            query = function_args.get("query")
            function_response = function_to_call(
                query= function_args.get("query"),
            )
            final_response = finetune(prompts, function_response)
            return final_response
    else:
        assistant_response = response['choices'][0]['message']['content'].strip() if response['choices'] else ""
        # print(assistant_response)
        return assistant_response
    
def generate_subject(input):
    try:
        response = openai.ChatCompletion.create(
            engine="HRbot",
            messages=[
                {"role": "system", 
                "content": "You can generate a short subject based on the beginning of the conversation based on the user's input, just the subject itself with no other information and without 'subject :'."},
                {"role": "user", "content": f"conversation: {input}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"Error querying ChatGPT: {e}")
        return "Error", 500
# print(intelligent_response("what is the hr leave policy"))



from flask import Blueprint, request, jsonify, url_for
from .models import Documents, Conversation
from . import db
from azure.storage.blob import BlobServiceClient
import logging
from logging.handlers import RotatingFileHandler
from middleware import ocr, docformat, docfreader
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import openai
import uuid
from flasgger import swag_from

load_dotenv()

views = Blueprint('views', __name__)

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
    

openai.api_type = os.environ.get('OPENAI_API_TYPE')
openai.api_base = os.environ.get('OPENAI_API_BASE')
openai.api_version = os.environ.get('OPENAI_API_VERSION')
openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.log = 'debug'

connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_name = os.environ.get('CONTAINER_NAME')

@views.route('/upload-document', methods=['POST'])
@swag_from({
    'tags': ['Documents'],
    'description': 'Upload a file to Azure Blob Storage',
    'parameters': [
        {
            'name': 'userName',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Name of the user making the request'
        },
        {
            'name': 'userEmail',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Email of the user making the request'
        },
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'File to upload to Azure Blob Storage'
        }
    ],
    'responses': {
        200: {
            'description': 'text extracted from the document'
        },
        400: {
            'description': 'Bad request'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    username = request.headers.get('userName')
    email = request.headers.get('userEmail')

    if email is None or username is None:
        return jsonify({"error": "Please provide both email and username in the request headers"}), 400
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    try:
        # Generate the initial filename
        # base_filename = file.filename.split('.')[0]
        # extension = file.filename.split('.')[-1]
        # new_filename = file.filename

        # document_exists = Documents.query.filter_by(document_name=new_filename).first()

        # while document_exists:
        #     unique_identifier = uuid.uuid4().hex[:8]  # Short UUID
        #     new_filename = f"{base_filename}_{unique_identifier}.{extension}"
            
        #     # Check if the newly generated filename exists
        #     document_exists = Documents.query.filter_by(document_name=new_filename).first()

        # Create a blob client using the new unique filename
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)

        # Upload the file to Azure Blob Storage
        blob_client.upload_blob(file, overwrite=True)

        content = ocr.analyze_read(file.filename)

        blob_delete = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
        blob_delete.delete_blob()
        # Save the document details to the database
        # document = Documents(document_name=new_filename, email=email, content=content, username=username)
        # db.session.add(document)
        # db.session.commit()
        # return jsonify({"message": f"File '{new_filename}' uploaded successfully!", "filename": new_filename}), 200
        return jsonify({"content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# @views.route('/documents', methods=['GET'])
# @swag_from({
#     'tags': ['Documents'],
#     'description': 'Get all documents uploaded by the user',
#     'parameters': [
#         {
#             'name': 'userEmail',
#             'in': 'header',
#             'type': 'string',
#             'required': True,
#             'description': 'Email of the user making the request'
#         },
#     ],
#     'responses': {
#         200: {
#             'description': 'List of documents uploaded by the user'
#         },
#         400: {
#             'description': 'Bad request'
#         },
#         404: {
#             'description': 'No documents found'
#         },
#         500: {
#             'description': 'Internal server error'
#         }
#     }
# })
# def get_documents():
#     try:
#         email = request.headers.get('userEmail')
#         if email is None:
#             return jsonify({"error": "Please provide email in the request headers"}), 400

#         documents = Documents.query.filter_by(email=email).all()
#         if documents:
#             document_list = []
#             for document in documents:
#                 document_list.append({
#                     "document_id": document.id,
#                     "document_name": document.document_name,
#                     "content": document.content,
#                     "username": document.username
#                 })
#             return jsonify({"documents": document_list}), 200
#         else:
#             return jsonify({"message": "No documents found"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @views.route('/document/<int:document_id>', methods=['GET'])
# @swag_from({
#     'tags': ['Documents'],
#     'description': 'Get a specific document uploaded by the user',
#     'parameters': [
#         {
#             'name': 'userEmail',
#             'in': 'header',
#             'type': 'string',
#             'required': True,
#         },
#         {
#             'name': 'document_id',
#             'in': 'path',
#             'type': 'integer',
#             'required': True,
#             'description': 'ID of the document to retrieve'
#         }
#     ],
#     'responses': {
#         200: {
#             'description': 'Document retrieved successfully'
#         },
#         400: {
#             'description': 'Bad request'
#         },
#         404: {
#             'description': 'Document not found'
#         },
#         500: {
#             'description': 'Internal server error'
#         }
#     }
# })
# def get_document(document_id):
#     try:
#         email = request.headers.get('userEmail')
#         if email is None:
#             return jsonify({"error": "Please provide email in the request headers"}), 400
#         document = Documents.query.filter_by(id=document_id, email=email).first()
#         if document:
#             return jsonify({
#                 "document_id": document.id,
#                 "document_name": document.document_name,
#                 "content": document.content,
#                 "username": document.username
#             }), 200
#         else:
#             return jsonify({"message": "Document not found"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
# @views.route('/document/<int:document_id>', methods=['DELETE'])
# @swag_from({
#     'tags': ['Documents'],
#     'description': 'Delete a specific document uploaded by the user',
#     'parameters': [
#         {
#             'name': 'document_id',
#             'in': 'path',
#             'type': 'integer',
#             'required': True,
#             'description': 'ID of the document to delete'
#         },
#         {
#             'name': 'userEmail',
#             'in': 'header',
#             'type': 'string',
#             'required': True,
#             'description': 'Email of the user making the request'
#         }
#     ],
#     'responses': {
#         200: {
#             'description': 'Document deleted successfully'
#         },
#         400: {
#             'description': 'Bad request'
#         },
#         404: {
#             'description': 'Document not found'
#         },
#         500: {
#             'description': 'Internal server error'
#         }
#     }
# })
# def delete_document(document_id):
#     try:
#         email = request.headers.get('userEmail')
#         if email is None:
#             return jsonify({"error": "Please provide email in the request headers"}), 400

#         document = Documents.query.filter_by(id=document_id, email=email).first()
#         if document:
#             blob_name = document.document_name
#             blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
#             blob_client.delete_blob()

#             db.session.delete(document)
#             db.session.commit()
#             return jsonify({"message": "Document deleted successfully"}), 200
#         else:
#             return jsonify({"message": "Document not found"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @views.route('document-link/<int:document_id>', methods=['GET'])
# @swag_from({
#     'tags': ['Documents'],
#     'description': 'Get a link to a specific document uploaded by the user',
#     'parameters': [
#         {
#             'name': 'document_id',
#             'in': 'path',
#             'type': 'integer',
#             'required': True,
#             'description': 'ID of the document to get a link for'
#         },
#         {
#             'name': 'userEmail',
#             'in': 'header',
#             'type': 'string',
#             'required': True,
#             'description': 'Email of the user making the request'
#         }
#     ],
#     'responses': {
#         200: {
#             'description': 'Link to the document retrieved successfully'
#         },
#         400: {
#             'description': 'Bad request'
#         },
#         404: {
#             'description': 'Document not found'
#         },
#         500: {
#             'description': 'Internal server error'
#         }
#     }
# })
# def get_document_link(document_id):
#     try:
#         email = request.headers.get('userEmail')
#         if email is None:
#             return jsonify({"error": "Please provide email in the request headers"}), 400
#         document = Documents.query.filter_by(id=document_id, email=email).first()
        
#         if document:
#             link = getdocument.generate_blob_url(document.document_name)
#             return jsonify({"document_link": link}), 200
#         else:
#             return jsonify({"message": "Document not found"}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
@views.route('/query', methods=['POST'])
@swag_from({
    'tags': ['Chatbot'],
    'description': 'Route to query the chatbot',
    'parameters': [
        {
            'name': 'Content-Type',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Content type of the request body (e.g., application/json, application/xml, text/plain)'
        },
        {
            'name': 'userEmail',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Email of the user making the request'
        },
        {
            'name': 'userName',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Name of the user making the request'
        },
        {
            'name': 'conversationId',
            'in': 'header',
            'type': 'string',
            'required': False,
            'description': 'ID of the conversation'
        },
        {
            'name': 'document',
            'in': 'body',
            'type': 'string',
            'required': False,
            'description': 'The extracted text from the document, included only when user uploads a document'
        },
        {
            'name': 'userInput',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'user': {
                        'type': 'string',
                        'description': 'User input for the chatbot'
                    }
                },
                'required': ['user']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Successful response from the chatbot'
        },
        400: {
            'description': 'Bad request'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def query():
    # Conversation.clear_expired_conversations()
    try:
        email = request.headers.get('userEmail')
        username = request.headers.get('userName')
        conversation_id = request.headers.get('conversationId')
        if email is None or username is None:
            return jsonify({"error": "Please provide both email and username in the request headers"}), 400
        document = request.json.get("document")
        data = request.data
        user_input = None         
        content_type = request.headers.get('Content-Type')

        if content_type == 'application/json':
            user_input = request.json.get("user")
        elif content_type == 'application/xml':
            root = ET.fromstring(data)
            user_input = root.find('user').text 
        elif content_type == 'text/plain':
            user_input = data.decode('utf-8')
        elif content_type == 'text/html':
            pass
        if user_input:
            if conversation_id:
                conversation_item = Conversation.query.filter_by(conversation_id=conversation_id).first()
                if conversation_item:
                    conversation = conversation_item.content 
                    if document:                      
                        response = docformat.ai_search({"user_input": user_input, "document": document}, conversation)
                    else:
                        response = docformat.ai_search({"user_input": user_input, "document": None}, conversation)
                    docformat.set_conversation(response[1], conversation_id)
                return jsonify({"response": response[0]}), 200
            elif conversation_id is None:
                conversation_item = docformat.get_conversation()
                conversation = conversation_item[0]
                print(conversation)
                conversation_id = conversation_item[1]
                subject = docfreader.generate_subject(user_input)
                if document:
                    response = docformat.ai_search({"user_input": user_input, "document": document}, conversation)
                else:
                    response = docformat.ai_search({"user_input": user_input, "document": None}, conversation)
                docformat.new_conversation(email, username, response[1], conversation_id, subject)
                return jsonify({"response": response[0], "conversation_id": conversation_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@views.route('/delete-query/<string:conversation_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Chatbot'],
    'description': 'Delete a specific conversation',
    'parameters': [
        {
            'name': 'conversation_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID of the conversation to delete'
        },
        {
            'name': 'userEmail',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Email of the user making the request'
        }
    ],
    'responses': {
        200: {
            'description': 'Conversation deleted successfully'
        },
        404: {
            'description': 'Conversation not found'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def delete_query(conversation_id):
    try:
        userEmail = request.headers.get('userEmail')
        conversation = Conversation.query.filter_by(conversation_id=conversation_id, user_id=userEmail).first()
        if conversation:
            db.session.delete(conversation)
            db.session.commit()
            return jsonify({"message": "Conversation deleted successfully"}), 200
        else:
            return jsonify({"message": "Conversation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@views.route('/get-query/<string:conversation_id>', methods=['GET'])
@swag_from({
    'tags': ['Chatbot'],
    'description': 'Get a specific conversation',
    'parameters': [
        {
            'name': 'conversation_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'ID of the conversation to retrieve'
        },
        {
            'name': 'userEmail',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Email of the user making the request'
        }
    ],
    'responses': {
        200: {
            'description': 'Conversation retrieved successfully'
        },
        404: {
            'description': 'Conversation not found'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def get_query(conversation_id):
    try:
        userEmail = request.headers.get('userEmail')
        conversation = Conversation.query.filter_by(conversation_id=conversation_id, user_id=userEmail).first()
        if conversation:
            return jsonify({"subject": conversation.subject,
                            "conversation_id": conversation.conversation_id,
                            "username": conversation.username,
                            "content": conversation.content
                            }), 200
        else:
            return jsonify({"message": "Conversation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@views.route('/get-queries', methods=['GET'])
@swag_from({
    'tags': ['Chatbot'],
    'description': 'Get all conversations',
    'parameters': [
        {
            'name': 'userEmail',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Email of the user making the request'
        }
    ],
    'responses': {
        200: {
            'description': 'List of all conversations'
        },
        404: {
            'description': 'No conversations found'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def get_queries():
    try:
        userEmail = request.headers.get('userEmail')
        conversations = Conversation.query.filter_by(user_id=userEmail).all()
        if conversations:
            conversation_list = []
            for conversation in conversations:
                conversation_list.append({
                    "subject": conversation.subject,
                    "conversation_id": conversation.conversation_id,
                    "username": conversation.username,
                    "content": conversation.content
                })
            return jsonify({"conversations": conversation_list}), 200
        else:
            return jsonify({"message": "No conversations found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
from sqlalchemy.exc import ProgrammingError
@views.route("/delete-table", methods=['DELETE'])
def escalate():
    try:
        Documents.__table__.drop(db.engine)
        Conversation.__table__.drop(db.engine)       
        return jsonify({'message': 'Table dropped successfully'})
    except ProgrammingError:
        return jsonify({'message': 'Table does not exist'})
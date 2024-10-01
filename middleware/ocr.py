from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from .getdocument import generate_blob_url
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = os.environ.get("FORM_RECOGNIZER_ENDPOINT")
key = os.environ.get("FORM_RECOGNIZER_KEY")

def analyze_read(blob_name):
    document_url = generate_blob_url(blob_name) # Generate the URL to the document
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    
    poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-read", document_url)
    result = poller.result()

    # document_text = ""
    # print(result)
    
    # for page in result.pages:
    #     # print(result.pages)
    #     # Add page number to the output
    #     document_text += f"---- Page {page.page_number} ----\n"
        
    #     # Append the text from each line on the page
    #     for line in page.lines:
    #         document_text += f"{result.content}\n"

    # print(document_text)
    return result.content

# # URL to the document
# document_name = 'ANTI CORRUPTION POLICY.pdf'
# # Call the function to analyze the document
# analyze_read(document_name)



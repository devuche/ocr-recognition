# OCR Recognition Project

## Overview
This project is an Optical Character Recognition (OCR) system that allows users to upload documents, extract text from them, and perform various operations such as summarization and querying. The system leverages Azure Cognitive Services and OpenAI's GPT-4 for advanced natural language processing capabilities.

## Features
- **Document Upload**: Upload documents to Azure Blob Storage.
- **Text Extraction**: Extract text from uploaded documents using Azure Form Recognizer.
- **Search and Query**: Perform intelligent searches and queries on the extracted text.
- **Summarization**: Summarize the content of the documents.
- **Logging**: Comprehensive logging for monitoring and debugging.

## Technologies Used
- **Flask**: Web framework for building the API.
- **SQLAlchemy**: ORM for database interactions.
- **Azure Cognitive Services**: For OCR and text extraction.
- **OpenAI GPT-4**: For natural language processing.
- **Swagger**: API documentation.
- **Gunicorn**: WSGI HTTP server for running the application.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/OCR-Recognition.git
    cd OCR-Recognition
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following:
    ```properties
    OPENAI_API_TYPE="azure"
    OPENAI_API_BASE="https://your-openai-api-base/"
    OPENAI_API_VERSION="2024-05-01-preview"
    OPENAI_API_KEY="your-openai-api-key"
    DEPLOYMENT_NAME="HRbot"

    SERVICE_NAME="your-service-name"
    INDEX_NAME="your-index-name"
    SERVICE_KEY="your-service-key"

    DBUSER="your-db-user"
    PASSWORD="your-db-password"
    SERVER="your-db-server"
    DATABASE="your-database"
    DBPORT="your-db-port"

    SESSION_TYPE="filesystem"
    SECRET_KEY="your-secret-key"

    AZURE_STORAGE_CONNECTION_STRING="your-azure-storage-connection-string"
    STORAGE_KEY="your-storage-key"
    CONTAINER_NAME="your-container-name"
    STORAGE_ACCOUNT="your-storage-account"

    FORM_RECOGNIZER_ENDPOINT="your-form-recognizer-endpoint"
    FORM_RECOGNIZER_KEY="your-form-recognizer-key"

    BING_SEARCH_KEY="your-bing-search-key"
    ```

5. **Run the application**:
    ```bash
    python main.py
    ```

## Usage
- **Upload Document**: Use the `/upload-document` endpoint to upload a document.
- **Get Documents**: Use the `/documents` endpoint to retrieve all documents uploaded by a user.
- **Analyze Document**: Use the `/analyze-document` endpoint to extract text from a document.
- **Query**: Use the `/query` endpoint to query the chatbot
- **Get Query**: Use the `/query` or `/query/<string:conversation_id>` endpoint to get one or more queries
- **Update Conversation Subject**: Use the `/update-conversation-subject/<string:conversation_id>` endpoint to update a query subject
- **Delete Query**: Use the `/query/<string:conversation_id>` endpoint to delete a query

## API Documentation
API documentation is available via Swagger. Access it at `http://localhost:8000/apidocs`.

## Deployment
To deploy the application, use the provided `startup.txt` script:
```plaintext
gunicorn --bind=0.0.0.0 --workers=2 --threads=2 main:app
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License.

## Contact
For any inquiries, please contact Uchenna Nnamani at [nnamaniuchenna8@gmail.com].

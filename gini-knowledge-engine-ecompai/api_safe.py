from fastapi import FastAPI,  HTTPException #pip install python-multipart
import boto3
from botocore.exceptions import NoCredentialsError
# import streamlit as st
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
# from typing_extensions import override


# Initialize OpenAI client
client = OpenAI(
    api_key ='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'
)

class VectorStore:
    def __init__(self):
        self.assistantId = None
        self.verctorStoreId = None
    
    def add_assistant(self, id):
        self.assistantId = id
        
    def add_vector_store_id(self, id):
        self.verctorStoreId = id
         
    
vector_store_obj = VectorStore()

app = FastAPI()

# Initialize the S3 client
s3_client = boto3.client('s3')

# Replace 'your-s3-bucket-name' with your actual S3 bucket name
BUCKET_NAME = 'zapier-test-123'

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}


    
@app.post("/create-setup")
def create_setup():
    print("Setting Up")
    try:
        assistant = client.beta.assistants.create(
            name="Financial Analyst Assistant",
            instructions="You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )
            
        # Create a vector store
        vector_store = client.beta.vector_stores.create(name="Financial Insurance Statements")

        # Static file upload
        #file_paths = [".\books\JH-GHNW-ForeignNationalBrochure.pdf"]
        file_paths = ["/Users/testaccount/Documents/source/GINI-POC-main/books/JH-GHNW-ForeignNationalBrochure 2018.pdf"]
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
            
        # Update assistant with vector store
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )            
        
        vector_store_obj.add_assistant(assistant.id)
        vector_store_obj.add_vector_store_id(vector_store.id)
            
        return{
            "status": "success",
            "message": "Setup complete! Assistant and Vector Store are ready."
            }
        
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"{e}"
            }
        
        
@app.post("/ask-gini")
def ask_gini(user_input: str = "Hi!!"):
    if not vector_store_obj.assistantId:
        return {
            "message": "Setup Vector Store"
        }
        
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": user_input}]
    )
    
    thread_id = thread.id
    print(f"Thread created with question: {user_input}")
    
    response_data = {
        "response_text": "",
        "tool_calls": [],
        "citations": []
    }
    
    # Event handler for processing responses
    class EventHandler(AssistantEventHandler):
        @override
        def on_text_created(self, text) -> None:
            print(f"\nassistant > {text}", end="", flush=True)
            response_data["response_text"] = f"\nassistant > {text}"
            

        @override
        def on_tool_call_created(self, tool_call):
            print(f"\nassistant > {tool_call.type}\n", flush=True)
            
        

        @override
        def on_message_done(self, message) -> None:
            message_content = message.content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(
                    annotation.text, f"[{index}]"
                )
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            print(message_content.value)
            print("\n".join(citations))
            
    return response_data
    
    # Stream the assistant's response
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=vector_store_obj.assistantId,
        instructions="Please address the user as Jane Doe. The user has a premium account.",
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done() 
        return {}       
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

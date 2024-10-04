from fastapi import FastAPI,  HTTPException, Request,File, UploadFile
import boto3
import io
import json
from botocore.exceptions import NoCredentialsError
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
from pydantic import BaseModel

import logging

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI client
client = OpenAI(
    api_key ='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'
)
# Storing system prompt given by Shekhar
default_messages = [
                {"role": "user", "content": "What is the jumbo limit for C countries?"},
                {"role": "assistant", "content": "The jumbo limit for C countries is $45 million. This limit refers to the maximum total amount of in-force coverage plus pending formal applications with all companies, including John Hancock. If an existing insurance policy is being replaced, the amount of the policy being replaced will be deducted, provided that a fully executed absolute assignment transferring ownership to John Hancock is received(JH-GHNW-ForeignNational…)"},
                {"role": "user", "content": "What is the estate tax exemption for nonresident aliens?"},
                {"role": "assistant", "content": "The estate tax exemption for nonresident aliens is $60,000. This exemption amount is significantly lower than the exemption for U.S. citizens and resident aliens, which is over $5 million and indexed for inflation. The $60,000 exemption does not increase with inflation and applies specifically to U.S. situs property, which includes assets like U.S. real estate and tangible personal property located in the U.S.(JH-GHNW-ForeignNational…)."},
                {"role": "user", "content": "what is the annual exemption limit on gifts made by nonresidents?"},
                {"role": "assistant", "content": "The annual exemption limit on gifts made by nonresidents is $14,000 per recipient (as of 2016). Nonresidents do not have a lifetime gift exemption, so any gifts made that exceed this annual exclusion amount are subject to U.S. gift tax if the gift involves U.S. situs property, such as U.S.-based real estate or tangible personal property located in the U.S.(JH-GHNW-ForeignNational…)."},
                {"role": "user", "content": "How long does it take on an average to get the underwriting decision after the application is filed?"},
                {"role": "assistant", "content": "The document does not provide a specific average time frame for receiving an underwriting decision after an application is filed. However, the underwriting process for HNW foreign nationals typically involves several steps, including financial and medical underwriting, which may extend the time required to reach a decision. \
The duration can vary based on factors such as the completeness of the application, the complexity of the case, the speed at which required documents (e.g., medical records, financial statements) are provided, and whether any additional information or clarification is needed during the underwriting process. \
For more precise information, it's recommended to consult with the underwriter or representative handling the case, as they can provide a more accurate estimate based on the specifics of the application(JH-GHNW-ForeignNational…)."},
                {"role": "user", "content": "What is US Situs? Explain in 60 words"}, 
                {"role": "assistant", "content": "U.S. situs refers to assets that are considered located within the United States for tax purposes. For nonresident aliens, U.S. situs property includes U.S. real estate, tangible personal property located in the U.S., shares of stock in U.S. corporations, and certain other assets. These assets are subject to U.S. estate and gift taxes when owned by nonresident aliens(JH-GHNW-ForeignNational…)."},
                {"role": "user", "content": "How can a pilot buy survivorship policy?"},
                {"role": "assistant", "content": "A pilot can buy a survivorship policy, but there are specific restrictions. For individual policies, John Hancock may offer coverage to private pilots, but it will include an aviation exclusion rider, meaning the policy will not cover death resulting from aviation activities. However, for survivorship policies, where the policy insures two lives, coverage is not available if there is an aviation risk involved(JH-GHNW-ForeignNational…)."},
                {"role": "user", "content": "After selling the GNW policy to a foreign national, the company discovers that the policyholder is an accused in a corruption scandal in her home country. What action can be taken by the carrier?"},
                {"role": "assistant", "content": "If the carrier discovers that the policyholder is an accused in a corruption scandal, which might classify them as a Politically Exposed Person (PEP), they have the following options: \
Review of Policy: The carrier will likely conduct an internal review of the policy and the policyholder's background, given that PEPs or individuals involved in corruption can present a higher risk for money laundering or fraud. \
Policy Rescission: If it is determined that material information was not disclosed during the application process, such as involvement in criminal activities or corruption, the carrier may have grounds to rescind the policy, effectively canceling it and refunding premiums paid. \
Enhanced Monitoring: If the policy is not rescinded, the carrier might place the policyholder under enhanced scrutiny, which could include monitoring for suspicious activity or requiring additional documentation for any transactions.\
Legal and Regulatory Compliance: The carrier may be obligated to report the policyholder to relevant authorities under anti-money laundering (AML) and Know Your Customer (KYC) regulations, particularly if the policyholder's activities are deemed suspicious."}               
                ]

class AskGiniHelper:
    def __init__(self):
        self.assistantId = None
        self.verctorStoreId = None
        self.threadId = None
    
    def add_assistant(self, id):
        self.assistantId = id
        
    def add_vector_store_id(self, id):
        self.verctorStoreId = id    
      
 
ask_gini_helper_obj = AskGiniHelper()

app = FastAPI()

# Initialize the S3 client
s3_client = boto3.client('s3')

# Replace 'your-s3-bucket-name' with your actual S3 bucket name
BUCKET_NAME = 'ecompai'

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read the file contents
        file_contents = await file.read()
        
        print(f"Uploading {file.filename}")

        # Upload the file to S3
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file.filename, Body=file_contents)

        return {"message": f"File '{file.filename}' uploaded successfully"}

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/create-setup")
def create_setup():
    print("Setting Up")
    logging.info("Setting Up")
    try:
        assistant = client.beta.assistants.create(
            name="Financial Analyst Assistant",
            instructions="You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
        )
            
        # Create a vector store
        vector_store = client.beta.vector_stores.create(name="Financial Insurance Statements")    
        
         # List PDF files in the S3 bucket
        s3_objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        pdf_files = [obj['Key'] for obj in s3_objects.get('Contents', []) if obj['Key'].endswith('.pdf')]
        print(f"pdf_files>>>> {pdf_files}")
        
        file_streams = []
        
        # Download each PDF file from S3
        for pdf_file in pdf_files:
            logging.info(f"Downloading {pdf_file} from S3")
            s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=pdf_file)
            # Read the content of the S3 object and store it in memory
            file_content = s3_response['Body'].read()

            # Convert the in-memory bytes to a file-like object
            file_stream = io.BytesIO(file_content)
            file_stream.name = pdf_file
            file_streams.append(file_stream)
            
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )
            
        # Update assistant with vector store
        assistant = client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )            
        
        ask_gini_helper_obj.add_assistant(assistant.id)
        ask_gini_helper_obj.add_vector_store_id(vector_store.id)
            
        return{
            "status": "success",
            "message": "Setup complete! Assistant and Vector Store are ready."
            }
        
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"{e}"
            }

# New API to ask questions and get answers based on the context
class QuestionRequest(BaseModel):
    query: str
    threadId: str | None = None
 # Fetched the value of the main_question flag
    main_question: bool
    

@app.post("/ask-gini")
def ask_question(request: QuestionRequest):
    response = []

    if request.threadId:        
        threadId = request.threadId
        print(f"Utilizing Previous thread with ID - {threadId}")
    else:
    # Create a thread and ask the question
        thread = client.beta.threads.create(
    # Creates a new thread. While creating the knowledge engine provides the system prompt, only the very first time for an user 
            messages=default_messages
        )
        threadId = thread.id
        print(f"Creating a new thread with ID - {threadId}")
    
        
    logging.info(f"Thread created with question: {request.query}")
    
  # Check is main_question's value is "true"
    if request.main_question:
        instruction = """The user has a premium account.
            Response should be in json format 
            Output should contain below keys:
            textual_response (string),
            action_plan (list of objects having steps (string) and details(string)),
            workflow (object having action_step (string) and tasks (list of strings)),
            do not add json codes. Just give me json output only
            do not provide non json response
            
            The reponse needs to work when I run json.loads()
        """
        additional_message = [{"role": "user", "content": request.query}]
    else:
    # if the main_question's value is "false" requesting the knowledge engine to display the details in html format.
        instruction = """Response should be in full page HTML Format. It should not be just string. When it is placed in '.html' file it should create a webpage and should not give any error """
        additional_message = [{"role": "user", "content": f"{request.query}\n Provide me the response strictly in HTML Format"}]
            
    run = client.beta.threads.runs.create_and_poll(
    thread_id=threadId, assistant_id=ask_gini_helper_obj.assistantId,
    additional_messages=additional_message,
    instructions=instruction
        
        
            # under textual response provide an analysis on the factors which helps to reduce or increase the premium amount
            # under action plan provide the list of steps and details
            # under workflow provide action_step and tasks
    
    )

    messages = list(client.beta.threads.messages.list(thread_id=threadId, run_id=run.id))

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    print(message_content.value)
    response.append({
        "response": json.loads(message_content.value) if request.main_question else message_content.value,
        "threadId": threadId
        })
    print("\n".join(citations))

    return response


create_setup()

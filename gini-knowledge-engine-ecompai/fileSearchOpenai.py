import streamlit as st
from openai import OpenAI, AssistantEventHandler
from typing_extensions import override

# Initialize OpenAI client
client = OpenAI(
    api_key ='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'
)

#openai.api_key = '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'

# Static Setup: Create Assistant and Vector Store, Upload Files
def setup_assistant_and_store():
    # Create the assistant
    assistant = client.beta.assistants.create(
        name="Financial Analyst Assistant",
        instructions="You are an expert financial analyst. Use your knowledge base to answer questions about audited financial statements.",
        #model="gpt-4o",
        #model="gpt-3.5-turbo",
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
    )
    
    # Create a vector store
    vector_store = client.beta.vector_stores.create(name="Financial Insurance Statements")
    
    # Static file upload
    #file_paths = ["./books/JH-GHNW-ForeignNationalBrochure 2018.pdf"]
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
    
    # Store the assistant and vector store IDs
    st.session_state["assistant_id"] = assistant.id
    st.session_state["vector_store_id"] = vector_store.id
    st.success("Setup complete! Assistant and Vector Store are ready.")

# Run setup once at startup
if "assistant_id" not in st.session_state:
    setup_assistant_and_store()

# Streamlit UI for asking questions
st.title("Ask Gini")

# Input for user's question
user_input = st.text_input("Ask a question to GINI")

if st.button("Submit") and user_input:
    # Create a thread and ask the question
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": user_input}]
    )
    st.session_state["thread_id"] = thread.id
    st.write(f"Thread created with question: {user_input}")

    # Event handler for processing responses
    class EventHandler(AssistantEventHandler):
        @override
        def on_text_created(self, text) -> None:
            st.write(f"\nassistant > {text}", end="", flush=True)

        @override
        def on_tool_call_created(self, tool_call):
            st.write(f"\nassistant > {tool_call.type}\n", flush=True)

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

            st.write(message_content.value)
            st.write("\n".join(citations))

    # Stream the assistant's response
    with client.beta.threads.runs.stream(
        thread_id=st.session_state["thread_id"],
        assistant_id=st.session_state["assistant_id"],
        instructions="Please address the user as Jane Doe. The user has a premium account.",
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

import streamlit as st
import ollama
import re
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb

# Initialize Chroma DB client
client = chromadb.PersistentClient(path='database')

# Check if collection exists before creating it
collection_name = "newdb"
existing_collections = [col.name for col in client.list_collections()]

if collection_name in existing_collections:
    my_collection = client.get_collection(name=collection_name)
else:
    my_collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

class RecursiveChunker:
    def __init__(self, model_name="BAAI/bge-large-en-v1.5", max_chunk_size=150):
        self.embeddings_model = HuggingFaceEmbeddings(model_name=model_name)
        self.chunks = []
        self.ids = []
        self.chunk_embeddings = []
        self.collection = my_collection
        self.max_chunk_size = max_chunk_size

    def chunk_text(self, text):
        paragraphs = text.split('\n\n')
        self.chunks = []

        for paragraph in paragraphs:
            if len(paragraph.split()) > self.max_chunk_size:
                indented_chunks = self.recursive_chunk_text(paragraph)
                self.chunks.extend(indented_chunks)
            else:
                self.chunks.append(paragraph)

    def recursive_chunk_text(self, text):
        words = text.split()
        if len(words) <= self.max_chunk_size:
            return [text]
        split_point = self.max_chunk_size
        while split_point > 0 and not words[split_point - 1].endswith(('.', '!', '?')):
            split_point -= 1
        if split_point == 0:
            split_point = self.max_chunk_size
        chunk = ' '.join(words[:split_point])
        remaining_text = ' '.join(words[split_point:])
        return [chunk] + self.recursive_chunk_text(remaining_text)

    def embed_chunks(self):
        self.chunk_embeddings = self.embeddings_model.embed_documents(self.chunks)
        self.ids = [f"idx{i+1}" for i in range(len(self.chunks))]
        self.collection.add(
            embeddings=self.chunk_embeddings,
            documents=self.chunks,
            ids=self.ids
        )

    def embed_query(self, query):
        return self.embeddings_model.embed_documents([query])[0]

    def search_similar_chunks(self, query_embedding, top_k=3):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        similar_chunks = []
        for doc, score in zip(results['documents'][0], results['distances'][0]):
            similar_chunks.append((doc, score))
        return similar_chunks

class Chatbot:
    def __init__(self, model_name="BAAI/bge-large-en-v1.5", max_chunk_size=150):
        self.chunker = RecursiveChunker(model_name, max_chunk_size)
        self.model = "deepseek-r1:1.5b"

    def process_document(self, text):
        self.chunker.chunk_text(text)
        self.chunker.embed_chunks()

    def query(self, user_query):
        query_embedding = self.chunker.embed_query(user_query)
        similar_chunks = self.chunker.search_similar_chunks(query_embedding, top_k=3)

        # Concatenate chunks into a single string
        result_string = "\n\n".join([chunk for chunk, _ in similar_chunks])

        # Use LLM to generate response
        system_part = (
            "You are an expert in Question and Answering. "
            "Answer the Question by only using the text below. "
            "If the answer isn't present in the text, respond with "
            "'I am sorry. I don't know the answer.'\n\n"
            f"Context: {result_string}"
        )

        messages = [
            {"role": "system", "content": system_part},
            {"role": "user", "content": user_query}
        ]
        
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"temperature": 0.7, "num_ctx": 7000}
        )
        return response['message']['content']

# Streamlit UI
st.title("🤖 RAG Chatbot")

# Initialize chatbot in session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chatbot()

# Initialize session state for tracking document upload
if "docs_uploaded" not in st.session_state:
    st.session_state.docs_uploaded = False

# User inputs
user_prompt = st.text_area("Enter your question:", "")
model_name = st.text_input("Enter model name:", "deepseek-r1:1.5b")

# File upload section
uploaded_file = st.file_uploader("Upload a text file", type=["txt"])

# Process file content if uploaded
if uploaded_file and not st.session_state.docs_uploaded:
    file_content = uploaded_file.read().decode("utf-8")
    
    with st.spinner("Processing document... This might take a while."):
        st.session_state.chatbot.process_document(file_content)
    
    st.success("✅ Document processed and embedded successfully!")
    st.session_state.docs_uploaded = True

# Multiple queries allowed without re-uploading
if st.button("Generate Response"):
    if user_prompt and st.session_state.docs_uploaded:
        with st.spinner("Generating response..."):
            response = st.session_state.chatbot.query(user_prompt)
            cleaned_text = re.sub(r"<think>.*?</think>\s*", "", response, flags=re.DOTALL)
 
            # Display response
            st.subheader("📝 Response:")
            st.write(cleaned_text)

    elif not st.session_state.docs_uploaded:
        st.warning("Please upload a document first.")
    else:
        st.warning("Please enter a question.")

# Button to reset chatbot and upload a new file
if st.button("Upload New File"):
    st.session_state.docs_uploaded = False
    st.rerun()

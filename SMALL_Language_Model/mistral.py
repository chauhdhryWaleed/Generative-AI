import os
from langchain_community.llms import CTransformers
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferMemory
model_id="TheBloke/Mistral-7B-codealpaca-lora-GGUF"
config= { 'temperature':0.00, 'context_length':4000,}
llm=CTransformers(model=model_id, model_type='mistral', config=config, callbacks=[StreamingStdOutCallbackHandler()])
# Query or input to the model
def interact_with_model():
    while True:
        # Prompt user for input
        input_text = input("Enter your query (type 'exit' to quit): ")

        # Check if user wants to exit
        if input_text.lower() == 'exit':
            print("Exiting...")
            break
        
        # Send the input to the model for processing
        response = llm.invoke(input_text)
      
        # Print the response
        print("Response:", response)
        print("-" * 50)

# Example usage
if __name__ == "__main__":
    interact_with_model()

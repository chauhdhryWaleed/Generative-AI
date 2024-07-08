import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pandas as pd 
import streamlit as st
import argparse


pd.set_option('display.max_columns', 4)

# def view_collections(dir):
#     st.markdown("### DB Path: %s" % dir)
  
#     client = chromadb.PersistentClient(path=dir)

#     # This might take a while in the first execution if Chroma wants to download
#     # the embedding transformer
#     collections = client.list_collections()
 
#     st.header("Collections")

#     for collection in collections:
#         data = collection.get()
#         print(collection.name)
      
#         ids = data['ids']
#         embeddings = data["embeddings"]
#         metadata = data["metadatas"]
#         documents = data["documents"]

#         df = pd.DataFrame.from_dict(data)
#         st.markdown("### Collection: **%s**" % collection.name)
#         st.dataframe(df)

# # Specify the path to your Chroma DB storage
# db_path = "F:/BITPIX/BITPIX/week3/database"

# # Directly call the function with the path
# view_collections(db_path)



def view_collections(dir):
    st.markdown("### DB Path: %s" % dir)
  
    client = chromadb.PersistentClient(path=dir)

    # This might take a while in the first execution if Chroma wants to download
    # the embedding transformer
    collections = client.list_collections()
 
    st.header("Collections")

    for collection in collections:
        data = collection.get()
      
        # Ensure all arrays are lists or default to empty lists if None
        ids = data.get('ids', []) or []
        embeddings = data.get('embeddings', []) or []
        metadata = data.get('metadatas', []) or []
        documents = data.get('documents', []) or []

        # Calculate max_length based on the longest list among ids, embeddings, metadata, and documents
        max_length = max(len(ids), len(embeddings), len(metadata), len(documents))

        # Pad arrays with None to ensure equal length
        ids += [None] * (max_length - len(ids))
        embeddings += [None] * (max_length - len(embeddings))
        metadata += [None] * (max_length - len(metadata))
        documents += [None] * (max_length - len(documents))

        data = {
            'ids': ids,
            'embeddings': embeddings,
            'metadatas': metadata,
            'documents': documents
        }

        df = pd.DataFrame(data)
        st.markdown("### Collection: **%s**" % collection.name)
        st.dataframe(df)


db_path = "F:/BITPIX/BITPIX/week3/database"

# Directly call the function with the path
view_collections(db_path)
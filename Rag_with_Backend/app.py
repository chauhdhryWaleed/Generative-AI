from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import execute_values
import numpy as np
from psycopg2 import sql
from lightrag.core.embedder import Embedder
from lightrag.core.types import ModelClientType
from lightrag.components.data_process.text_splitter import TextSplitter
from lightrag.components.data_process import  ToEmbeddings
from lightrag.core.container import Sequential
from lightrag.components.model_client import TransformersClient
from lightrag.components.retriever.postgres_retriever import PostgresRetriever
from lightrag.core.types import Document
from lightrag.components.retriever.postgres_retriever import DistanceToOperator
import hashlib
import logging


# Connect to PostgreSQL
host = "localhost"  # or Docker container IP
port = "5432"
database = "postgres"
user = "postgres"
password = "mysecretpassword"
connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"


logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

model_kwargs = {
    "model": "thenlper/gte-base",
    "dimensions": 256,
    "encoding_format": "float",
}
local_embedder = Embedder(model_client=TransformersClient(), model_kwargs=model_kwargs)


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        app.logger.info("INSIDE THE upload_file FUNCTION")
        
        # Extract tenant_id and customer_id from form data
        tenant_id = request.form.get('tenant_id')
        customer_id = request.form.get('customer_id')
        file = request.files.get('file')

        # Check for missing fields
        if not all([tenant_id, customer_id, file]):
            return jsonify({"error": "Missing tenant_id, customer_id, or file"}), 400

        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Ensure the schema and table exist
        create_schema_query = sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema_name}").format(
            schema_name=sql.Identifier(tenant_id)
        )
        cursor.execute(create_schema_query)

        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                chunk_id SERIAL PRIMARY KEY,
                file_name TEXT,
                file_hash TEXT, 
                chunk_index INT,          
                chunk_content TEXT,
                embedding vector(768)
            )
        """).format(
            schema_name=sql.Identifier(tenant_id),
            table_name=sql.Identifier(customer_id)
        )
        cursor.execute(create_table_query)

        # Compute file hash
        file_text = file.read().decode('utf-8')
        file_hash = hashlib.sha256(file_text.encode('utf-8')).hexdigest()

        # Check if a file with the same name already exists
        check_file_name_query = sql.SQL("""
            SELECT file_hash FROM {schema_name}.{table_name} WHERE file_name = %s LIMIT 1
        """).format(
            schema_name=sql.Identifier(tenant_id),
            table_name=sql.Identifier(customer_id)
        )
        cursor.execute(check_file_name_query, (file.filename,))
        existing_file_hash = cursor.fetchone()


        p=False
        if existing_file_hash:
            if existing_file_hash[0] == file_hash:
                return jsonify({"message": "File with the same name and content already exists"}), 200
            else:
                # Delete existing rows with the same filename
                delete_existing_rows_query = sql.SQL("""
                    DELETE FROM {schema_name}.{table_name} WHERE file_name = %s
                """).format(
                    schema_name=sql.Identifier(tenant_id),
                    table_name=sql.Identifier(customer_id)
                )
                p=True
                cursor.execute(delete_existing_rows_query, (file.filename,))

        # Process file
        chunks, embeddings = process(connection_string, file_text)

        # Retrieve the maximum chunk_index for new chunks
        max_chunk_index_query = sql.SQL("""
            SELECT COALESCE(MAX(chunk_index), 0) FROM {schema_name}.{table_name}
        """).format(
            schema_name=sql.Identifier(tenant_id),
            table_name=sql.Identifier(customer_id)
        )
        cursor.execute(max_chunk_index_query)
        max_chunk_index = cursor.fetchone()[0]

        # Prepare data for insertion
        data = [(chunks[i], max_chunk_index + i + 1, file.filename, file_hash, embeddings[i]) for i in range(len(chunks))]

        insert_query = sql.SQL("""
            INSERT INTO {schema_name}.{table_name} (chunk_content, chunk_index, file_name, file_hash, embedding)
            VALUES %s
        """).format(
            schema_name=sql.Identifier(tenant_id),
            table_name=sql.Identifier(customer_id)
        )

        execute_values(cursor, insert_query, data)

        # Commit changes and close connection
        connection.commit()
        cursor.close()
        connection.close()

        # Return success response
        response = {
            "message": "File received and processed successfully",
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "file_name": file.filename,
            "file_hash": file_hash,
            "chunks": chunks,
            "max_chunk_index": max_chunk_index,
            "Previous deleted":p
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process(connection_string, content):
    try:
        text_splitter = TextSplitter(
            split_by="sentence",
            chunk_size=5,
            chunk_overlap=0
        )
        doc = Document(text=content, id="doc1")
        splitted_docs = text_splitter.call(documents=[doc])
        
        chunks = [doc.text for doc in splitted_docs]
        output = local_embedder(input=[doc.text for doc in splitted_docs])
        documents_embeddings = [x.embedding for x in output.data]

        output_file_path = "splitted_docs.txt"
        i = 0

        with open(output_file_path, 'w') as file:
            for doc in splitted_docs:
                file.write(str(i))
                file.write(doc.text)  # Write each chunk followed by a newline
                file.write('\n')
                i += 1
        
        return chunks, documents_embeddings
    except Exception as e:
        app.logger.error(f"Error in process function: {e}")
        raise

@app.route('/delete', methods=['DELETE'])
def delete_file():
    try:
        # Extract tenant_id, customer_id, and file_name from query parameters
        tenant_id = request.args.get('tenant_id')
        customer_id = request.args.get('customer_id')
        file_name = request.args.get('file_name')

        # Log the received values
        app.logger.info(f"Received tenant_id: {tenant_id}")
        app.logger.info(f"Received customer_id: {customer_id}")
        app.logger.info(f"Received file_name: {file_name}")

        # Debugging: Print the values to the console
        print(f"Received tenant_id: {tenant_id}")
        print(f"Received customer_id: {customer_id}")
        print(f"Received file_name: {file_name}")

        # Check if all required fields are provided
        if not all([tenant_id, customer_id, file_name]):
            return jsonify({"error": "Missing tenant_id, customer_id, or file_name"}), 400

        # Connect to PostgreSQL
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        # Construct and execute the delete query
        delete_query = sql.SQL("""
            DELETE FROM {schema_name}.{table_name} 
            WHERE file_name = %s
        """).format(
            schema_name=sql.Identifier(tenant_id),
            table_name=sql.Identifier(customer_id)
        )
        cursor.execute(delete_query, (file_name,))

        # Check how many rows were deleted
        rows_deleted = cursor.rowcount

        # Commit the changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()

        if rows_deleted == 0:
            return jsonify({"message": "No rows found for the given file name."}), 404

        # Return a success response
        return jsonify({"message": f"Successfully deleted {rows_deleted} rows where file_name = '{file_name}'."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/result', methods=['POST'])
def get_result():
    try:
        # Open a new database connection
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        # Execute your query
        cursor.execute("SELECT embedding from my_schema4.my_table")
        result = cursor.fetchall()

        # Close the connection
        cursor.close()
        connection.close()

        # Return the response
        return jsonify({"query_result": result}), 200

    except Exception as e:
        # Handle the exception and close the connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve', methods=['POST'])
def getAnswer():
    try:

        tenant_id = request.form.get('tenant_id')
        customer_id = request.form.get('customer_id')
        query = request.form.get('query')
        similarity=request.form.get('similarity')

       

        list_similarity=["L2","L1","COSINE","INNER_PRODUCT"]
        
        list_similarity = ["L2", "L1", "COSINE", "INNER_PRODUCT"]

        if similarity not in list_similarity:
            return jsonify({
                "Error": "Invalid similarity type provided. Please use one of the following: " + ", ".join(list_similarity),
                "wHAT YOU SENT":similarity,
            }), 400

        operator = getattr(DistanceToOperator, similarity)

        retreiver=  PostgresRetriever(embedder=local_embedder,database_url=connection_string,distance_operator=operator)

        table=f"{tenant_id}.{customer_id}"  #imo should add schema.table_name will test on monday
        vector_column="embedding"   # same here
        output=local_embedder(query)
        top_k=8
        query_embedding = output.data[0].embedding
    

        result=retreiver.format_vector_search_query(table_name=table,vector_column="embedding",query_embedding=query_embedding,top_k=top_k,distance_operator=retreiver.distance_operator,sort_desc=False)
        

        results=retreiver.retrieve_by_sql(result)

        # Return the response
        return jsonify({"query_result": results}), 200

    except Exception as e:
        
        return jsonify({"error": str(e),
                        "tenant_id": tenant_id,
                        "customer_id": customer_id,
                        "query": query,
                        "table_name":table,
                        "vector_column":vector_column,
                        "Operator Name":operator
                        }), 500

def rag(connection_string,query):
    
    retreiver=  PostgresRetriever(embedder=local_embedder,database_url=connection_string)

    table_name="my_table"  #imo should add schema.table_name will test on monday
    vector_column="embedding"   # same here
    output=local_embedder(query)
    top_k=3
    for x in output.data:
        query_embedding=x.embedding

    retreiver.format_vector_search_query(table_name)

if __name__ == '__main__':
    app.run(debug=False)



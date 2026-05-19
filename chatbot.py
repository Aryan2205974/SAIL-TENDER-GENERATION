from sentence_transformers import SentenceTransformer
import pandas as pd
import snowflake.connector
import faiss
import numpy as np
import ollama

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect Snowflake
conn = snowflake.connector.connect(
    user='Aryan',
    password='Aryan@7250544320',
    account='jb49688.ap-southeast-1',
    warehouse='COMPUTE_WH',
    database='SUPPORT_BOT_DB',
    schema='SUPPORT_SCHEMA'
)

# Fetch data
query = "SELECT ticket_id, issue, resolution FROM support_tickets"

df = pd.read_sql(query, conn)

# Combine text
df['combined'] = df['ISSUE'] + " " + df['RESOLUTION']

# Generate embeddings
embeddings = model.encode(df['combined'].tolist())

# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(embeddings))

# User query
user_query = input("Ask your issue: ")

# Query embedding
query_embedding = model.encode([user_query])

# Search
D, I = index.search(np.array(query_embedding), k=2)

# Retrieved context
context = ""

for idx in I[0]:
    context += df.iloc[idx]['ISSUE'] + "\n"
    context += df.iloc[idx]['RESOLUTION'] + "\n\n"

# Prompt
prompt = f"""
Answer the customer query using the support ticket context.

Customer Query:
{user_query}

Context:
{context}
"""

# Generate response
response = ollama.chat(
    model='mistral',
    messages=[
        {'role': 'user', 'content': prompt}
    ]
)

print("\nAI Response:\n")
print(response['message']['content'])
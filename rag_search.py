from sentence_transformers import SentenceTransformer
import pandas as pd
import snowflake.connector
import faiss
import numpy as np

# Load embedding model
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

# Combine text columns
df['combined'] = df['ISSUE'] + " " + df['RESOLUTION']

# Generate embeddings
embeddings = model.encode(df['combined'].tolist())

# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(np.array(embeddings))

# User query
user_query = "login problem"

# Convert query to embedding
query_embedding = model.encode([user_query])

# Search top 2 similar records
D, I = index.search(np.array(query_embedding), k=2)

print("Matching Indexes:")
print(I)

print("\nMost Similar Tickets:\n")

for idx in I[0]:
    print(df.iloc[idx]['ISSUE'])
    print(df.iloc[idx]['RESOLUTION'])
    print("-" * 50)
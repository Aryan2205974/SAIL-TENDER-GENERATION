from sentence_transformers import SentenceTransformer
import pandas as pd
import snowflake.connector

model = SentenceTransformer('all-MiniLM-L6-v2')

conn = snowflake.connector.connect(
    user='Aryan',
    password='Aryan@7250544320',
    account='jb49688.ap-southeast-1',
    warehouse='COMPUTE_WH',
    database='SUPPORT_BOT_DB',
    schema='SUPPORT_SCHEMA'
)

query = "SELECT ticket_id, issue, resolution FROM support_tickets"

df = pd.read_sql(query, conn)

print(df.columns)

df['combined'] = df['ISSUE'] + " " + df['RESOLUTION']

embeddings = model.encode(df['combined'].tolist())

print(embeddings.shape)
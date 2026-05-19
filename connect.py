import snowflake.connector
import pandas as pd

conn = snowflake.connector.connect(
    user='Aryan',
    password='Aryan@7250544320',
    account='jb49688.ap-southeast-1',
    warehouse='COMPUTE_WH',
    database='SUPPORT_BOT_DB',
    schema='SUPPORT_SCHEMA',
    role='ACCOUNTADMIN'
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM support_tickets")

for row in cursor.fetchall():
    print(row)
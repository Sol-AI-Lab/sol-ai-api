from hackathons import search_excel_records, create_tables

create_tables()

results = search_excel_records(
    excel_file='./context/hackathons/colloseum/renaissance-hackathon-projects.xlsx',
    query='What projects are related with Bonk token?',
    text_column='Description',
    sheet_name=0,
    top_n=20
)

print(results)
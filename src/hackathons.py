import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from typing import List, Optional
import sqlite3
import os.path

from src.database import engine, get_db, Base
from src.models import RenaissanceHackathonProject, RadarHackathonProject, BreakoutHackathonProject

def ensure_db_exists():
    """
    Check if the database file exists, and create it if it doesn't.
    """
    db_path = "./hackathons.db" 
    
    if not os.path.exists(db_path):
        print(f"Database file not found. Creating new database at {db_path}")
        conn = sqlite3.connect(db_path)
        conn.close()
        
        Base.metadata.create_all(bind=engine)
        print("Database and tables created successfully")
    else:
        Base.metadata.create_all(bind=engine)
        print("Database exists, ensuring all tables are created")

def create_tables():
    """
    Create all database tables if they don't exist.
    """
    ensure_db_exists()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def extract_hyperlinks_from_excel(excel_file):
    """
    Extract hyperlinks from Excel cells.
    Returns a DataFrame with the same structure but with hyperlink information.
    """
    import openpyxl
    
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active
    
    hyperlinks = {}
    
    for cell in sheet._cells.values():
        if cell.hyperlink:
            hyperlinks[(cell.row, cell.column)] = {
                'text': cell.value,
                'url': cell.hyperlink.target
            }
    
    df = pd.read_excel(excel_file)
    
    df['Project_Link'] = None
    df['Presentation_Link_URL'] = None
    df['Repo_Link_URL'] = None
    df['Technical_Demo_Link_URL'] = None
    
    is_breakout = 'Technical Demo Link' in df.columns
    
    col_mapping = {
        'Project': 1,
        'Presentation Link': 7,
        'Repo Link': 8,
    }
    
    if is_breakout:
        col_mapping['Technical Demo Link'] = 8
        col_mapping['Repo Link'] = 9
    
    for i, row in df.iterrows():
        excel_row = i + 2
        
        if (excel_row, col_mapping['Project']) in hyperlinks:
            link_info = hyperlinks[(excel_row, col_mapping['Project'])]
            df.at[i, 'Project_Link'] = link_info['url']
        
        if (excel_row, col_mapping['Presentation Link']) in hyperlinks:
            link_info = hyperlinks[(excel_row, col_mapping['Presentation Link'])]
            df.at[i, 'Presentation_Link_URL'] = link_info['url']
        
        if (excel_row, col_mapping['Repo Link']) in hyperlinks:
            link_info = hyperlinks[(excel_row, col_mapping['Repo Link'])]
            df.at[i, 'Repo_Link_URL'] = link_info['url']
        
        if is_breakout and (excel_row, col_mapping['Technical Demo Link']) in hyperlinks:
            link_info = hyperlinks[(excel_row, col_mapping['Technical Demo Link'])]
            df.at[i, 'Technical_Demo_Link_URL'] = link_info['url']
    
    return df

def search_excel_records(excel_file, query, text_column, sheet_name=0, top_n=20, sync_with_db=True, hackathon="renaissance"):
    """
    Search Excel records based on semantic similarity to a query.
    If sync_with_db is True, also adds any new projects to the database.
    """
    create_tables()
    
    try:
        df = extract_hyperlinks_from_excel(excel_file)
    except Exception as e:
        print(f"Error extracting hyperlinks: {str(e)}. Falling back to basic Excel reading.")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    if hackathon.lower() == "breakout" and len(df) > 0:
        if "Solana Breakout Hackathon project directory" in str(df.iloc[0].values[0]):
            df = df.iloc[1:].reset_index(drop=True)
    
    if sync_with_db:
        sync_excel_with_database(df, hackathon)
    
    if text_column not in df.columns:
        print(f"Warning: Column '{text_column}' not found in Excel file. Available columns: {df.columns.tolist()}")
        potential_columns = ['Description', 'description', 'Project', 'project']
        for col in potential_columns:
            if col in df.columns:
                text_column = col
                print(f"Using '{text_column}' column instead")
                break
        else:
            text_column = df.columns[0]
            print(f"No suitable text column found. Using '{text_column}' column")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query_embedding = model.encode([query])
    
    record_embeddings = model.encode(df[text_column].fillna('').tolist())
    
    similarity_scores = cosine_similarity(query_embedding, record_embeddings)[0]
    
    df['similarity_score'] = similarity_scores
    df['hackathon'] = hackathon
    
    results = df.sort_values('similarity_score', ascending=False).head(top_n)
    
    return results

def sync_excel_with_database(df, hackathon="renaissance"):
    """
    Syncs Excel data with the database, adding ONLY projects that don't exist yet.
    Properly handles link columns.
    
    Args:
        df: DataFrame containing project data
        hackathon: Which hackathon the data belongs to ("renaissance", "radar", "breakout")
    """
    create_tables()
    
    db = get_db()
    
    try:
        if hackathon.lower() == "renaissance":
            model_class = RenaissanceHackathonProject
        elif hackathon.lower() == "radar":
            model_class = RadarHackathonProject
        elif hackathon.lower() == "breakout":
            model_class = BreakoutHackathonProject
        else:
            raise ValueError(f"Unknown hackathon type: {hackathon}")
            
        existing_projects_raw = db.query(model_class.project).all()
        
        if existing_projects_raw:
            existing_projects = {project[0].lower(): project[0] for project in existing_projects_raw}
        else:
            existing_projects = {}
        
        new_projects_added = 0
        
        for _, row in df.iterrows():
            if 'Project' not in row or pd.isna(row['Project']):
                continue
            
            project_name = row['Project']
            
            project_link = row['Project_Link'] if 'Project_Link' in row and pd.notna(row['Project_Link']) else None
            presentation_link = row['Presentation_Link_URL'] if 'Presentation_Link_URL' in row and pd.notna(row['Presentation_Link_URL']) else row.get('Presentation Link')
            repo_link = row['Repo_Link_URL'] if 'Repo_Link_URL' in row and pd.notna(row['Repo_Link_URL']) else row.get('Repo Link')
            
            if presentation_link == "Presentation Link":
                presentation_link = None
            if repo_link == "Repo Link":
                repo_link = None
            
            project_name_lower = project_name.lower()
            
            if project_name_lower not in existing_projects:
                project_data = {
                    "project": project_name,
                    "project_link": project_link,
                    "description": row['Description'] if 'Description' in row and pd.notna(row['Description']) else None,
                    "country": row['Country'] if 'Country' in row and pd.notna(row['Country']) else None,
                    "additional_info": row['Additional Info'] if 'Additional Info' in row and pd.notna(row['Additional Info']) else None,
                    "tracks": row['Tracks'] if 'Tracks' in row and pd.notna(row['Tracks']) else None,
                    "team_members": row['Team Members'] if 'Team Members' in row and pd.notna(row['Team Members']) else None,
                    "presentation_link": presentation_link,
                    "repo_link": repo_link
                }
                
                if hackathon.lower() == "breakout":
                    technical_demo_link = row['Technical_Demo_Link_URL'] if 'Technical_Demo_Link_URL' in row and pd.notna(row['Technical_Demo_Link_URL']) else row.get('Technical Demo Link')
                    if technical_demo_link == "Technical Demo Link":
                        technical_demo_link = None
                    project_data["technical_demo_link"] = technical_demo_link
                
                new_project = model_class(**project_data)
                
                db.add(new_project)
                new_projects_added += 1
                print(f"Added new project to database: {project_name} (Hackathon: {hackathon})")
                
                existing_projects[project_name_lower] = project_name
        
        if new_projects_added > 0:
            db.commit()
            print(f"Database sync complete. Added {new_projects_added} new projects to {hackathon} hackathon.")
        else:
            print(f"No new projects to add. All projects already exist in the {hackathon} hackathon database.")
    
    except Exception as e:
        db.rollback()
        print(f"Error syncing with database: {str(e)}")
        raise e
    
    finally:
        db.close()
        
    return new_projects_added

def search_projects(query, text_column='description', top_n=20, use_db=True, hackathon="all"):
    """
    Search for projects using either the database or Excel file.
    
    Args:
        query: Search query text
        text_column: Column to search in
        top_n: Number of results to return
        use_db: Whether to search in the database (True) or Excel file (False)
        hackathon: Which hackathon to search in ("renaissance", "radar", "breakout", or "all")
        
    Returns:
        List of matching projects
    """
    create_tables()
    
    if use_db:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode([query])
        
        db = get_db()
        try:
            all_projects = []
            
            if hackathon.lower() == "renaissance" or hackathon.lower() == "all":
                renaissance_projects = db.query(RenaissanceHackathonProject).all()
                all_projects.extend([(project, "renaissance") for project in renaissance_projects])
            
            if hackathon.lower() == "radar" or hackathon.lower() == "all":
                radar_projects = db.query(RadarHackathonProject).all()
                all_projects.extend([(project, "radar") for project in radar_projects])
            
            if hackathon.lower() == "breakout" or hackathon.lower() == "all":
                breakout_projects = db.query(BreakoutHackathonProject).all()
                all_projects.extend([(project, "breakout") for project in breakout_projects])
            
            search_texts = []
            for project, _ in all_projects:
                if hasattr(project, text_column):
                    text = getattr(project, text_column) or ""
                else:
                    print(f"Warning: Column '{text_column}' not found in project. Using 'description' instead.")
                    text = project.description or ""
                search_texts.append(text)
            
            if search_texts:
                record_embeddings = model.encode(search_texts)
                
                similarity_scores = cosine_similarity(query_embedding, record_embeddings)[0]
                
                project_scores = [(all_projects[i][0], all_projects[i][1], similarity_scores[i]) 
                                 for i in range(len(all_projects))]
                
                sorted_projects = sorted(project_scores, key=lambda x: x[2], reverse=True)[:top_n]
                
                return [{"project": p[0], "hackathon": p[1], "similarity_score": p[2]} for p in sorted_projects]
            else:
                print("No projects found in the database.")
                return []
        
        finally:
            db.close()
    else:
        base_path = "./context/hackathons/colloseum/"
        os.makedirs(base_path, exist_ok=True)
        
        if hackathon.lower() == "renaissance":
            excel_file = f"{base_path}renaissance_hackathon_projects.xlsx"
        elif hackathon.lower() == "radar":
            excel_file = f"{base_path}radar_hackathon_projects.xlsx"
        elif hackathon.lower() == "breakout":
            excel_file = f"{base_path}breakout_hackathon_projects.xlsx"
        else:
            excel_file = f"{base_path}renaissance_hackathon_projects.xlsx"
        
        if not os.path.exists(excel_file):
            print(f"Warning: Excel file not found: {excel_file}")
            return []
            
        results = search_excel_records(excel_file, query, text_column, top_n=top_n, hackathon=hackathon)
        return results.to_dict('records')
    
def import_all_hackathon_data():
    """
    Import data from all hackathon Excel files into the database.
    """
    create_tables()
    
    try:
        base_path = "./context/hackathons/colloseum/"
        os.makedirs(base_path, exist_ok=True)
        
        renaissance_file = f"{base_path}renaissance_hackathon_projects.xlsx"
        if os.path.exists(renaissance_file):
            print(f"Importing Renaissance hackathon data from {renaissance_file}")
            df = extract_hyperlinks_from_excel(renaissance_file)
            sync_excel_with_database(df, "renaissance")
        else:
            print(f"Warning: {renaissance_file} not found")
        
        radar_file = f"{base_path}radar_hackathon_projects.xlsx"
        if os.path.exists(radar_file):
            print(f"Importing Radar hackathon data from {radar_file}")
            df = extract_hyperlinks_from_excel(radar_file)
            sync_excel_with_database(df, "radar")
        else:
            print(f"Warning: {radar_file} not found")
        
        breakout_file = f"{base_path}breakout_hackathon_projects.xlsx"
        if os.path.exists(breakout_file):
            print(f"Importing Breakout hackathon data from {breakout_file}")
            df = extract_hyperlinks_from_excel(breakout_file)
            if len(df) > 0 and "Solana Breakout Hackathon project directory" in str(df.iloc[0].values[0]):
                print("Removing header row from Breakout hackathon data")
                df = df.iloc[1:].reset_index(drop=True)
            sync_excel_with_database(df, "breakout")
        else:
            print(f"Warning: {breakout_file} not found")
            
        print("All hackathon data imported successfully")
        
    except Exception as e:
        print(f"Error importing hackathon data: {str(e)}")
        import traceback
        traceback.print_exc()
import json
import sys
import os
from datetime import datetime
import glob

# Add the parent directory to the Python path to enable importing connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connection import get_connection

# The directory containing the FAQ JSON files
FAQ_JSON_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'faq')

def load_faq_data(file_path):
    """Loads FAQ data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: JSON file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None

def get_or_create_manufacturer_id(cursor, manufacturer_name):
    """Gets the ID of a manufacturer, creating it if it doesn't exist."""
    cursor.execute("SELECT id FROM EV_Manufacturer WHERE name = %s", (manufacturer_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print(f"Manufacturer '{manufacturer_name}' not found. Inserting it.")
        cursor.execute("INSERT INTO EV_Manufacturer (name) VALUES (%s)", (manufacturer_name,))
        return cursor.lastrowid

def insert_faq_to_db(faq_data, manufacturer_name, conn, cursor):
    """Inserts FAQ data into the EV_Manufacturer_FAQ table."""
    if not faq_data:
        print("No FAQ data to insert.")
        return 0

    try:
        manufacturer_id = get_or_create_manufacturer_id(cursor, manufacturer_name)
        if not manufacturer_id:
            print(f"Could not get or create manufacturer ID for '{manufacturer_name}'. Skipping.")
            return 0

        sql = """
        INSERT IGNORE INTO EV_Manufacturer_FAQ (
            manufacturer_id, source_url, section, question, answer_text, answer_html, captured_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        captured_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        inserted_count = 0
        for faq in faq_data:
            source_url = faq.get('source_url')
            section = faq.get('section')
            question = faq.get('question')
            answer_text = faq.get('answer_text')
            answer_html = faq.get('answer_html')

            if not all([source_url, question, answer_text]):
                print(f"Skipping invalid FAQ entry: {faq.get('question', 'N/A')}")
                continue

            values = (manufacturer_id, source_url, section, question, answer_text, answer_html, captured_at)
            cursor.execute(sql, values)
            inserted_count += cursor.rowcount # Counts how many rows were actually inserted

        return inserted_count

    except Exception as e:
        print(f"Database error while processing for manufacturer '{manufacturer_name}': {e}")
        raise # Re-raise the exception to trigger rollback

def process_all_faq_files():
    """Loads all FAQ JSON files from the specified directory and inserts them into the database."""
    conn = None
    total_inserted = 0
    try:
        conn = get_connection()
        cursor = conn.cursor()

        json_files = glob.glob(os.path.join(FAQ_JSON_DIRECTORY, '*.json'))
        if not json_files:
            print(f"No JSON files found in {FAQ_JSON_DIRECTORY}")
            return

        for file_path in json_files:
            print(f"Processing file: {file_path}")
            faq_data = load_faq_data(file_path)
            if not faq_data:
                print(f"Failed to load data from {file_path}. Skipping.")
                continue

            filename = os.path.basename(file_path)
            manufacturer_name = "General" # Default
            if 'kia' in filename.lower():
                manufacturer_name = 'Kia'
            elif faq_data and 'pge.com' in faq_data[0].get('source_url', ''): # Check content for pge
                 manufacturer_name = 'PGE'
            
            print(f"Determined manufacturer: {manufacturer_name}")

            inserted_count = insert_faq_to_db(faq_data, manufacturer_name, conn, cursor)
            total_inserted += inserted_count
            print(f"Inserted {inserted_count} new entries for this file.")
        
        conn.commit()
        print(f"\nProcessing complete. Total new entries inserted: {total_inserted}")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    process_all_faq_files()

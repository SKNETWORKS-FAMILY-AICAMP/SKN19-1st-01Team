import csv
import sys
import os

# Add the parent directory to the Python path to enable importing connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from connection import get_connection

# Base path for datasets
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets')

def get_or_create_manufacturer_id(cursor, manufacturer_name):
    cursor.execute("SELECT id FROM EV_Manufacturer WHERE name = %s", (manufacturer_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print(f"Manufacturer '{manufacturer_name}' not found. Inserting it.")
        cursor.execute("INSERT INTO EV_Manufacturer (name) VALUES (%s)", (manufacturer_name,))
        return cursor.lastrowid

def load_total_fire_incidents(cursor):
    file_path = os.path.join(DATASET_PATH, '소방청_차량화재통계.csv')
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            # Aggregate counts by year
            fire_counts_by_year = {}
            for row in reader:
                year = int(row[0])
                fire_counts_by_year[year] = fire_counts_by_year.get(year, 0) + 1

            sql = "INSERT IGNORE INTO total_fire_incidents (year, count) VALUES (%s, %s)"
            total_inserted = 0
            for year, count in fire_counts_by_year.items():
                cursor.execute(sql, (year, count))
                total_inserted += cursor.rowcount
            print(f"Inserted {total_inserted} rows into total_fire_incidents.")
            
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

def load_vehicle_registrations(cursor):
    file_path = os.path.join(DATASET_PATH, 'Vehicles_2021-2023.csv')
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) # 'ID', '연료', '2021', '2022', '2023', 'source_url'
            years = [int(y) for y in header[2:5]] # Years are at index 2, 3, 4

            sql = "INSERT IGNORE INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (%s, %s, %s, %s)"
            total_inserted = 0
            for row in reader:
                fuel_type = row[1]
                # No need to skip '계' as the new file only contains EV, ICE, 총계
                counts = [int(c) for c in row[2:5]] # Counts are at index 2, 3, 4
                source_url = row[5] # Source URL is at index 5
                for i, year in enumerate(years):
                    cursor.execute(sql, (year, fuel_type, counts[i], source_url))
                    total_inserted += cursor.rowcount
            print(f"Inserted {total_inserted} rows into vehicle_registrations.")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

def load_ev_fire_cases(cursor):
    file_path = os.path.join(DATASET_PATH, '전기차 화재 발생 현황.csv')
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header

            sql = """
            INSERT IGNORE INTO ev_fire_cases (year, manufacturer_id, model, ignition_point, situation, battery_supplier)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            total_inserted = 0
            for row in reader:
                year = int(row[0])
                manufacturer_name = row[1]
                model = row[2]
                ignition_point = row[3]
                situation = row[4]
                battery_supplier = row[5]

                manufacturer_id = get_or_create_manufacturer_id(cursor, manufacturer_name)

                values = (year, manufacturer_id, model, ignition_point, situation, battery_supplier)
                cursor.execute(sql, values)
                total_inserted += cursor.rowcount
            print(f"Inserted {total_inserted} rows into ev_fire_cases.")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

def main():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            load_total_fire_incidents(cursor)
            load_vehicle_registrations(cursor)
            load_ev_fire_cases(cursor)
            conn.commit()
            cursor.close()
    except Exception as e:
        print(f"A database error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()

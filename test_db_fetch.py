import sys
import os
import pandas as pd

# Add the parent directory to the Python path to enable importing connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'db')))

from connection import get_connection

def test_fetch():
    conn = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            print("\n--- vehicle_registrations data ---")
            cursor.execute("SELECT year, fuel_type, count, source_url FROM vehicle_registrations")
            reg_data = cursor.fetchall()
            if reg_data:
                df_reg = pd.DataFrame(reg_data)
                print(df_reg)
            else:
                print("No data found in vehicle_registrations.")

            print("\n--- total_fire_incidents data ---")
            cursor.execute("SELECT year, count FROM total_fire_incidents")
            fire_data = cursor.fetchall()
            if fire_data:
                df_fire = pd.DataFrame(fire_data)
                print(df_fire)
            else:
                print("No data found in total_fire_incidents.")

            cursor.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    test_fetch()

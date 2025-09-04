import mysql.connector
import json
from datetime import datetime
import re

# Database connection details (should ideally come from .env)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '121512',
    'database': 'ev_fire'
}

def load_faq_data():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("MySQL에 성공적으로 연결되었습니다! (FAQ 로더)")
            cursor = connection.cursor()

            # Get manufacturer IDs
            manufacturer_ids = {}
            cursor.execute("SELECT id, name FROM EV_Manufacturer")
            for (id, name) in cursor:
                manufacturer_ids[name] = id

            # Load Chevrolet FAQ
            chevrolet_faq_path = "C:\\Users\\minek\\github\\SKN19-1st-04Team\\datasets\\faq\\chevrolet_ev_faq.json"
            with open(chevrolet_faq_path, 'r', encoding='utf-8') as f:
                chevrolet_faqs = json.load(f)
            
            chevrolet_manufacturer_id = manufacturer_ids.get('쉐보레')
            if chevrolet_manufacturer_id:
                for faq in chevrolet_faqs:
                    question = faq['question']
                    answer = faq['answer']
                    captured_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    insert_query_simple = """
                    INSERT INTO EV_Manufacturer_FAQ (manufacturer_id, question, answer, captured_at)
                    VALUES (%s, %s, %s, %s);
                    """
                    cursor.execute(insert_query_simple, (chevrolet_manufacturer_id, question, answer, captured_at))
                connection.commit()
                print(f"쉐보레 FAQ 데이터 {len(chevrolet_faqs)}건 삽입 완료.")
            else:
                print("쉐보레 제조사를 찾을 수 없습니다. FAQ 데이터를 로드할 수 없습니다.")

            # Load Kia FAQ
            kia_faq_path = "C:\\Users\\minek\\github\\SKN19-1st-04Team\\datasets\\faq\\kia_ev_faq.json"
            with open(kia_faq_path, 'r', encoding='utf-8') as f:
                kia_faqs = json.load(f)
            
            kia_manufacturer_id = manufacturer_ids.get('기아자동차')
            if kia_manufacturer_id:
                for faq in kia_faqs:
                    question = faq['question']
                    answer = faq['answer']
                    clean_answer = re.sub('<[^<]+?>', '', answer).strip()
                    
                    captured_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    cursor.execute(insert_query_simple, (kia_manufacturer_id, question, clean_answer, captured_at))
                connection.commit()
                print(f"기아자동차 FAQ 데이터 {len(kia_faqs)}건 삽입 완료.")
            else:
                print("기아자동차 제조사를 찾을 수 없습니다. FAQ 데이터를 로드할 수 없습니다.")

    except mysql.connector.Error as err:
        print(f"데이터베이스 오류: {err}")
    except FileNotFoundError as err:
        print(f"파일을 찾을 수 없습니다: {err}")
    except Exception as err:
        print(f"예상치 못한 오류: {err}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL 연결이 닫혔습니다! (FAQ 로더)")

if __name__ == "__main__":
    load_faq_data()

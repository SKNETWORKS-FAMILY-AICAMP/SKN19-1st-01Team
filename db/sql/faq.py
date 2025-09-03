import json
import os
from datetime import datetime
import glob
import sys # Add sys import

# Add the parent directory to the Python path to enable importing connection.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# connection.py에서 get_connection 함수 임포트
from connection import get_connection

# --- 설정 ---
# FAQ JSON 파일들이 있는 디렉토리 경로
FAQ_JSON_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'faq')

# --- 메인 데이터 로드 및 삽입 로직 ---
def load_and_insert_faqs():
    conn = None
    cursor = None
    try:
        conn = get_connection() # connection.py의 get_connection 사용
        if not conn:
            return

        cursor = conn.cursor()

        # 1. 기존 데이터 전부 삭제 (TRUNCATE)
        print("기존 FAQ 데이터 삭제 중...")
        cursor.execute("TRUNCATE TABLE EV_Manufacturer_FAQ")
        print("기존 데이터 삭제 완료.")

        # 2. EV_Manufacturer 테이블에서 제조사 ID 가져오기 또는 새로 생성
        # 이 부분은 기존 faq.py의 get_or_create_manufacturer_id 로직을 단순화합니다.
        # 실제 프로젝트에서는 EV_Manufacturer 테이블이 미리 채워져 있거나,
        # 스크래퍼에서 제조사 정보를 명확히 제공해야 합니다.
        # 여기서는 파일명에서 제조사를 유추합니다.
        
        # 제조사 ID를 저장할 딕셔너리
        manufacturer_ids = {}
        
        # 모든 JSON 파일 찾기
        json_files = glob.glob(os.path.join(FAQ_JSON_DIRECTORY, '*.json'))
        if not json_files:
            print(f"경로에 JSON 파일이 없습니다: {FAQ_JSON_DIRECTORY}")
            return

        total_inserted_count = 0
        captured_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for file_path in json_files:
            print(f"\n파일 처리 중: {file_path}")
            
            # 파일명에서 제조사 이름 유추
            filename = os.path.basename(file_path).lower()
            manufacturer_name = "Unknown"
            if "chevrolet" in filename:
                manufacturer_name = "Chevrolet"
            elif "kia" in filename:
                manufacturer_name = "Kia"
            elif "renault" in filename: # 르노도 추가
                manufacturer_name = "Renault"
            # 필요에 따라 다른 제조사 추가

            # 제조사 ID 가져오기 또는 생성
            if manufacturer_name not in manufacturer_ids:
                cursor.execute("SELECT id FROM EV_Manufacturer WHERE name = %s", (manufacturer_name,))
                result = cursor.fetchone()
                if result:
                    manufacturer_ids[manufacturer_name] = result[0]
                else:
                    print(f"제조사 '{manufacturer_name}'를 EV_Manufacturer 테이블에 추가합니다.")
                    cursor.execute("INSERT INTO EV_Manufacturer (name) VALUES (%s)", (manufacturer_name,))
                    manufacturer_ids[manufacturer_name] = cursor.lastrowid
            
            current_manufacturer_id = manufacturer_ids[manufacturer_name]

            # JSON 파일 로드
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    faqs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"JSON 파일 로드 오류 ({file_path}): {e}")
                continue

            if not faqs:
                print(f"파일에 FAQ 데이터가 없습니다: {file_path}")
                continue

            # 3. FAQ 데이터 삽입
            insert_sql = """
            INSERT INTO EV_Manufacturer_FAQ (manufacturer_id, question, answer, captured_at)
            VALUES (%s, %s, %s, %s)
            """
            
            inserted_count_for_file = 0
            for faq in faqs:
                question = faq.get('question')
                answer = faq.get('answer')

                if question and answer: # 질문과 답변이 모두 있는 경우만 삽입
                    try:
                        cursor.execute(insert_sql, (current_manufacturer_id, question, answer, captured_at))
                        inserted_count_for_file += 1
                    except mysql.connector.Error as err:
                        print(f"데이터 삽입 오류 (질문: {question[:30]}...): {err}")
                else:
                    print(f"유효하지 않은 FAQ 항목 건너뛰기 (질문 또는 답변 없음): {faq}")

            conn.commit() # 파일별로 커밋
            total_inserted_count += inserted_count_for_file
            print(f"'{manufacturer_name}' 제조사 FAQ {inserted_count_for_file}개 삽입 완료.")

        print(f"\n모든 파일 처리 완료. 총 {total_inserted_count}개의 FAQ 데이터 삽입.")

    except Exception as e:
        print(f"오류 발생: {e}")
        if conn:
            conn.rollback() # 오류 발생 시 롤백
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --- 스크립트 실행 ---
if __name__ == "__main__":
    load_and_insert_faqs()
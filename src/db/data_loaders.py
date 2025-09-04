import mysql.connector

# Database connection details (should ideally come from .env)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '121512',
    'database': 'ev_fire'
}

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("MySQL에 성공적으로 연결되었습니다!")
            return connection
    except mysql.connector.Error as err:
        print(f"MySQL 연결 오류: {err}")
        return None

def load_ev_manufacturers():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        manufacturers = [
            '현대자동차', '기아자동차', '르노코리아', '쉐보레', '닛산', '벤츠', 'BMW', 'BYD',
            '포르쉐', '폭스바겐', '폴스타', '렉서스', '링컨', '벤틀리', '볼보', '아우디',
            '테슬라', '토요타', '재규어', '푸조', 'Jeep', 'CEVO 모빌리티', 'Evion',
            'MaiV(마이브)', 'MASADA(마사다)', 'SE-A(세아)', 'SMART EV', '대창모터스',
            '디피코', '마이크로리노', '명원아이앤씨(오토바이)', '비바모빌리티', '에스에스 라이트',
            '제이스 모빌리티', '파워프라자', '한신자동차', '기타', 'KGM'
        ]
        sql = "INSERT IGNORE INTO EV_Manufacturer (name) VALUES (%s)"
        try:
            for manufacturer in manufacturers:
                cursor.execute(sql, (manufacturer,))
            conn.commit()
            print(f"EV_Manufacturer 데이터 {len(manufacturers)}건 삽입 완료.")
        except mysql.connector.Error as err:
            print(f"EV_Manufacturer 데이터 삽입 오류: {err}")
        finally:
            cursor.close()
            conn.close()

def load_total_fire_incidents():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        data = [
            (2021, 3517, 1734, 685, 178, 634, 271, 15),
            (2022, 3680, 1739, 727, 181, 700, 307, 26),
            (2023, 3736, 1793, 749, 172, 690, 309, 23)
        ]
        sql = """
        INSERT INTO total_fire_incidents (year, total_fires, general_road, highway, other_road, parking_lot, vacant_lot, tunnel)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            for row in data:
                cursor.execute(sql, row)
            conn.commit()
            print(f"total_fire_incidents 데이터 {len(data)}건 삽입 완료.")
        except mysql.connector.Error as err:
            print(f"total_fire_incidents 데이터 삽입 오류: {err}")
        finally:
            cursor.close()
            conn.close()

def load_ev_fire_cases():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        data = [
            (2021, 24, 1, 0, 1, 878084),
            (2022, 43, 3, 0, 3, 913362),
            (2023, 72, 9, 0, 9, 1463986)
        ]
        sql = """
        INSERT INTO ev_fire_cases (year, total_fires, total_casualties, deaths, injuries, property_damage_krw)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            for row in data:
                cursor.execute(sql, row)
            conn.commit()
            print(f"ev_fire_cases 데이터 {len(data)}건 삽입 완료.")
        except mysql.connector.Error as err:
            print(f"ev_fire_cases 데이터 삽입 오류: {err}")
        finally:
            cursor.close()
            conn.close()

def load_vehicle_registrations():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        data = [
            (2021, 'EV', 231443, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1'),
            (2022, 'EV', 389855, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1'),
            (2023, 'EV', 543900, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1'),
            (2021, 'ICE', 24678557, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1'),
            (2022, 'ICE', 25113145, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1'),
            (2023, 'ICE', 25405100, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1'),
            (2021, '총계', 24910000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1'),
            (2022, '총계', 25503000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1'),
            (2023, '총계', 25949000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1')
        ]
        sql = """
        INSERT INTO vehicle_registrations (year, fuel_type, count, source_url)
        VALUES (%s, %s, %s, %s)
        """
        try:
            for row in data:
                cursor.execute(sql, row)
            conn.commit()
            print(f"vehicle_registrations 데이터 {len(data)}건 삽입 완료.")
        except mysql.connector.Error as err:
            print(f"vehicle_registrations 데이터 삽입 오류: {err}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("모든 데이터 로더를 실행합니다.")
    load_ev_manufacturers()
    load_total_fire_incidents()
    load_ev_fire_cases()
    load_vehicle_registrations()
    print("모든 데이터 로더 실행 완료.")
import mysql.connector

def get_connection():
    """MySQL 데이터베이스 연결 객체를 반환합니다."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            database="ev_fire",
            user="ohgiraffers",
            password="ohgiraffers"
        )
        if conn.is_connected():
            print("MySQL에 성공적으로 연결되었습니다! (ohgiraffers 계정)")
            return conn
    except mysql.connector.Error as e:
        print(f"MySQL 연결 오류: {e}")
        return None

if __name__ == "__main__":
    # 이 파일이 직접 실행될 때만 연결 테스트
    conn = get_connection()
    if conn:
        print("Connection test successful.")
        conn.close()
        print("Connection closed.")
import mysql.connector

# mysql 서버 접속 가능한 연결 객체 생성 (ohgiraffers 계정)
connection = mysql.connector.connect(
    host="localhost",
    database="ev_fire",
    user="ohgiraffers",
    password="ohgiraffers"
)

# Test Connection 메서드
if connection.is_connected():
    print("MySQL에 성공적으로 연결되었습니다! (ohgiraffers 계정)")

# Connection Close 메서드
connection.close()

if connection.is_closed():
    print("MySQL 연결이 닫혔습니다! (ohgiraffers 계정)")
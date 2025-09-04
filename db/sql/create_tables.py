import mysql.connector

# mysql 서버 접속 가능한 연결 객체 생성 (root 계정)
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="121512"
)

# Test Connection 메서드
if connection.is_connected():
    print("MySQL에 성공적으로 연결되었습니다! (root 계정)")

    cursor = connection.cursor()

    # SQL DDL statements
    SQL_DDL = """
    CREATE DATABASE IF NOT EXISTS ev_fire;

    USE ev_fire;

    DROP TABLE IF EXISTS EV_Manufacturer_FAQ;

    CREATE TABLE IF NOT EXISTS EV_Manufacturer (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    );

    DROP TABLE IF EXISTS vehicle_registrations;

    CREATE TABLE IF NOT EXISTS vehicle_registrations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL,
        fuel_type VARCHAR(50) NOT NULL,
        count INT NOT NULL,
        source_url VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS total_fire_incidents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL,
        count INT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ev_fire_cases (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL,
        manufacturer_id INT NOT NULL,
        model VARCHAR(100) NOT NULL,
        ignition_point VARCHAR(255) NOT NULL,
        situation VARCHAR(100),
        battery_supplier VARCHAR(100),
        FOREIGN KEY (manufacturer_id) REFERENCES EV_Manufacturer(id)
    );

    CREATE TABLE IF NOT EXISTS EV_Manufacturer_FAQ (
        id INT AUTO_INCREMENT PRIMARY KEY,
        manufacturer_id INT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        captured_at DATETIME NOT NULL,
        FOREIGN KEY (manufacturer_id) REFERENCES EV_Manufacturer(id)
    );

    -- Create user and grant privileges
    CREATE USER IF NOT EXISTS 'ohgiraffers'@'localhost' IDENTIFIED BY 'ohgiraffers';
    GRANT ALL PRIVILEGES ON ev_fire.* TO 'ohgiraffers'@'localhost';
    FLUSH PRIVILEGES;

    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('Kia');
    """

    # Execute each statement
    for statement in SQL_DDL.split(';'):
        if statement.strip():
            cursor.execute(statement)
    connection.commit()
    print("데이터베이스 및 테이블 생성, 권한 부여 완료.")

    # Connection Close 메서드
    cursor.close()
    connection.close()

    if connection.is_closed():
        print("MySQL 연결이 닫혔습니다!")
else:
    print("MySQL 연결에 실패했습니다!")
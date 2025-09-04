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

    DROP TABLE IF EXISTS total_fire_incidents;
    CREATE TABLE IF NOT EXISTS total_fire_incidents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL,
        total_fires INT NOT NULL,
        general_road INT,
        highway INT,
        other_road INT,
        parking_lot INT,
        vacant_lot INT,
        tunnel INT
    );

    DROP TABLE IF EXISTS ev_fire_cases;
    CREATE TABLE IF NOT EXISTS ev_fire_cases (
        id INT AUTO_INCREMENT PRIMARY KEY,
        year INT NOT NULL,
        total_fires INT NOT NULL,
        total_casualties INT,
        deaths INT,
        injuries INT,
        property_damage_krw BIGINT
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

    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('현대자동차');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('기아자동차');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('르노코리아');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('쉐보레');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('닛산');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('벤츠');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('BMW');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('BYD');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('포르쉐');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('폭스바겐');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('폴스타');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('렉서스');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('링컨');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('벤틀리');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('볼보');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('아우디');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('테슬라');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('토요타');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('재규어');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('푸조');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('Jeep');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('CEVO 모빌리티');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('Evion');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('MaiV(마이브)');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('MASADA(마사다)');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('SE-A(세아)');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('SMART EV');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('대창모터스');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('디피코');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('마이크로리노');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('명원아이앤씨(오토바이)');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('비바모빌리티');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('에스에스 라이트');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('제이스 모빌리티');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('파워프라자');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('한신자동차');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('기타');
    INSERT IGNORE INTO EV_Manufacturer (name) VALUES ('KGM');
    
    INSERT INTO total_fire_incidents (year, total_fires, general_road, highway, other_road, parking_lot, vacant_lot, tunnel) VALUES (2021, 3517, 1734, 685, 178, 634, 271, 15);
    INSERT INTO total_fire_incidents (year, total_fires, general_road, highway, other_road, parking_lot, vacant_lot, tunnel) VALUES (2022, 3680, 1739, 727, 181, 700, 307, 26);
    INSERT INTO total_fire_incidents (year, total_fires, general_road, highway, other_road, parking_lot, vacant_lot, tunnel) VALUES (2023, 3736, 1793, 749, 172, 690, 309, 23);

    INSERT INTO ev_fire_cases (year, total_fires, total_casualties, deaths, injuries, property_damage_krw) VALUES (2021, 24, 1, 0, 1, 878084);
    INSERT INTO ev_fire_cases (year, total_fires, total_casualties, deaths, injuries, property_damage_krw) VALUES (2022, 43, 3, 0, 3, 913362);
    INSERT INTO ev_fire_cases (year, total_fires, total_casualties, deaths, injuries, property_damage_krw) VALUES (2023, 72, 9, 0, 9, 1463986);

    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2021, 'EV', 231443, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2022, 'EV', 389855, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2023, 'EV', 543900, 'https://argos.nanet.go.kr/lawstat/arc/attach/112495?view=1');

    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2021, 'ICE', 24678557, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2022, 'ICE', 25113145, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2023, 'ICE', 25405100, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');

    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2021, '총계', 24910000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2022, '총계', 25503000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');
    INSERT INTO vehicle_registrations (year, fuel_type, count, source_url) VALUES (2023, '총계', 25949000, 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95086498&lcmspage=1');
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
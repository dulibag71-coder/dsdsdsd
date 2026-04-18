-- Database Creation
-- psql이나 pgAdmin에서 아래 스크립트를 실행하세요.
-- 1) CREATE DATABASE는 단독으로 실행해야 합니다.
-- CREATE DATABASE golf_ai;
-- 2) 이 후 데이터베이스를 golf_ai로 연결 변경 후 아래 테이블을 생성하세요.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE swings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    video_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE poses (
    id SERIAL PRIMARY KEY,
    swing_id INTEGER REFERENCES swings(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,
    keypoints_json TEXT NOT NULL -- JSON 형태의 3D 관절 좌표 저장 (예: [[x, y, z], ...])
);

CREATE TABLE analysis (
    id SERIAL PRIMARY KEY,
    swing_id INTEGER REFERENCES swings(id) ON DELETE CASCADE,
    result_json TEXT NOT NULL -- 분석 지표 결과 (예: 스웨이, 코일링 등)
);

CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    swing_id INTEGER REFERENCES swings(id) ON DELETE CASCADE,
    lesson_text TEXT NOT NULL -- GPT가 생성한 레슨 코멘트
);

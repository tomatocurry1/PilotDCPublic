CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_salt BLOB,
    email TEXT,
    join_date DATE,
    longitude REAL,
    latitude REAL,
    karma INTEGER
);

CREATE TABLE favors (
    favor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    content TEXT,
    location_description TEXT,
    requirements TEXT,
    state INTEGER, -- 0 = America (free), 1 = taken, 2 = completed
    creation_date DATE,
    deadline DATE,
    cost INTEGER,
    payment INTEGER,
    longitude REAL,
    latitude REAL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE favor_permissions (
    favor_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY (favor_id) REFERENCES favors(favor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_salt BLOB,
    email TEXT,
    join_date INTEGER,
    longitude REAL,
    latitude REAL,
    karma INTEGER
);

CREATE TABLE favors (
    favor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    title TEXT,
    content TEXT,
    location_description TEXT,
    requirements TEXT,
    state INTEGER, -- 0 = America (free), 1 = taken, 2 = completed, 3 = expired w/o completion
    worker_id INTEGER,
    creation_date INTEGER,
    deadline INTEGER,
    cost INTEGER,
    payment INTEGER,
    longitude REAL,
    latitude REAL,
    FOREIGN KEY (creator_id) REFERENCES users(user_id),
    FOREIGN KEY (worker_id) REFERENCES users(user_id)
);

CREATE TABLE favor_permissions (
    favor_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY (favor_id) REFERENCES favors(favor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
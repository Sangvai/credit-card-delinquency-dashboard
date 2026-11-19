CREATE TABLE observation (
    quarter_id INTEGER NOT NULL,
    series TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (quarter_id, series)
);
CREATE TABLE source (
    url TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL
);

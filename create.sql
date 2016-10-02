CREATE TABLE channel(
    channum INT KEY,
    name TEXT NOT NULL,
    type INT NOT NULL DEFAULT 1,
    watts DOUBLE NOT NULL,
    stamp DATETIME);
CREATE TABLE used(
    channum INT NOT NULL, KEY(channum),
    watts INT NOT NULL,
    stamp DATETIME NOT NULL, KEY(stamp));
CREATE TABLE scratchpad LIKE used;
CREATE TABLE alert(
    id INT KEY AUTO_INCREMENT,
    channum INT,
    greater BOOL,
    watts INT,
    minutes INT,
    start TIME,
    end TIME,
    message TEXT,
    alerted BOOL DEFAULT FALSE);
CREATE TABLE settings(
    consolidate_stamp DATETIME,
    history_days int);
INSERT INTO settings VALUES(NULL, 30);


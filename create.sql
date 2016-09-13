CREATE TABLE channel(
    channum INT KEY,
    name TEXT NOT NULL,
    inuse BOOL NOT NULL DEFAULT 1,
    mult DOUBLE NOT NULL DEFAULT 1,
    last DOUBLE NOT NULL,
    stamp DATETIME NOT NULL);
CREATE TABLE used(
    channum INT NOT NULL, KEY(channum),
    watts INT NOT NULL,
    stamp DATETIME NOT NULL, KEY(stamp));

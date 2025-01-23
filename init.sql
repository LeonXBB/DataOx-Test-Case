CREATE TABLE IF NOT EXISTS Users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phoneNumber VARCHAR(50),
    rating VARCHAR(50),
    registrationDate VARCHAR(255) NOT NULL,
    lastOnline VARCHAR(255),
    location VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Items (
    id SERIAL PRIMARY KEY,
    olxId VARCHAR(255) UNIQUE NOT NULL,
    pageUrl TEXT,
    title VARCHAR(255),
    price VARCHAR(255),
    options TEXT,
    description TEXT,
    views INT,
    publicationDate VARCHAR(255),
    userId INT,
    FOREIGN KEY (userId) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS ItemPictures (
    id SERIAL PRIMARY KEY,
    itemId INT,
    pictureUrl TEXT,
    FOREIGN KEY (itemId) REFERENCES Items(id)
);
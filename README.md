## Finance Stock Simulator  
This project allows users to practice trading stocks before committing to the real thing.  

### FullStack App Specifications:  
- The dynamic front end was built using Javascript and Jinja.  
- HTTP methods were handled on the backend by leveraging the Flask Python Module.  
- Data was stored in a relational database, MYSQL.  
- External API was used to get real-time stock data.  

### Database Specifications:
- User's Passwords were hashed before stored to ensure greater security.  
- Transactions table can be queried to get a user's transaction history.  
- Stock Distribution table contains information on who owns what stocks, and how many.

database_info.txt contains information on the SQL database structure but for your convenience, here is the schema:  

```
CREATE TABLE users (
    id INTEGER NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    cash FLOAT NOT NULL, DEFAULT 10000
    PRIMARY KEY (id),
);

CREATE TABLE transactions (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    shares INTEGER NOT NULL,
    price_per_share FLOAT NOT NULL,
    time TEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE stock_distribution (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    shares INTEGER NOT NULL,
    avg_share_price FLOAT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```


-- Create the shops table
CREATE TABLE shops (
    id UUID PRIMARY KEY,
    certificated BOOLEAN DEFAULT FALSE NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL,
    paying BOOLEAN DEFAULT FALSE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE NOT NULL,
    version INT NOT NULL
);

-- Create an enum type for the country_code
CREATE TYPE country_code_type AS ENUM ('CZ', 'SK', 'HU', 'BG', 'RO', 'SI', 'BA', 'RS', 'HR');

-- Create enum types for type and currency_code
CREATE TYPE currency_code_type AS ENUM ('BAM', 'EUR', 'BGN', 'HRK', 'CZK', 'HUF', 'RON', 'RSD');

-- Create the offers table
CREATE TABLE offers (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    country_code country_code_type NOT NULL,
    shop_id UUID NOT NULL,
    amount DECIMAL(12, 2) NOT NULL, --REGULAR
    currency_code currency_code_type NOT NULL,
    version INT NOT NULL
);

-- Create the buyables table
CREATE TABLE buyables (
    offer_id UUID PRIMARY KEY,
    buyable BOOLEAN DEFAULT FALSE NOT NULL,
    version INT NOT NULL
);

-- Create the availabilities table
CREATE TABLE availabilities (
    offer_id UUID PRIMARY KEY,
    in_stock BOOLEAN DEFAULT FALSE NOT NULL,
    version INT NOT NULL
);


-- Create an enum type for price_type
CREATE TYPE product_price_type AS ENUM ('ALL_OFFERS', 'MARKETPLACE', 'IN_STOCK', 'IN_STOCK_CERTIFIED');

-- Create the ProductPrices table
CREATE TABLE product_prices (
    product_id UUID NOT NULL,
    country_code country_code_type NOT NULL, -- Product could be in multiple countries, distinguish for each country
    currency_code currency_code_type NOT NULL,
    min_price DECIMAL(12, 2) NOT NULL,
    max_price DECIMAL(12, 2) NOT NULL,
    avg_price DECIMAL(12, 2) NOT NULL,
    price_type product_price_type NOT NULL,
    updated_at TIMESTAMP NOT NULL, -- To know which Product should be updated in Product price history table
    version INT NOT NULL,
    PRIMARY KEY (product_id, country_code)
);

-- Create the ProductDiscount table
CREATE TABLE product_discounts (
    product_id UUID NOT NULL,
    country_code country_code_type NOT NULL, -- Product could be in multiple countries, distinguish for each country
    discount DECIMAL(5, 2) NOT NULL, -- percentage
    price_type product_price_type NOT NULL, -- Do we need Discount per Price type?
    updated_at TIMESTAMP NOT NULL, -- To know which Product should be updated in Product price history table
    version INT NOT NULL,
    PRIMARY KEY (product_id, country_code)
);

-- Create the ProductPriceHistory master table
CREATE TABLE product_prices_history (
    product_id UUID NOT NULL,
    country_code country_code_type NOT NULL, -- Product could be in multiple countries, distinguish for each country
    currency_code currency_code_type NOT NULL,
    min_price DECIMAL(12, 2) NOT NULL,
    max_price DECIMAL(12, 2) NOT NULL,
    avg_price DECIMAL(12, 2) NOT NULL,
    price_type product_price_type NOT NULL,
    date DATE NOT NULL,
    PRIMARY KEY (product_id, country_code, date)
) PARTITION BY RANGE (date);

-- Example partitions (you'd continue this pattern as needed):
CREATE TABLE product_price_history_2023_10 PARTITION OF product_price_history
    FOR VALUES FROM ('2023-10-01') TO ('2023-11-01');

CREATE TABLE product_price_history_2023_11 PARTITION OF product_price_history
    FOR VALUES FROM ('2023-11-01') TO ('2023-12-01');

-- Other indexes will be added when implemented

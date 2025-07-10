-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO products (name, price) VALUES 
('MacBook Pro', 1999.99),
('iPhone 15', 799.99),
('iPad Air', 599.99),
('AirPods Pro', 249.99),
('Apple Watch', 399.99),
('Magic Mouse', 79.99),
('Magic Keyboard', 179.99),
('Studio Display', 1599.99)
ON CONFLICT DO NOTHING;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

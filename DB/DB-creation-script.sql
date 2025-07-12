-- Database: medifinder

-- Drop database if it exists and create a new one
-- DROP DATABASE IF EXISTS medifinder;
-- CREATE DATABASE medifinder WITH ENCODING = 'UTF8';

-- Connect to the database
-- \c medifinder

-- Create extension for full text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create regions table
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create medical_centers table
CREATE TABLE medical_centers (
    center_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    region_id INTEGER REFERENCES regions(region_id),
    category VARCHAR(20),
    reporter_name VARCHAR(200),
    institution_type VARCHAR(100),
    reporter_type VARCHAR(50),
    address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_medical_centers_code UNIQUE (code)
);

-- Create product_types table
CREATE TABLE product_types (
    type_id SERIAL PRIMARY KEY,
    code CHAR(1) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_types_code UNIQUE (code)
);

-- Create products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type_id INTEGER REFERENCES product_types(type_id),
    description TEXT,
    dosage_form VARCHAR(100),
    strength VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_products_code UNIQUE (code)
);

-- Create inventory table
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    center_id INTEGER NOT NULL REFERENCES medical_centers(center_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    current_stock INTEGER NOT NULL DEFAULT 0,
    avg_monthly_consumption DOUBLE PRECISION,
    accumulated_consumption_4m INTEGER,
    measurement DOUBLE PRECISION,
    last_month_consumption INTEGER,
    last_month_stock INTEGER,
    status_indicator VARCHAR(50),
    cpma_12_months_ago DOUBLE PRECISION,
    cpma_24_months_ago DOUBLE PRECISION,
    cpma_36_months_ago DOUBLE PRECISION,
    accumulated_consumption_12m INTEGER,
    report_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVO',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_center_product_report UNIQUE (center_id, product_id, report_date)
);

-- Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    user_password VARCHAR(15) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    user_name VARCHAR(100),
    preferred_location VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_phone_number UNIQUE (phone_number)
);

-- Create search_history table
CREATE TABLE search_history (
    search_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    product_query VARCHAR(255),
    location_query VARCHAR(255),
    search_radius DOUBLE PRECISION,
    results_count INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating timestamps
CREATE TRIGGER update_regions_timestamp BEFORE UPDATE ON regions
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_medical_centers_timestamp BEFORE UPDATE ON medical_centers
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_product_types_timestamp BEFORE UPDATE ON product_types
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_products_timestamp BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_inventory_timestamp BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Create indexes for performance optimization

-- Geographic search optimization
CREATE INDEX idx_medical_centers_location ON medical_centers (latitude, longitude);

-- Medicine name search optimization
CREATE INDEX idx_products_name ON products USING gin (name gin_trgm_ops);
CREATE INDEX idx_products_code ON products (code);

-- Inventory query optimization
CREATE INDEX idx_inventory_center_product ON inventory (center_id, product_id);
CREATE INDEX idx_inventory_current_stock ON inventory (current_stock);
CREATE INDEX idx_inventory_status_indicator ON inventory (status_indicator);
CREATE INDEX idx_inventory_report_date ON inventory (report_date);

-- User interaction optimization
CREATE INDEX idx_users_phone_number ON users (phone_number);
CREATE INDEX idx_search_history_created_at ON search_history (created_at);
CREATE INDEX idx_search_history_user_id ON search_history (user_id);

-- Insert initial product types
INSERT INTO product_types (code, name, description) VALUES 
('M', 'Medicine', 'Pharmaceutical products including tablets, injections, syrups, etc.'),
('I', 'Instrument/Supply', 'Medical supplies, instruments, and equipment');

-- Sample trigger function for inventory updates (optional)
CREATE OR REPLACE FUNCTION check_inventory_stock()
RETURNS TRIGGER AS $$
BEGIN
    -- Update status_indicator based on stock levels and consumption
    IF NEW.current_stock IS NOT NULL AND NEW.avg_monthly_consumption IS NOT NULL AND NEW.avg_monthly_consumption > 0 THEN
        IF NEW.current_stock = 0 THEN
            NEW.status_indicator = 'Desabastecido';
        ELSIF NEW.current_stock < NEW.avg_monthly_consumption THEN
            NEW.status_indicator = 'Substock';
        ELSIF NEW.current_stock > NEW.avg_monthly_consumption * 3 THEN
            NEW.status_indicator = 'Sobrestock';
        ELSE
            NEW.status_indicator = 'Normostock';
        END IF;
    ELSIF NEW.current_stock = 0 THEN
        NEW.status_indicator = 'Desabastecido';
    ELSIF NEW.avg_monthly_consumption IS NULL OR NEW.avg_monthly_consumption = 0 THEN
        IF NEW.current_stock > 0 THEN
            NEW.status_indicator = 'Sin_Rotación';
        ELSE
            NEW.status_indicator = 'Sin_Consumo';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_check_inventory_stock
BEFORE INSERT OR UPDATE ON inventory
FOR EACH ROW EXECUTE FUNCTION check_inventory_stock();

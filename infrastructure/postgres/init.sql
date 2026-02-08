-- Wafaa Platform Database Initialization
-- This script runs on first database creation only

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create test database for running tests
CREATE DATABASE wafaa_test;
GRANT ALL PRIVILEGES ON DATABASE wafaa_test TO wafaa_user;

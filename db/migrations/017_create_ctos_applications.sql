
-- CTOS Applications Table
-- Stores personal and company CTOS consent form submissions

CREATE TABLE IF NOT EXISTS ctos_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    application_type TEXT NOT NULL CHECK(application_type IN ('personal', 'company')),
    application_date DATE NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'completed')),
    
    -- Personal CTOS fields
    full_name TEXT,
    ic_number TEXT,
    occupation TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    
    -- Company CTOS fields
    company_name TEXT,
    registration_number TEXT,
    company_address TEXT,
    authorized_person TEXT,
    authorized_phone TEXT,
    
    -- File paths
    ic_front_path TEXT,
    ic_back_path TEXT,
    ssm_path TEXT,
    signature_path TEXT,
    seal_path TEXT,
    pdf_path TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ctos_customer ON ctos_applications(customer_id);
CREATE INDEX IF NOT EXISTS idx_ctos_type ON ctos_applications(application_type);
CREATE INDEX IF NOT EXISTS idx_ctos_status ON ctos_applications(status);

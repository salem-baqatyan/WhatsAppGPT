CREATE TABLE users (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    email VARCHAR(255) UNIQUE NOT NULL,

    password_hash TEXT NOT NULL,

    name VARCHAR(255),

    role user_role NOT NULL DEFAULT 'CUSTOMER',

    status user_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW()

);



CREATE TABLE companies (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    slug VARCHAR(100) UNIQUE NOT NULL,

    display_name VARCHAR(255) NOT NULL,

    description TEXT,

    status company_status NOT NULL DEFAULT 'TRIAL',

    trial_ends_at TIMESTAMP,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW()

);



CREATE TABLE company_settings (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID UNIQUE NOT NULL
    REFERENCES companies(id) ON DELETE CASCADE,

    timezone VARCHAR(100) DEFAULT 'Asia/Aden',

    language VARCHAR(20) DEFAULT 'ar',

    session_memory_size INTEGER DEFAULT 5,

    auto_reply_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),

    updated_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE plans (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) UNIQUE NOT NULL,

    price NUMERIC(10,2),

    currency VARCHAR(10) DEFAULT 'USD',

    memory_limit INTEGER DEFAULT 5,

    allow_images BOOLEAN DEFAULT FALSE,

    allow_reports BOOLEAN DEFAULT FALSE,

    allow_analytics BOOLEAN DEFAULT FALSE,

    allow_export BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE subscriptions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id),

    plan_id UUID NOT NULL
    REFERENCES plans(id),

    status subscription_status
    DEFAULT 'ACTIVE',

    started_at TIMESTAMP,

    expires_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE waha_instances (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id) ON DELETE CASCADE,

    container_name VARCHAR(255) UNIQUE NOT NULL,

    docker_port INTEGER,

    session_name VARCHAR(100) DEFAULT 'default',

    phone_number VARCHAR(50),

    status waha_status DEFAULT 'CREATED',

    webhook_url TEXT,

    last_connected_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE system_ports (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    port_number INTEGER UNIQUE NOT NULL,

    company_id UUID
    REFERENCES companies(id)
    ON DELETE SET NULL,

    is_reserved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE ai_providers (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    provider ai_provider NOT NULL,

    encrypted_key TEXT NOT NULL,

    model VARCHAR(255),

    temperature NUMERIC(3,2) DEFAULT 0.70,

    enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id, provider)

);



CREATE TABLE company_profiles (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID UNIQUE NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    description TEXT,

    category VARCHAR(100),

    language VARCHAR(20),

    channel VARCHAR(50),

    positioning TEXT,

    working_hours TEXT,

    phone VARCHAR(50),

    website TEXT,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE knowledge_services (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    sort_order INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE knowledge_products (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    price NUMERIC(10,2),

    currency VARCHAR(10) DEFAULT 'USD',

    availability BOOLEAN DEFAULT TRUE,

    image_url TEXT,

    sku VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id, sku)

);



CREATE TABLE knowledge_faq (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    question TEXT NOT NULL,

    answer TEXT NOT NULL,

    tags TEXT[],

    priority INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE customers (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    phone VARCHAR(50) NOT NULL,

    name VARCHAR(255),

    notes TEXT,

    last_seen TIMESTAMP,

    is_blocked BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id, phone)

);



CREATE TABLE conversations (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    customer_id UUID NOT NULL
    REFERENCES customers(id)
    ON DELETE CASCADE,

    status conversation_status DEFAULT 'OPEN',

    messages_count INTEGER DEFAULT 0,

    started_at TIMESTAMP DEFAULT NOW(),

    last_message_at TIMESTAMP,

    closed_at TIMESTAMP

);



CREATE TABLE messages (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    conversation_id UUID NOT NULL
    REFERENCES conversations(id)
    ON DELETE CASCADE,

    customer_id UUID
    REFERENCES customers(id)
    ON DELETE SET NULL,

    role message_role NOT NULL,

    content JSONB NOT NULL,

    provider VARCHAR(50),

    token_count INTEGER DEFAULT 0,

    cost NUMERIC(12,6) DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE customer_questions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    customer_id UUID NOT NULL
    REFERENCES customers(id)
    ON DELETE CASCADE,

    question TEXT NOT NULL,

    category VARCHAR(100),

    asked_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE knowledge_gaps (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    question TEXT NOT NULL,

    count INTEGER DEFAULT 1,

    resolved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE usage_stats (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID UNIQUE NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    messages_count INTEGER DEFAULT 0,

    customers_count INTEGER DEFAULT 0,

    tokens_used BIGINT DEFAULT 0,

    images_sent INTEGER DEFAULT 0,

    failed_answers INTEGER DEFAULT 0,

    updated_at TIMESTAMP DEFAULT NOW()

);



CREATE TABLE reports (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    type report_type NOT NULL,

    status report_status DEFAULT 'GENERATING',

    period VARCHAR(30),

    generated_at TIMESTAMP,

    file_path TEXT

);



CREATE TABLE notifications (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    company_id UUID NOT NULL
    REFERENCES companies(id)
    ON DELETE CASCADE,

    type notification_type NOT NULL,

    status notification_status DEFAULT 'PENDING',

    sent_at TIMESTAMP

);



CREATE TABLE audits (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID
    REFERENCES users(id)
    ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,

    entity VARCHAR(100),

    entity_id UUID,

    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW()

);
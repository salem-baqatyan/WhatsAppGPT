CREATE INDEX idx_companies_user_id
ON companies(user_id);



CREATE INDEX idx_subscriptions_company_id
ON subscriptions(company_id);

CREATE INDEX idx_subscriptions_plan_id
ON subscriptions(plan_id);



CREATE INDEX idx_waha_company_id
ON waha_instances(company_id);



CREATE INDEX idx_ports_company_id
ON system_ports(company_id);



CREATE INDEX idx_ai_company_id
ON ai_providers(company_id);



CREATE INDEX idx_services_company_id
ON knowledge_services(company_id);



CREATE INDEX idx_products_company_id
ON knowledge_products(company_id);

CREATE INDEX idx_products_name
ON knowledge_products(name);



CREATE INDEX idx_faq_company_id
ON knowledge_faq(company_id);



CREATE INDEX idx_customers_company_id
ON customers(company_id);

CREATE INDEX idx_customers_phone
ON customers(phone);



CREATE INDEX idx_conversations_company_id
ON conversations(company_id);

CREATE INDEX idx_conversations_customer_id
ON conversations(customer_id);

CREATE INDEX idx_conversations_last_message
ON conversations(last_message_at);



CREATE INDEX idx_messages_company_id
ON messages(company_id);

CREATE INDEX idx_messages_conversation_id
ON messages(conversation_id);

CREATE INDEX idx_messages_customer_id
ON messages(customer_id);

CREATE INDEX idx_messages_created_at
ON messages(created_at);



CREATE INDEX idx_questions_company_id
ON customer_questions(company_id);

CREATE INDEX idx_questions_customer_id
ON customer_questions(customer_id);



CREATE INDEX idx_gaps_company_id
ON knowledge_gaps(company_id);



CREATE INDEX idx_reports_company_id
ON reports(company_id);



CREATE INDEX idx_notifications_company_id
ON notifications(company_id);



CREATE INDEX idx_audits_user_id
ON audits(user_id);

CREATE INDEX idx_audits_created_at
ON audits(created_at);
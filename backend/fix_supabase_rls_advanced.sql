-- Script para configurar RLS (Row Level Security) com isolamento total por provedor
-- Versão avançada que suporta múltiplos provedores
-- Execute este script no SQL Editor do Supabase

-- Remover políticas existentes
DROP POLICY IF EXISTS "conversations_allow_all" ON conversations;
DROP POLICY IF EXISTS "contacts_allow_all" ON contacts;
DROP POLICY IF EXISTS "conversations_provedor_policy" ON conversations;
DROP POLICY IF EXISTS "contacts_provedor_policy" ON contacts;
DROP POLICY IF EXISTS "auditoria_provedor_policy" ON auditoria;
DROP POLICY IF EXISTS "csat_feedback_provedor_policy" ON csat_feedback;
DROP POLICY IF EXISTS "mensagens_provedor_policy" ON mensagens;
DROP POLICY IF EXISTS "conversations_provedor_isolation" ON conversations;
DROP POLICY IF EXISTS "contacts_provedor_isolation" ON contacts;
DROP POLICY IF EXISTS "auditoria_provedor_isolation" ON auditoria;
DROP POLICY IF EXISTS "csat_feedback_provedor_isolation" ON csat_feedback;
DROP POLICY IF EXISTS "mensagens_provedor_isolation" ON mensagens;
DROP POLICY IF EXISTS "conversations_provedor_access" ON conversations;
DROP POLICY IF EXISTS "contacts_provedor_access" ON contacts;
DROP POLICY IF EXISTS "auditoria_provedor_access" ON auditoria;
DROP POLICY IF EXISTS "csat_feedback_provedor_access" ON csat_feedback;
DROP POLICY IF EXISTS "mensagens_provedor_access" ON mensagens;

-- Configurar RLS para todas as tabelas
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE auditoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE csat_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- Criar função para obter provedor_id do header
CREATE OR REPLACE FUNCTION get_provedor_id()
RETURNS bigint AS $$
BEGIN
    -- Tentar obter do header X-Provedor-ID
    IF current_setting('request.headers', true)::json->>'x-provedor-id' IS NOT NULL THEN
        RETURN (current_setting('request.headers', true)::json->>'x-provedor-id')::bigint;
    END IF;
    
    -- Fallback para provedor_id 1 se não conseguir obter do header
    RETURN 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Políticas RLS usando a função
CREATE POLICY "conversations_provedor_filter" ON conversations
    FOR ALL USING (provedor_id = get_provedor_id());

CREATE POLICY "contacts_provedor_filter" ON contacts
    FOR ALL USING (provedor_id = get_provedor_id());

CREATE POLICY "auditoria_provedor_filter" ON auditoria
    FOR ALL USING (provedor_id = get_provedor_id());

CREATE POLICY "csat_feedback_provedor_filter" ON csat_feedback
    FOR ALL USING (provedor_id = get_provedor_id());

CREATE POLICY "mensagens_provedor_filter" ON mensagens
    FOR ALL USING (provedor_id = get_provedor_id());

-- Verificar se as políticas foram criadas
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('conversations', 'contacts', 'auditoria', 'csat_feedback', 'mensagens')
ORDER BY tablename, policyname;

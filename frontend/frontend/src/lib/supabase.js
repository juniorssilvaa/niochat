import { createClient } from '@supabase/supabase-js'

// Configurações do Supabase
const supabaseUrl = 'https://uousrmdefljusigvncrb.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvdXNybWRlZmxqdXNpZ3ZuY3JiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5ODQyODgsImV4cCI6MjA3NTU2MDI4OH0._DLHRiae-1eVA31SpPl-M36D12HH5G7jmylIRLKyZ_I'

// Criar cliente Supabase
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
})

// Função para buscar mensagens de uma conversa
export const getMessages = async (conversationId, provedorId) => {
  try {
    const { data, error } = await supabase
      .from('mensagens')
      .select('*')
      .eq('conversation_id', conversationId)
      .eq('provedor_id', provedorId)
      .order('created_at', { ascending: true })
    
    if (error) throw error
    return data
  } catch (error) {
    console.error('Erro ao buscar mensagens:', error)
    return []
  }
}

// Função para buscar auditoria
export const getAuditLogs = async (provedorId, filters = {}) => {
  try {
    let query = supabase
      .from('auditoria')
      .select('*')
      .eq('provedor_id', provedorId)
      .order('created_at', { ascending: false })
    
    // Aplicar filtros
    if (filters.conversation_closed) {
      query = query.eq('action', 'conversation_closed_agent')
    }
    
    if (filters.date_from) {
      query = query.gte('created_at', filters.date_from)
    }
    
    if (filters.date_to) {
      query = query.lte('created_at', filters.date_to)
    }
    
    const { data, error } = await query
    
    if (error) throw error
    return data
  } catch (error) {
    console.error('Erro ao buscar auditoria:', error)
    return []
  }
}

// Função para buscar CSAT feedback
export const getCSATFeedback = async (provedorId, filters = {}) => {
  try {
    let query = supabase
      .from('csat_feedback')
      .select('*')
      .eq('provedor_id', provedorId)
      .order('created_at', { ascending: false })
    
    // Aplicar filtros
    if (filters.date_from) {
      query = query.gte('created_at', filters.date_from)
    }
    
    if (filters.date_to) {
      query = query.lte('created_at', filters.date_to)
    }
    
    const { data, error } = await query
    
    if (error) throw error
    return data
  } catch (error) {
    console.error('Erro ao buscar CSAT:', error)
    return []
  }
}

// Função para calcular satisfação média
export const getAverageSatisfaction = async (provedorId, filters = {}) => {
  try {
    const csatData = await getCSATFeedback(provedorId, filters)
    
    if (csatData.length === 0) return 0
    
    const totalRating = csatData.reduce((sum, item) => sum + item.rating_value, 0)
    return (totalRating / csatData.length).toFixed(1)
  } catch (error) {
    console.error('Erro ao calcular satisfação média:', error)
    return 0
  }
}

// Função para calcular taxa de resolução
export const getResolutionRate = async (provedorId, filters = {}) => {
  try {
    const auditData = await getAuditLogs(provedorId, { ...filters, conversation_closed: true })
    
    if (auditData.length === 0) return 0
    
    // Contar conversas resolvidas (fechadas)
    const resolvedConversations = auditData.length
    
    // Aqui você pode adicionar lógica para contar total de conversas se necessário
    // Por enquanto, retornamos a porcentagem baseada nas conversas fechadas
    return resolvedConversations
  } catch (error) {
    console.error('Erro ao calcular taxa de resolução:', error)
    return 0
  }
}

// Função para escutar mudanças em tempo real
export const subscribeToMessages = (conversationId, provedorId, callback) => {
  return supabase
    .channel('messages')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'mensagens',
      filter: `conversation_id=eq.${conversationId}`
    }, callback)
    .subscribe()
}

// Função para escutar mudanças na auditoria
export const subscribeToAudit = (provedorId, callback) => {
  return supabase
    .channel('audit')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'auditoria',
      filter: `provedor_id=eq.${provedorId}`
    }, callback)
    .subscribe()
}

// Função para escutar mudanças no CSAT
export const subscribeToCSAT = (provedorId, callback) => {
  return supabase
    .channel('csat')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'csat_feedback',
      filter: `provedor_id=eq.${provedorId}`
    }, callback)
    .subscribe()
}


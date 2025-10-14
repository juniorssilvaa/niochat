from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet, InboxViewSet, ConversationViewSet,
    MessageViewSet, TeamViewSet, TeamMemberViewSet,
    serve_media_file, DashboardStatsView, ConversationAnalysisView
)
from .views_internal_chat import (
    InternalChatRoomViewSet,
    InternalChatMessageViewSet,
    InternalChatParticipantViewSet,
    InternalChatUnreadCountView,
    InternalChatUnreadByUserView
)
from .views_private_chat import (
    PrivateMessageViewSet,
    PrivateUnreadCountsView,
    UsersListView
)
from .views_csat import (
    CSATFeedbackViewSet,
    CSATRequestViewSet,
    process_csat_webhook
)
from .recovery_views import (
    get_recovery_stats,
    analyze_conversations,
    send_recovery_campaign,
    get_recovery_settings,
    update_recovery_settings
)


router = DefaultRouter()
router.register(r'contacts', ContactViewSet)
router.register(r'inboxes', InboxViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'team-members', TeamMemberViewSet)

# Chat interno
router.register(r'internal-chat/rooms', InternalChatRoomViewSet, basename='internal-chat-rooms')
router.register(r'internal-chat/messages', InternalChatMessageViewSet, basename='internal-chat-messages')
router.register(r'internal-chat/participants', InternalChatParticipantViewSet, basename='internal-chat-participants')

# Chat privado
router.register(r'private-messages', PrivateMessageViewSet, basename='private-messages')

# CSAT
router.register(r'csat/feedbacks', CSATFeedbackViewSet, basename='csat-feedbacks')
router.register(r'csat/requests', CSATRequestViewSet, basename='csat-requests')

urlpatterns = [
    path('', include(router.urls)),
    # URLs específicas para recuperador de conversas (removidas - usando views separadas)
    # URL para servir arquivos de mídia
    path('media/messages/<int:conversation_id>/<str:filename>/', serve_media_file, name='serve-media-file'),

    
    # APIs específicas
    path('private-unread-counts/', PrivateUnreadCountsView.as_view(), name='private-unread-counts'),
    path('internal-chat-unread-count/', InternalChatUnreadCountView.as_view(), name='internal-chat-unread-count'),
    path('internal-chat-unread-by-user/', InternalChatUnreadByUserView.as_view(), name='internal-chat-unread-by-user'),
    path('users-list/', UsersListView.as_view(), name='users-list'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('analysis/', ConversationAnalysisView.as_view(), name='conversation-analysis'),
    path('test-analysis/', ConversationAnalysisView.as_view(), name='test-analysis'),
    
    # CSAT webhook
    path('csat/webhook/', process_csat_webhook, name='csat-webhook'),
    
    # Recuperação de conversas
    path('recovery/stats/', get_recovery_stats, name='recovery-stats'),
    path('recovery/analyze/', analyze_conversations, name='recovery-analyze'),
    path('recovery/campaign/', send_recovery_campaign, name='recovery-campaign'),
    path('recovery/settings/', get_recovery_settings, name='recovery-settings'),
    path('recovery/settings/update/', update_recovery_settings, name='recovery-settings-update'),

]


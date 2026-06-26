from django.urls import path
from .views import SearchView, AnswerView

app_name = 'nlp_processor'

urlpatterns = [
    path('search/', SearchView.as_view(), name='semantic_search'),
    path('answer/', AnswerView.as_view(), name='generate_answer'),
]

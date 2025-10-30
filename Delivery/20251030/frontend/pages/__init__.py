# Pages package
from .home import render as home_render
from .importador import render as importador_render
from .chat import render as chat_render
from .history import render as history_render
from .rag import main as rag_main

__all__ = ['home_render', 'importador_render', 'chat_render', 'history_render', 'rag_main']

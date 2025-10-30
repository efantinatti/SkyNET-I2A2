import streamlit as st

def render_validation_badge(status: str):
    if status == 'success':
        st.success('Validação: ✅ success')
    elif status == 'warning':
        st.warning('Validação: ⚠ warning')
    else:
        st.error('Validação: ❌ error')

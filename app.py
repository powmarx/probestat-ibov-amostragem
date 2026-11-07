"""Trabalho final de Probabilidade e Estatística para IA: três painéis.

    D:\\venvs\\probestat312\\Scripts\\streamlit.exe run app.py
"""
import streamlit as st

import comum as C

st.set_page_config(page_title=C.TITULO, page_icon='📊', layout='wide')
C.estilo()

paginas = st.navigation([
    st.Page('paginas/p1_populacao.py', title='1. População', icon=':material/groups:', default=True),
    st.Page('paginas/p2_amostra.py', title='2. Amostra', icon=':material/filter_alt:'),
    st.Page('paginas/p3_inferencia.py', title='3. Inferência e comparação', icon=':material/functions:'),
])
st.sidebar.caption(f'{C.TITULO}  \n{C.AUTOR}  \nProbabilidade e Estatística para IA')
paginas.run()

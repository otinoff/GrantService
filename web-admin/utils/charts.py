#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Charts utilities for GrantService admin panel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def create_daily_chart(data, title="Статистика по дням"):
    """Создание графика по дням"""
    if not data:
        st.warning("Нет данных для отображения")
        return
    
    # Преобразуем в DataFrame
    df = pd.DataFrame(list(data.items()), columns=['Дата', 'Количество'])
    df['Дата'] = pd.to_datetime(df['Дата'])
    df = df.sort_values('Дата')
    
    # Создаем график
    fig = px.line(df, x='Дата', y='Количество', 
                  title=title,
                  markers=True)
    
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Количество",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_cost_chart(data, title="Затраты по дням"):
    """Создание графика затрат"""
    if not data:
        st.warning("Нет данных о затратах")
        return
    
    # Преобразуем в DataFrame
    df = pd.DataFrame(list(data.items()), columns=['Дата', 'Затраты'])
    df['Дата'] = pd.to_datetime(df['Дата'])
    df = df.sort_values('Дата')
    
    # Создаем график
    fig = px.bar(df, x='Дата', y='Затраты',
                 title=title,
                 color='Затраты',
                 color_continuous_scale='Reds')
    
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Затраты (₽)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_metrics_cards(stats):
    """Создание карточек с метриками"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Всего пользователей",
            value=stats.get('total_users', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Сессий за неделю",
            value=stats.get('recent_sessions', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Завершенных заявок",
            value=stats.get('completed_apps', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Конверсия",
            value=f"{stats.get('conversion_rate', 0)}%",
            delta=None
        )

def create_researcher_metrics(researcher_stats):
    """Создание метрик исследователя"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Всего запросов",
            value=researcher_stats.get('total_queries', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Успешных запросов",
            value=researcher_stats.get('successful_queries', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Успешность",
            value=f"{researcher_stats.get('success_rate', 0)}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Общие затраты",
            value=f"{researcher_stats.get('total_cost', 0):.2f}₽",
            delta=None
        )

def create_popular_queries_chart(queries_data):
    """Создание графика популярных запросов"""
    if not queries_data:
        st.warning("Нет данных о запросах")
        return
    
    # Преобразуем в DataFrame
    df = pd.DataFrame(queries_data, columns=['Запрос', 'Количество'])
    df = df.head(10)  # Топ-10
    
    # Создаем график
    fig = px.bar(df, x='Количество', y='Запрос',
                 title="Популярные запросы",
                 orientation='h')
    
    fig.update_layout(
        xaxis_title="Количество",
        yaxis_title="Запрос",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True) 
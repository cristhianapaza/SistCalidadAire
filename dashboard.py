import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Medición de Calidad de Aire",
    page_icon="🌬️",
    layout="wide"
)

# Función para cargar los datos
@st.cache_data
def load_data():
    # Cargar datos desde el archivo CSV
    df = pd.read_csv('AIRDATA.CSV')
    
    # Convertir timestamp a datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extraer componentes de fecha/hora para análisis
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['month'] = df['timestamp'].dt.month
    df['year'] = df['timestamp'].dt.year
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    return df

# Función para calcular AQI (Índice de Calidad del Aire) basado en PM2.5
def calculate_aqi_pm25(pm25):
    # Puntos de corte para PM2.5 según EPA
    breakpoints = [
        (0, 12, 0, 50, 'Bueno', '#00E400'),
        (12.1, 35.4, 51, 100, 'Moderado', '#FFFF00'),
        (35.5, 55.4, 101, 150, 'Insalubre para Grupos Sensibles', '#FF7E00'),
        (55.5, 150.4, 151, 200, 'Insalubre', '#FF0000'),
        (150.5, 250.4, 201, 300, 'Muy Insalubre', '#99004C'),
        (250.5, 500.4, 301, 500, 'Peligroso', '#7E0023')
    ]
    
    for bp_low, bp_high, aqi_low, aqi_high, category, color in breakpoints:
        if bp_low <= pm25 <= bp_high:
            aqi = ((aqi_high - aqi_low) / (bp_high - bp_low)) * (pm25 - bp_low) + aqi_low
            return round(aqi), category, color
    
    return None, "Fuera de rango", "#000000"

# Función para calcular AQI basado en CO
def calculate_aqi_co(co):
    # Puntos de corte para CO (ppm) según EPA
    breakpoints = [
        (0, 4.4, 0, 50, 'Bueno', '#00E400'),
        (4.5, 9.4, 51, 100, 'Moderado', '#FFFF00'),
        (9.5, 12.4, 101, 150, 'Insalubre para Grupos Sensibles', '#FF7E00'),
        (12.5, 15.4, 151, 200, 'Insalubre', '#FF0000'),
        (15.5, 30.4, 201, 300, 'Muy Insalubre', '#99004C'),
        (30.5, 50.4, 301, 500, 'Peligroso', '#7E0023')
    ]
    
    for bp_low, bp_high, aqi_low, aqi_high, category, color in breakpoints:
        if bp_low <= co <= bp_high:
            aqi = ((aqi_high - aqi_low) / (bp_high - bp_low)) * (co - bp_low) + aqi_low
            return round(aqi), category, color
    
    return None, "Fuera de rango", "#000000"

# Estilo y título
st.title("🌬️ Dashboard de Monitoreo de Calidad del Aire")

# Cargar datos
try:
    df = load_data()
    
    # Añadir columnas de AQI
    df['aqi_pm25'], df['category_pm25'], df['color_pm25'] = zip(*df['pm25'].apply(calculate_aqi_pm25))
    df['aqi_co'], df['category_co'], df['color_co'] = zip(*df['co'].apply(calculate_aqi_co))
    
    # Calcular el AQI general (el máximo de los contaminantes)
    df['aqi'] = df[['aqi_pm25', 'aqi_co']].max(axis=1)
    
    # Determinar la categoría general basada en el AQI más alto
    conditions = [
        (df['aqi'] <= 50),
        (df['aqi'] <= 100),
        (df['aqi'] <= 150),
        (df['aqi'] <= 200),
        (df['aqi'] <= 300),
        (df['aqi'] <= 500)
    ]
    categories = ['Bueno', 'Moderado', 'Insalubre para Grupos Sensibles', 'Insalubre', 'Muy Insalubre', 'Peligroso']
    colors = ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#99004C', '#7E0023']
    
    df['category'] = np.select(conditions, categories, default='Fuera de rango')
    df['color'] = np.select(conditions, colors, default='#000000')
    
    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    
    # Filtro de rango de fechas
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    
    date_range = st.sidebar.date_input(
        "Rango de fechas",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        # Filtrar el dataframe basado en las fechas seleccionadas
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    else:
        filtered_df = df
    
    # Crear KPIs en la primera fila
    col1, col2, col3, col4 = st.columns(4)
    
    # AQI Promedio
    avg_aqi = filtered_df['aqi'].mean()
    max_aqi = filtered_df['aqi'].max()
    
    # Determinar color del AQI promedio
    if avg_aqi <= 50:
        aqi_color = '#00E400'
        aqi_category = 'Bueno'
    elif avg_aqi <= 100:
        aqi_color = '#FFFF00'
        aqi_category = 'Moderado'
    elif avg_aqi <= 150:
        aqi_color = '#FF7E00'
        aqi_category = 'Insalubre para Grupos Sensibles'
    elif avg_aqi <= 200:
        aqi_color = '#FF0000'
        aqi_category = 'Insalubre'
    elif avg_aqi <= 300:
        aqi_color = '#99004C'
        aqi_category = 'Muy Insalubre'
    else:
        aqi_color = '#7E0023'
        aqi_category = 'Peligroso'
    
    with col1:
        st.metric("AQI Promedio", f"{avg_aqi:.1f}")
        st.markdown(f"<div style='padding: 10px; border-radius: 5px; background-color: {aqi_color}; color: black; text-align: center; font-weight: bold;'>{aqi_category}</div>", unsafe_allow_html=True)
    
    with col2:
        st.metric("PM2.5 Promedio (µg/m³)", f"{filtered_df['pm25'].mean():.1f}")
        st.metric("PM2.5 Máximo (µg/m³)", f"{filtered_df['pm25'].max():.1f}")
    
    with col3:
        st.metric("PM10 Promedio (µg/m³)", f"{filtered_df['pm10'].mean():.1f}")
        st.metric("PM10 Máximo (µg/m³)", f"{filtered_df['pm10'].max():.1f}")
    
    with col4:
        st.metric("CO Promedio (ppm)", f"{filtered_df['co'].mean():.1f}")
        st.metric("CO Máximo (ppm)", f"{filtered_df['co'].max():.1f}")
    
    # Segunda fila - Gráficos temporales
    st.subheader("Tendencia de Calidad del Aire")
    
    tab1, tab2 = st.tabs(["Gráficos de Línea", "Gráficos de Calor"])
    
    with tab1:
        # Gráfico de línea para todos los contaminantes
        fig = px.line(
            filtered_df, 
            x='timestamp', 
            y=['pm25', 'pm10', 'co'],
            labels={'value': 'Concentración', 'timestamp': 'Fecha y Hora', 'variable': 'Contaminante'},
            title='Tendencia de Contaminantes',
            color_discrete_map={'pm25': 'red', 'pm10': 'blue', 'co': 'green'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de línea para AQI
        fig = px.line(
            filtered_df, 
            x='timestamp', 
            y='aqi',
            labels={'aqi': 'Índice de Calidad del Aire', 'timestamp': 'Fecha y Hora'},
            title='Tendencia del Índice de Calidad del Aire (AQI)'
        )
        
        # Añadir líneas horizontales para los umbrales de AQI
        fig.add_shape(type="line", x0=filtered_df['timestamp'].min(), y0=50, x1=filtered_df['timestamp'].max(), y1=50,
                     line=dict(color="#00E400", width=1, dash="dash"))
        fig.add_shape(type="line", x0=filtered_df['timestamp'].min(), y0=100, x1=filtered_df['timestamp'].max(), y1=100,
                     line=dict(color="#FFFF00", width=1, dash="dash"))
        fig.add_shape(type="line", x0=filtered_df['timestamp'].min(), y0=150, x1=filtered_df['timestamp'].max(), y1=150,
                     line=dict(color="#FF7E00", width=1, dash="dash"))
        fig.add_shape(type="line", x0=filtered_df['timestamp'].min(), y0=200, x1=filtered_df['timestamp'].max(), y1=200,
                     line=dict(color="#FF0000", width=1, dash="dash"))
        fig.add_shape(type="line", x0=filtered_df['timestamp'].min(), y0=300, x1=filtered_df['timestamp'].max(), y1=300,
                     line=dict(color="#99004C", width=1, dash="dash"))
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Preparar datos para heatmap por hora del día
        if len(filtered_df) > 0:
            # Agrupar por fecha y hora para el heatmap
            heatmap_data = filtered_df.groupby(['date', 'hour'])['aqi'].mean().reset_index()
            heatmap_pivot = heatmap_data.pivot(index='hour', columns='date', values='aqi')
            
            # Crear heatmap con Plotly
            fig = px.imshow(
                heatmap_pivot,
                labels=dict(x="Fecha", y="Hora del día", color="AQI"),
                x=heatmap_pivot.columns,
                y=heatmap_pivot.index,
                color_continuous_scale=[
                    [0, '#00E400'],  # Bueno
                    [0.2, '#FFFF00'],  # Moderado
                    [0.4, '#FF7E00'],  # Insalubre para Grupos Sensibles
                    [0.6, '#FF0000'],  # Insalubre
                    [0.8, '#99004C'],  # Muy Insalubre
                    [1, '#7E0023']    # Peligroso
                ],
                title="Mapa de Calor de AQI por Hora y Día"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay suficientes datos para crear el mapa de calor.")
    
    # Tercera fila - Análisis Detallado
    st.subheader("Análisis Detallado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de categorías de calidad del aire
        cat_counts = filtered_df['category'].value_counts().reset_index()
        cat_counts.columns = ['Categoría', 'Conteo']
        
        # Ordenar las categorías según severidad
        category_order = ['Bueno', 'Moderado', 'Insalubre para Grupos Sensibles', 'Insalubre', 'Muy Insalubre', 'Peligroso']
        cat_counts['Categoría'] = pd.Categorical(cat_counts['Categoría'], categories=category_order, ordered=True)
        cat_counts = cat_counts.sort_values('Categoría')
        
        # Colores para cada categoría
        colors_dict = {
            'Bueno': '#00E400',
            'Moderado': '#FFFF00',
            'Insalubre para Grupos Sensibles': '#FF7E00',
            'Insalubre': '#FF0000',
            'Muy Insalubre': '#99004C',
            'Peligroso': '#7E0023'
        }
        
        fig = px.bar(
            cat_counts, 
            x='Categoría', 
            y='Conteo',
            title='Distribución de Categorías de Calidad del Aire',
            color='Categoría',
            color_discrete_map=colors_dict
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de correlación entre contaminantes, temperatura y humedad
        corr_df = filtered_df[['pm25', 'pm10', 'co', 'temp', 'humidity']].corr()
        
        fig = px.imshow(
            corr_df,
            labels=dict(x="Variable", y="Variable", color="Correlación"),
            x=corr_df.columns,
            y=corr_df.columns,
            color_continuous_scale=px.colors.diverging.RdBu_r,
            title="Correlación entre Variables"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Cuarta fila - Estadísticas por períodos
    st.subheader("Estadísticas por Período")
    
    tab1, tab2, tab3 = st.tabs(["Diario", "Semanal", "Mensual"])
    
    with tab1:
        # Agrupar por día
        daily_stats = filtered_df.groupby('date').agg({
            'pm25': 'mean',
            'pm10': 'mean',
            'co': 'mean',
            'aqi': 'mean',
            'temp': 'mean',
            'humidity': 'mean'
        }).reset_index()
        
        fig = px.line(
            daily_stats, 
            x='date', 
            y='aqi',
            labels={'aqi': 'AQI Promedio', 'date': 'Fecha'},
            title='AQI Promedio Diario',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla de estadísticas diarias
        st.write("Estadísticas Diarias")
        formatted_daily = daily_stats.copy()
        formatted_daily.columns = ['Fecha', 'PM2.5', 'PM10', 'CO', 'AQI', 'Temperatura', 'Humedad']
        formatted_daily = formatted_daily.round(1)
        st.dataframe(formatted_daily, use_container_width=True)
    
    with tab2:
        # Añadir columna de día de la semana
        filtered_df['day_of_week_num'] = filtered_df['timestamp'].dt.dayofweek
        
        # Agrupar por día de la semana
        weekday_stats = filtered_df.groupby('day_of_week').agg({
            'pm25': 'mean',
            'pm10': 'mean',
            'co': 'mean',
            'aqi': 'mean'
        }).reset_index()
        
        # Ordenar los días de la semana
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_stats['day_of_week'] = pd.Categorical(weekday_stats['day_of_week'], categories=weekday_order, ordered=True)
        weekday_stats = weekday_stats.sort_values('day_of_week')
        
        fig = px.bar(
            weekday_stats, 
            x='day_of_week', 
            y='aqi',
            title='AQI Promedio por Día de la Semana',
            labels={'aqi': 'AQI Promedio', 'day_of_week': 'Día de la Semana'},
            color='aqi',
            color_continuous_scale=[
                [0, '#00E400'],
                [0.2, '#FFFF00'],
                [0.4, '#FF7E00'],
                [0.6, '#FF0000'],
                [0.8, '#99004C'],
                [1, '#7E0023']
            ]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Agrupar por mes
        monthly_stats = filtered_df.groupby(['year', 'month']).agg({
            'pm25': 'mean',
            'pm10': 'mean',
            'co': 'mean',
            'aqi': 'mean'
        }).reset_index()
        
        # Crear etiqueta de mes
        monthly_stats['month_name'] = monthly_stats['month'].apply(lambda x: calendar.month_name[x])
        monthly_stats['year_month'] = monthly_stats['year'].astype(str) + '-' + monthly_stats['month_name']
        
        fig = px.bar(
            monthly_stats, 
            x='year_month', 
            y='aqi',
            title='AQI Promedio Mensual',
            labels={'aqi': 'AQI Promedio', 'year_month': 'Mes'},
            color='aqi',
            color_continuous_scale=[
                [0, '#00E400'],
                [0.2, '#FFFF00'],
                [0.4, '#FF7E00'],
                [0.6, '#FF0000'],
                [0.8, '#99004C'],
                [1, '#7E0023']
            ]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Quinta fila - Tabla de datos recientes
    st.subheader("Datos Recientes")
    
    # Mostrar los últimos 10 registros
    recent_data = filtered_df.sort_values('timestamp', ascending=False).head(10)
    recent_display = recent_data[['timestamp', 'pm25', 'pm10', 'co', 'aqi', 'category', 'temp', 'humidity']].copy()
    recent_display.columns = ['Timestamp', 'PM2.5 (µg/m³)', 'PM10 (µg/m³)', 'CO (ppm)', 'AQI', 'Categoría', 'Temperatura (°C)', 'Humedad (%)']
    
    # Estilizar la tabla
    def color_aqi(val):
        if val <= 50:
            return 'background-color: #00E400'
        elif val <= 100:
            return 'background-color: #FFFF00'
        elif val <= 150:
            return 'background-color: #FF7E00'
        elif val <= 200:
            return 'background-color: #FF0000'
        elif val <= 300:
            return 'background-color: #99004C'
        else:
            return 'background-color: #7E0023'
    
    # Aplicar estilo solo a la columna AQI
    styled_recent = recent_display.style.applymap(color_aqi, subset=['AQI'])
    st.dataframe(styled_recent, use_container_width=True)

    # Información sobre AQI
    st.subheader("Información sobre el Índice de Calidad del Aire (AQI)")
    
    aqi_info = pd.DataFrame({
        'Categoría': ['Bueno', 'Moderado', 'Insalubre para Grupos Sensibles', 'Insalubre', 'Muy Insalubre', 'Peligroso'],
        'Rango AQI': ['0-50', '51-100', '101-150', '151-200', '201-300', '301-500'],
        'Color': ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#99004C', '#7E0023'],
        'Significado': [
            'La calidad del aire se considera satisfactoria y la contaminación del aire presenta poco o ningún riesgo.',
            'La calidad del aire es aceptable; sin embargo, puede haber preocupación para un pequeño número de personas que son inusualmente sensibles a la contaminación del aire.',
            'Los miembros de grupos sensibles pueden experimentar efectos en la salud. No es probable que el público en general se vea afectado.',
            'Todos pueden comenzar a experimentar efectos en la salud; los miembros de grupos sensibles pueden experimentar efectos más graves.',
            'Advertencias sanitarias de condiciones de emergencia. Es más probable que toda la población se vea afectada.',
            'Alerta sanitaria: todos pueden experimentar efectos de salud más graves.'
        ]
    })
    
    # Mostrar tabla con información sobre AQI
    st.table(aqi_info[['Categoría', 'Rango AQI', 'Significado']])
    
    # Mostrar sección de color AQI
    st.write("Código de Colores AQI:")
    color_cols = st.columns(6)
    for i, (cat, color) in enumerate(zip(aqi_info['Categoría'], aqi_info['Color'])):
        with color_cols[i]:
            st.markdown(f"<div style='padding: 20px; border-radius: 5px; background-color: {color}; color: black; text-align: center; font-weight: bold;'>{cat}</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.write("Asegúrate de que el archivo AIRDATA.CSV existe y tiene el formato correcto.")
import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils import load_metrics


st.set_page_config(
    page_title='ResearchMatch Performance Dashboard',
    page_icon='📊',
    layout='wide'
)

st.title('ResearchMatch Performance Dashboard')
st.markdown('''
This dashboard shows the performance metrics of different matching strategies.
Metrics are updated whenever a matching operation is performed.
''')

# tabs for each metric
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    'Latency',
    'Precision',
    'Recall',
    'F1 Score',
    'BLEU Score',
    'ROUGE Score'
])


def create_box_plot(metric_name: str, tab):
    '''
    Create a box plot for the given metric.
    '''
    metrics = load_metrics()
    if not metrics[metric_name]:
        tab.write('No data available yet.')
        return
    
    df = pd.DataFrame(
        metrics[metric_name], columns=['Strategy', metric_name]
    )
    
    fig = px.box(
        df,
        x='Strategy',
        y=metric_name,
        title=f'{metric_name.title()} Distribution by Strategy',
        color='Strategy'
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title='Matching Strategy',
        yaxis_title=metric_name.title(),
        height=500
    )
    
    tab.plotly_chart(fig, use_container_width=True)


def create_line_plot(metric_name: str, tab):
    '''Create a line plot showing metric trends over time.'''
    metrics = load_metrics()
    if not metrics[metric_name]:
        tab.write('No data available yet.')
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(
        metrics[metric_name], columns=['Strategy', metric_name]
    )
    df['Time'] = range(len(df))
    
    # Create line plot
    fig = px.line(
        df,
        x='Time',
        y=metric_name,
        color='Strategy',
        title=f'{metric_name.title()} Trend Over Time'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Time (Number of Queries)',
        yaxis_title=metric_name.title(),
        height=500
    )
    
    tab.plotly_chart(fig, use_container_width=True)


# plots for each metric
with tab1:
    st.header('Latency Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('latency', st)
    with col2:
        create_line_plot('latency', st)

with tab2:
    st.header('Precision Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('precision', st)
    with col2:
        create_line_plot('precision', st)

with tab3:
    st.header('Recall Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('recall', st)
    with col2:
        create_line_plot('recall', st)

with tab4:
    st.header('F1 Score Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('f1', st)
    with col2:
        create_line_plot('f1', st)

with tab5:
    st.header('BLEU Score Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('bleu', st)
    with col2:
        create_line_plot('bleu', st)

with tab6:
    st.header('ROUGE Score Analysis')
    col1, col2 = st.columns(2)
    with col1:
        create_box_plot('rouge', st)
    with col2:
        create_line_plot('rouge', st)

# section for raw data
st.header('Raw Metrics Data')
metrics = load_metrics()
if any(metrics.values()):
    # DataFrame with all metrics
    data = []
    for i in range(len(metrics['latency'])):
        row = {
            'Strategy': metrics['latency'][i][0],
            'Latency': metrics['latency'][i][1],
            'Precision': metrics['precision'][i][1],
            'Recall': metrics['recall'][i][1],
            'F1': metrics['f1'][i][1],
            'BLEU': metrics['bleu'][i][1],
            'ROUGE': metrics['rouge'][i][1]
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    st.dataframe(df)
else:
    st.write('No data available yet.')

# auto-refresh
time.sleep(1)
st.rerun()
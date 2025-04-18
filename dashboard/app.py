import time
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils import (
    load_metrics,
    rolling_mean,
    rolling_p05,
    rolling_p95,
)


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
    Create metric box plot.
    '''
    metrics = load_metrics()
    if not metrics[metric_name]:
        tab.write('No data available yet.')
        return
    
    df = pd.DataFrame(
        metrics[metric_name],
        columns=['Strategy', 'Timestamp', metric_name]
    )

    # create a color-map
    unique_strategies = df['Strategy'].unique()
    colors = px.colors.qualitative.Plotly
    color_map = {
        strategy: colors[i % len(colors)] for i, strategy in enumerate(unique_strategies)
    }
    
    fig = px.box(
        df,
        x='Strategy',
        y=metric_name,
        title=f'{metric_name.title()} Distribution by Strategy',
        color='Strategy',
        color_discrete_map=color_map
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title='Matching Strategy',
        yaxis_title=metric_name.title(),
        height=500
    )
    
    tab.plotly_chart(fig, use_container_width=True)


def create_line_plot(metric_name: str, tab):
    '''
    Create metric temporal plot.
    '''
    metrics = load_metrics()
    if not metrics[metric_name]:
        tab.write('No data available yet.')
        return
    
    df = pd.DataFrame(
        metrics[metric_name],
        columns=['Strategy', 'Timestamp', metric_name]
    )
    # convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

    # sort for rolling statistics
    df = df.sort_values(by=['Strategy', 'Timestamp'])
    
    df['MA'] = df.groupby('Strategy')[metric_name].transform(rolling_mean)
    df['P05'] = df.groupby('Strategy')[metric_name].transform(rolling_p05)
    df['P95'] = df.groupby('Strategy')[metric_name].transform(rolling_p95)

    # create a color-map
    unique_strategies = df['Strategy'].unique()
    colors = px.colors.qualitative.Plotly
    color_map = {
        strategy: colors[i % len(colors)] for i, strategy in enumerate(unique_strategies)
    }

    # make the plot
    fig = go.Figure()
    for i, strategy in enumerate(unique_strategies):
        strategy_df = df[df['Strategy'] == strategy]
        color = color_map[strategy]
        try:
            # convert plotly hex -> rgba for confidence interval
            rgb = tuple(
                int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)
            )
        except ValueError:
            # assume format 'rgb(r, g, b)'
            print(
                f'Warning: Could not parse color {color}. Using default grey fill.'
            )
            rgb = (128, 128, 128) 
            
        fill_color_rgba = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.2)'

        # lower bound (P05)
        fig.add_trace(go.Scatter(
            x=strategy_df['Timestamp'],
            y=strategy_df['P05'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

        # upper bound (P95)
        fig.add_trace(go.Scatter(
            x=strategy_df['Timestamp'],
            y=strategy_df['P95'],
            mode='lines',
            line=dict(width=0),
            fillcolor=fill_color_rgba,
            fill='tonexty',
            showlegend=False,
             hoverinfo='skip'
        ))

        # moving average (MA)
        fig.add_trace(go.Scatter(
            x=strategy_df['Timestamp'],
            y=strategy_df['MA'],
            mode='lines',
            line=dict(color=color),
            name=strategy,
            hovertemplate = (
                f'<b>{strategy}</b><br>Time: %{{x}}<br>{metric_name.title()} (MA): %{{y:.4f}}<extra></extra>'
            )
        ))
    
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title=metric_name.title(),
        height=500,
        hovermode='x unified'
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
    num_entries = len(metrics.get('latency', []))
    for i in range(num_entries):
        row = {'Strategy': metrics['latency'][i][0],
               'Timestamp': pd.to_datetime(metrics['latency'][i][1], unit='s'), # convert timestamp
               'Latency': metrics['latency'][i][2],
               'Precision': metrics['precision'][i][2],
               'Recall': metrics['recall'][i][2],
               'F1': metrics['f1'][i][2],
               'BLEU': metrics['bleu'][i][2],
               'ROUGE': metrics['rouge'][i][2]}
        data.append(row)
    
    if data: # Check if data was populated
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.write('No data available yet.')
else:
    st.write('No data available yet.')

# auto-refresh
time.sleep(1)
st.rerun()
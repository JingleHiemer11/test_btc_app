#Display BTC Charts with Plotly

#import datetime
#import plotly.graph_objects as go
#import streamlit as st

#def plot_price_chart(prices, currency, days):
#    dates = [datetime.datetime.fromtimestamp(p[0] / 1000) for p in prices]
#    values = [p[1] for p in prices]

#    fig = go.Figure()
#    fig.add_trace(go.Scatter(
#        x=dates, y=values, mode='lines', name='BTC',
#        hovertemplate='%{x}<br>$%{y:,.2f}<extra></extra>',
#        line=dict(color='orange')
#    ))
#    fig.update_layout(
#        title=f"BTC Price in {currency.upper()} - Last {days} Day(s)",
#        xaxis_title="Date", yaxis_title=f"Price ({currency.upper()})",
#        hovermode="x unified"
#    )
#    st.plotly_chart(fig, use_container_width=True)
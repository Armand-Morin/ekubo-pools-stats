import numpy as np
import pandas as pd
import plotly.graph_objs as go
import imageio
import os

def liquidity_shape(pool_data):
    tick_spacing = pool_data['TICK_SPACING'].iloc[0] # 19802
    ticks = range(pool_data['LOWER_TICK'].min(), pool_data['UPPER_TICK'].max() + tick_spacing, tick_spacing)
    liquidity_per_tick = {tick: 0 for tick in ticks}

    # Compute liquidity for each tick
    for _, row in pool_data.iterrows():
        for tick in range(row['LOWER_TICK'], row['UPPER_TICK'] + tick_spacing, tick_spacing):
            if tick in liquidity_per_tick:
                if row['EVENT_NAME'] != 'Burn':
                    liquidity_per_tick[tick] += float(row['LIQUIDITY_AMOUNT'])
                if row['EVENT_NAME'] != 'Mint':
                    liquidity_per_tick[tick] -= float(row['LIQUIDITY_AMOUNT'])

    return liquidity_per_tick

def plot_liquidity_shape(liquidity_per_tick, current_tick, tick_spacing, title):
    ticks = [tick + tick_spacing / 2 for tick in liquidity_per_tick.keys()]  # Center the bars
    liquidity_values = list(liquidity_per_tick.values())
    data = [go.Bar(x=ticks, y=liquidity_values, name='Liquidity Amount')]
    data.append(go.Scatter(x=[current_tick, current_tick], y=[min(liquidity_values), max(liquidity_values)],
                           mode='lines', name=f'Current Tick {current_tick//10**6}', line=dict(color='red', dash='dash')))
    layout = go.Layout(
        title=title,
        yaxis=dict(title='Liquidity Amount'),
        xaxis=dict(title='Tick', range=[-20.8e6, -19.6e6]),
        hovermode='closest',
        width=800,
        height=600,
    )
    fig = go.Figure(data=data, layout=layout)
    return fig


def create_gif(n_frames=100):
    df = pd.read_csv('ekubo_market_depth_dataset.csv')

    df['time'] = pd.to_datetime(df['BLOCK_TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
    df.sort_values('time', inplace=True)
    df.set_index('time', inplace=True)

    pool_id = df['POOL_ID'].values[0]
    pool_data = df[df['POOL_ID'] == pool_id].copy()

    increments = np.linspace(0.001, 1, n_frames)
    for increment in increments:
        subset_size = int(len(pool_data) * increment)
        subset_data = pool_data.iloc[:subset_size]
        liquidity_per_tick = liquidity_shape(subset_data)
        fig = plot_liquidity_shape(liquidity_per_tick, subset_data['SWAP_TICK'].iloc[0], subset_data['TICK_SPACING'].iloc[0], f'Liquidity Shape at time {subset_data.index[-1]}')
        fig.write_image(f'img/frame_{int(increment*100):03d}.png')


    image_folder = 'img'

    images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(".png")]

    images.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))

    gif_path = 'liquidity_shape.gif'
    with imageio.get_writer(gif_path, mode='I') as writer:
        for filename in images:
            image = imageio.imread(filename)
            writer.append_data(image)

    print(f"GIF created successfully at: {gif_path}")

create_gif(n_frames=100)
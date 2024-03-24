import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('ekubo_market_depth_dataset.csv')

df['time'] = pd.to_datetime(df['BLOCK_TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
df.sort_values('time', inplace=True)
df.set_index('time', inplace=True)

pool_id = df['POOL_ID'].values[0]
pool_data = df[df['POOL_ID'] == pool_id].copy()

traders_id = set(pool_data['FROM_ADDRESS'].values)

# Filter traders who have at least 6 mint or burn events
traders_with_enough_events = []
for trader_id in traders_id:
    num_events = len(pool_data[(pool_data['FROM_ADDRESS'] == trader_id) & (pool_data['EVENT_NAME'].isin(['Mint', 'Burn']))])
    if num_events >= 12:
        traders_with_enough_events.append(trader_id)

# Iterate over traders with enough events and plot their ranges
for trader_id in traders_with_enough_events:
    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(15, 5))

    # Plot on the full range
    pool_data[pool_data['EVENT_NAME'] == 'Swap'].PRICE.rolling(20).mean().plot(ax=ax1)
    tmp = pool_data[pool_data['FROM_ADDRESS'] == trader_id]
    upper_price = tmp[tmp['EVENT_NAME'] == 'Mint'].UPPER_PRICE
    lower_price = tmp[tmp['EVENT_NAME'] == 'Mint'].LOWER_PRICE
    ax1.step(upper_price.index, upper_price, where='post')
    ax1.step(lower_price.index, lower_price, where='post')

    # Plot on the limited range
    min_time = min(upper_price.index.min(), lower_price.index.min())
    max_time = max(upper_price.index.max(), lower_price.index.max())
    limited_data = pool_data[(pool_data.index >= min_time) & (pool_data.index <= max_time) & (pool_data['EVENT_NAME'] == 'Swap')]
    limited_data.PRICE.rolling(20).mean().plot(ax=ax2)
    ax2.step(upper_price.index, upper_price, where='post')
    ax2.step(lower_price.index, lower_price, where='post')

    ax1.legend(['Price', 'Upper Price', 'Lower Price'])
    ax2.legend(['Price', 'Upper Price', 'Lower Price'])

    # write title of the full figure
    fig.suptitle(f'Trader {trader_id} Price Ranges')

    # Limit the x-axis range for the second graph
    ax2.set_xlim([min_time, max_time])

    plt.tight_layout()
    #plt.show()

    # save figure
    fig.savefig(f'positions/trader_{trader_id}_price_ranges.png')

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

def market_depth(pool_data, depth):

    """
    Calculate market depth based on token amounts within a specified depth range

    Params:
    - pool_data: DataFrame containing the pool data.
    - depth: The depth percentage (e.g., 0.01 for 1%).

    Returns:
    - The total USD value of tokens within the depth range.
    """

    def price_to_tick(price):
        return int(np.log(price/10**12) / np.log(1.000001))

    tick_spacing = pool_data['TICK_SPACING'].iloc[0]  # Assume a uniform tick spacing for simplicity
    current_price = pool_data['PRICE'].iloc[-1]
    lower_bound_price = current_price / (1 + depth)
    upper_bound_price = current_price * (1 + depth)
    lower_bound_tick = price_to_tick(lower_bound_price)
    upper_bound_tick = price_to_tick(upper_bound_price)
    print('Current price:', round(current_price))
    print('Lower price:', round(lower_bound_price))
    print('Upper price:', round(upper_bound_price))
    print('Lower tick :', round(lower_bound_tick))
    print('Upper tick :', round(upper_bound_tick))
    
    # Initialize the total USD value
    total_usd_value = 0

    for _, row in pool_data.iterrows():
        lower_tick = row['LOWER_TICK']
        upper_tick = row['UPPER_TICK']

        # Check if the position's range overlaps with the depth range
        if not (lower_bound_tick > upper_tick or upper_bound_tick < lower_tick):
            # Calculate the number of ticks covered by this position
            num_ticks = (upper_tick - lower_tick) // tick_spacing + 1

            # Distribute token amounts equally across all ticks
            token0_per_tick = float(row['TOKEN0_REAL_AMOUNT']) / num_ticks
            token1_per_tick = float(row['TOKEN1_REAL_AMOUNT']) / num_ticks

            # the USD value of token0 is direct and token1 needs to be multiplied by the current price
            # Adjust based on your token valuation model
            if row['EVENT_NAME'] != 'Burn':
                total_usd_value -= token1_per_tick * num_ticks
                # total_usd_value -= (token0_per_tick + token1_per_tick * current_price) * num_ticks
            if row['EVENT_NAME'] != 'Mint':
                total_usd_value += token1_per_tick * num_ticks
                # total_usd_value += (token0_per_tick + token1_per_tick * current_price) * num_ticks

    print(f"Market for a depth of {int(depth*100)}  % : {round(total_usd_value)}")
    print('')
    return total_usd_value


def calculate_market_depth(pool_data, depth):
    # Adjusted to pass pool_data as an argument
    return market_depth(pool_data, depth)


if __name__ == '__main__':
    # Load your dataset
    df = pd.read_csv('ekubo_market_depth_dataset.csv')
        
    df['time'] = pd.to_datetime(df['BLOCK_TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
    df.sort_values('time', inplace=True)
    df.set_index('time', inplace=True)

    def calculate_price(tick, token0_decimals, token1_decimals):
        return np.where(tick == 0, 0, (1.000001 ** tick) * (token0_decimals / token1_decimals))

    df['PRICE'] = calculate_price(df['SWAP_TICK'].values, df['TOKEN0_DECIMALS'].values, df['TOKEN1_DECIMALS'].values) * 10**11
    df['UPPER_PRICE'] = calculate_price(df['UPPER_TICK'].values, df['TOKEN0_DECIMALS'].values, df['TOKEN1_DECIMALS'].values) * 10**11
    df['LOWER_PRICE'] = calculate_price(df['LOWER_TICK'].values, df['TOKEN0_DECIMALS'].values, df['TOKEN1_DECIMALS'].values) * 10**11

    pool_id = df['POOL_ID'].values[0]
    pool_data = df[df['POOL_ID'] == pool_id].copy()

    depth_values = [0.2, 0.1, 0.05]

    # Using joblib for parallel execution
    results = Parallel(n_jobs=-1)(delayed(market_depth)(pool_data, depth) for depth in depth_values)

    # Unpacking the results
    depth_value_20, depth_value_10, depth_value_5 = results
    print(f"Depth Value 20%: {depth_value_20}")
    print(f"Depth Value 10%: {depth_value_10}")
    print(f"Depth Value 5%: {depth_value_5}")
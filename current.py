
# two functions when calculating current evaluation period star rating 
# 
import pandas as pd

def restandardize_var(df_current, var, mean_var, std_var, upl_var, lol_var, var_mean_t, var_std_t):
    """
    Standardize, truncate, and re-standardize a variable
    
    Parameters:
    df_current : DataFrame containing current evaluation period data
    var : str - variable name to process
    mean_var : float - mean value for standardization
    std_var : float - standard deviation for standardization
    upl_var : float - upper limit from baseline
    lol_var : float - lower limit from baseline
    var_mean_t : float - mean of truncated scores from baseline
    var_std_t : float - std dev of truncated scores from baseline
    
    Returns:
    DataFrame with processed variable added as new columns
    """
    
    # Make a copy to avoid modifying original
    df = df_current.copy()
    
    # STEP 1: Calculate z-scores (standardization)
    df[f'zc_{var}'] = (df[var] - mean_var) / std_var
    
    # Initialize truncated column
    df[f'tc_{var}'] = df[f'zc_{var}']
    
    # STEP 2: Truncate values based on baseline limits
    # Create flag column
    df[f'flagtc_{var}'] = 0
    df.loc[(df[f'tc_{var}'].notna()) & (df[f'tc_{var}'] < lol_var), f'flagtc_{var}'] = 1
    df.loc[df[f'tc_{var}'] > upl_var, f'flagtc_{var}'] = 2
    
    # Apply truncation
    df.loc[df[f'flagtc_{var}'] == 1, f'tc_{var}'] = lol_var
    df.loc[df[f'flagtc_{var}'] == 2, f'tc_{var}'] = upl_var
    
    # STEP 3: Re-standardize truncated scores
    df[f'wc_{var}'] = (df[f'tc_{var}'] - var_mean_t) / var_std_t
    
    # Sort by facility ID (provfs)
    df = df.sort_values('provfs')
    
    return df

# Example usage:
# Assume we have these baseline parameters from previous calculations
# baseline_params = {
#     'mean_var1': 0.5, 'std_var1': 1.2, 'upl_var1': 2.58, 'lol_var1': -2.58,
#     'var1_mean_t': 0.1, 'var1_std_t': 0.9
# }

# processed_df = restandardize_var(
#     df_current=current_data,
#     var='var1',
#     mean_var=baseline_params['mean_var1'],
#     std_var=baseline_params['std_var1'],
#     upl_var=baseline_params['upl_var1'],
#     lol_var=baseline_params['lol_var1'],
#     var_mean_t=baseline_params['var1_mean_t'],
#     var_std_t=baseline_params['var1_std_t']
# )





def calculate_adjusted_measures(adj_factor_df, fivestar_current_df):
    """
    Multiply adjustment factors with current standardized measures
    
    Parameters:
    adj_factor_df : DataFrame containing adjustment factors
    fivestar_current_df : DataFrame containing current star measures
    
    Returns:
    DataFrame with adjusted measures and raw values
    """
    
    # Merge the dataframes on provfs
    merged_df = pd.merge(
        adj_factor_df,
        fivestar_current_df[['provfs', 'yr', 
                           'star_var1_f_current', 'star_var2_f_current',
                           'star_var3_f_current', 'star_var4_f_current',
                           'star_var5_f_current']],
        on='provfs',
        how='inner'
    )
    
    # Calculate adjusted measures
    merged_df['adj_var1_f'] = merged_df['star_var1_f_current'] * merged_df['factor_var1']
    merged_df['adj_var2_f'] = merged_df['star_var2_f_current'] * merged_df['factor_var2']
    merged_df['adj_var3_f'] = merged_df['star_var3_f_current'] * merged_df['factor_var3']
    merged_df['adj_var4_f'] = merged_df['star_var4_f_current'] * merged_df['factor_var4']
    merged_df['adj_var5_f'] = merged_df['star_var5_f_current'] * merged_df['factor_var5']
    
    # Create raw value columns (equivalent to SAS CALCULATED)
    merged_df['raw_var1_f'] = merged_df['adj_var1_f']
    merged_df['raw_var2_f'] = merged_df['adj_var2_f']
    merged_df['raw_var3_f'] = merged_df['adj_var3_f']
    merged_df['raw_var4_f'] = merged_df['adj_var4_f']
    merged_df['raw_var5_f'] = merged_df['adj_var5_f']
    
    # Sort by provfs
    merged_df = merged_df.sort_values('provfs')
    
    return merged_df

# Example usage:
# adjusted_results = calculate_adjusted_measures(adj_factor_data, fivestar_current_data)
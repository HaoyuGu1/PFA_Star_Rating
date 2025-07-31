import pandas as pd
import numpy as np
from scipy.stats import norm
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.weightstats import DescrStatsW

class StarRatingCalculator:
    def __init__(self, df):
        self.df = df.copy()
        self.threshold = 2.58  # Z-score threshold for winsorization
        self.step = 0.001      # Adjustment step size
        
    def assign_availability(self, row, var, cert_date, cutoff, cutoff_v, pt_cnt, pdonly):
        """Determine if measure data is available"""
        if pdnot pdonly and (row[cert_date] >= cutoff_date) and (row[cutoff] < cutoff_v):
            return ("999", "Not Available")
        elif row[pt_cnt] == 0 and var not in ["SRR", "ED"]:
            return ("998", "Not Available")
        elif row[cutoff] < cutoff_v or (var == "SWR" and row[pt_cnt] < 11):
            return ("999", "Not Available")
        else:
            return ("001", "Available")
    
    def preprocess_measures(self):
        """Realign measures to ensure higher values always mean better performance"""
        self.df['star_var3_f'] = 100 - self.df['star_var3_f']
        self.df['star_var4_f'] = 100 - self.df['star_var4_f']
        self.df['star_var6_f'] = -1 * self.df['star_var6_f']
        self.df['star_var7_f'] = -1 * self.df['star_var7_f']
        self.df['star_var8_f'] = -1 * self.df['star_var8_f']
        self.df['star_var9_f'] = -1 * self.df['star_var9_f']
        self.df['yr'] = "baseline"
        
    def calculate_percentiles(self, ratio_vars):
        """Calculate percentiles and probit transforms for ratio measures"""
        # Rank variables (0-199)
        ranked = self.df[ratio_vars].rank(method='average', pct=False) - 1
        ranked = ranked.astype(int)
        
        # Convert to percentiles (0.5-99.5)
        percentiles = (ranked + 1) / 200 * 100
        
        # Probit transformation
        probit = percentiles.apply(lambda x: norm.ppf(x/100))
        
        # Add to dataframe
        for var in ratio_vars:
            self.df[f'p_{var}'] = percentiles[var]
            self.df[f'n_{var}'] = probit[var]
            
        return self.df
    
    def winsorize(self, var):
        """Winsorize a variable to ±2.58 standard deviations"""
        mean_val = self.df[var].mean()
        std_val = self.df[var].std()
        
        # Initial z-scores
        z = (self.df[var] - mean_val) / std_val
        upl, lol = self.threshold, -self.threshold
        t = z.copy()
        
        # Iterative winsorization
        for i in range(1, 10001):
            # Apply current limits
            t = np.where(t > upl, upl, np.where(t < lol, lol, t))
            
            # Calculate new stats
            mean_t = t.mean()
            std_t = t.std()
            w_var = (t - mean_t) / std_t
            
            # Check convergence
            max_w = w_var.max()
            min_w = w_var.min()
            
            if max_w <= self.threshold and min_w >= -self.threshold:
                break
                
            # Adjust limits
            if max_w > self.threshold:
                upl -= self.step
            if min_w < -self.threshold:
                lol += self.step
        
        # Store results
        self.df[f'w_{var}'] = w_var
        self.df[f'{var}_mean_t'] = mean_t
        self.df[f'{var}_std_t'] = std_t
        self.df[f'upl_{var}'] = upl
        self.df[f'lol_{var}'] = lol
        
        return self.df
    
    def calculate_domain_scores(self):
        """Calculate domain scores with missing value handling"""
        # Create missing indicators
        for var in ['n_var1_f', 'n_var2_f', 'n_var3_f', 'n_var4_f']:
            self.df[f'm_{var}'] = self.df[var].isna().astype(int)
            
        for var in ['w_star_var5_f', 'w_star_var6_f', 'w_star_var7_f', 'w_star_var8_f', 'n_var9_f', 'w_star_var10_f']:
            self.df[f'm_{var}'] = self.df[var].isna().astype(int)
        
        # Calculate domain scores
        self.df['factor1'] = np.where(
            (self.df[['m_n_var1_f', 'm_n_var2_f', 'm_n_var3_f', 'm_n_var4_f']].sum(axis=1) == 4),
            np.nan,
            self.df[['n_var1_f', 'n_var2_f', 'n_var3_f', 'n_var4_f']].mean(axis=1)
        )
        
        self.df['factor2'] = np.where(
            (self.df[['m_w_star_var5_f', 'm_w_star_var6_f']].sum(axis=1) == 2),
            np.nan,
            self.df[['w_star_var5_f', 'w_star_var6_f']].mean(axis=1)
        )
        
        self.df['factor3'] = np.where(
            (self.df[['m_w_star_var7_f', 'm_w_star_var8_f']].sum(axis=1) == 2),
            np.nan,
            self.df[['w_star_var7_f', 'w_star_var8_f']].mean(axis=1)
        )
        
        self.df['factor4'] = np.where(
            (self.df[['m_n_var9_f', 'm_w_star_var10_f']].sum(axis=1) == 2),
            np.nan,
            self.df[['n_var9_f', 'w_star_var10_f']].mean(axis=1)
        )
        
        return self.df
    
    def calculate_final_score(self):
        """Calculate final composite score with domain weights"""
        conditions = [
            self.df['factor1'].isna(),
            self.df['factor3'].isna(),
            self.df['factor4'].isna(),
            (self.df['pdflag'] == 0) & self.df['factor2'].isna()
        ]
        
        choices = [
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.where(
                self.df['pdflag'] == 1,
                (2/5)*self.df['factor1'] + (1/5)*self.df['factor3'] + (2/5)*self.df['factor4'],
                (2/7)*self.df['factor1'] + (2/7)*self.df['factor2'] + (1/7)*self.df['factor3'] + (2/7)*self.df['factor4']
            )
        ]
        
        self.df['final_score'] = np.select(conditions, choices, default=choices[-1])
        return self.df
    
    def assign_star_ranks(self):
        """Assign star ratings based on quintiles"""
        # Calculate quintiles
        quintiles = np.percentile(self.df['final_score'].dropna(), [10, 30, 70, 90, 100])
        q1, q2, q3, q4, q5 = quintiles
        
        # Assign star ranks
        conditions = [
            self.df['final_score'].isna(),
            self.df['final_score'] <= q1,
            self.df['final_score'] <= q2,
            self.df['final_score'] <= q3,
            self.df['final_score'] <= q4
        ]
        
        choices = [np.nan, 1, 2, 3, 4, 5]
        
        self.df['starrank'] = np.select(conditions, choices[1:], default=choices[-1])
        return self.df
    
    def calculate_cutoffs(self):
        """Calculate star rating cutoffs"""
        # Get min/max for each star rank
        cutoffs = self.df.groupby('starrank')['final_score'].agg(['min', 'max']).reset_index()
        
        # Calculate boundaries between stars
        self.df['star_1_cutoff'] = (cutoffs.loc[0, 'max'] + cutoffs.loc[1, 'min']) / 2
        self.df['star_2_cutoff'] = (cutoffs.loc[1, 'max'] + cutoffs.loc[2, 'min']) / 2
        self.df['star_3_cutoff'] = (cutoffs.loc[2, 'max'] + cutoffs.loc[3, 'min']) / 2
        self.df['star_4_cutoff'] = (cutoffs.loc[3, 'max'] + cutoffs.loc[4, 'min']) / 2
        
        return self.df
    
    def process(self):
        """Complete star rating calculation pipeline"""
        self.preprocess_measures()
        self.calculate_percentiles(['star_var6_f', 'star_var7_f', 'star_var8_f', 'star_var9_f', 'star_var10_f'])
        
        # Winsorize percentage measures
        for var in ['star_var1_f', 'star_var2_f', 'star_var3_f', 'star_var4_f', 'star_var5_f']:
            self.winsorize(var)
            
        self.calculate_domain_scores()
        self.calculate_final_score()
        self.assign_star_ranks()
        self.calculate_cutoffs()
        
        return self.df

# Example usage:
# calculator = StarRatingCalculator(input_df)
# result_df = calculator.process()
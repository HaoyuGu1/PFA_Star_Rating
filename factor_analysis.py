import pandas as pd
from factor_analyzer import FactorAnalyzer
import matplotlib.pyplot as plt

# Assuming baseline_joined is your DataFrame containing the variables
# var_list = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'w1', 'w2', 'w3', 'w4', 'w5']

def perform_factor_analysis(data, var_list, n_factors=4):
    """
    Perform factor analysis similar to SAS proc factor
    
    Parameters:
    data : pandas DataFrame
    var_list : list of variable names to include in analysis
    n_factors : number of factors to extract
    """
    
    # Subset the data with selected variables
    df = data[var_list].copy()
    
    # Check for missing values
    if df.isnull().any().any():
        print("Warning: Data contains missing values which may affect results")
    
    # Factor analysis with principal axis factoring and SMC priors
    fa = FactorAnalyzer(
        rotation='varimax',  # varimax rotation
        n_factors=n_factors,
        method='principal',  # principal axis factoring
        use_smc=True,        # squared multiple correlations as prior communality estimates
    )
    
    # Fit the model
    fa.fit(df)
    
    # Print factor loadings (rounded)
    loadings = pd.DataFrame(fa.loadings_, index=var_list, 
                          columns=[f'Factor{i+1}' for i in range(n_factors)])
    print("\nFactor Loadings (rotated):")
    print(loadings.round(3))
    
    # Get variance explained
    ev, varexp = fa.get_factor_variance()
    varexp_df = pd.DataFrame({
        'Factor': [f'Factor{i+1}' for i in range(n_factors)],
        'Eigenvalue': ev,
        'Proportion': varexp[0],
        'Cumulative': varexp[1]
    })
    print("\nVariance Explained:")
    print(varexp_df.round(4))
    
    # Scree plot
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(var_list)+1), fa.get_eigenvalues()[0], 'bo-')
    plt.axhline(y=1, color='r', linestyle='--')  # Kaiser criterion line
    plt.title('Scree Plot')
    plt.xlabel('Factor Number')
    plt.ylabel('Eigenvalue')
    plt.grid()
    plt.show()
    
    # MSA (Measure of Sampling Adequacy) - similar to SAS
    from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
    chi_square, p_value = calculate_bartlett_sphericity(df)
    kmo_all, kmo_model = calculate_kmo(df)
    print(f"\nBartlett's test of sphericity: χ² = {chi_square:.1f}, p = {p_value:.4f}")
    print(f"KMO Measure of Sampling Adequacy: {kmo_model:.3f}")
    
    # Factor scores (similar to SAS score option)
    factor_scores = fa.transform(df)
    factor_scores_df = pd.DataFrame(factor_scores, 
                                  columns=[f'Factor{i+1}_Score' for i in range(n_factors)])
    
    # Return results
    results = {
        'loadings': loadings,
        'variance_explained': varexp_df,
        'factor_scores': factor_scores_df,
        'kmo': kmo_model,
        'bartlett': (chi_square, p_value)
    }
    
    return results

# Example usage:
# results = perform_factor_analysis(baseline_joined, 
#                                 ['n1','n2','n3','n4','n5','n6','w1','w2','w3','w4','w5'],
#                                 n_factors=4)
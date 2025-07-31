proc factor data = baseline_joined 
    simple 
    method = p 
    priors = smc 
    nfactors = 4 
    scree
    rotate = varimax 
    round 
    score 
    outstat = pca 
    res 
    msa;
    title 'Four Factor Solution';
    var n1 n2 n3 n4 n5 n6 w1 w2 w3 w4 w5;
    ods output varexplain = varexp_k4;
run;
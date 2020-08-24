# SP500-options-strategy

Quick and dirty program to see what the performance is of a portfolio consisting of a long position in the S&P500 and a long position in (far) OTM S&P500 put options. Just to see how effective the hedge is with different values of the OTM ratio, different times to maturities for the chosen options and different percentages of the portfolio allocated to the options. 

The portfolio is rebalanced each 3rd Friday of the month, as then new S&P500 options are listed. All options data is obtained from optionmetrics. For speed, the complete (daily) options file is cleaned to the subset of 3rd Friday prices. 

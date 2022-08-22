from src.download import download_data
from src.capm import Capm
from src.calculatefrontier import EfficientFrontier
from src.optimizer import Optimizer
import matplotlib.pyplot as plt
from src.plots import plotcolumns, efficientplot, frontierplot, weightbar
import pandas as pd
from tabulate import tabulate

import numpy as np

time_frame = 1
tickers = ' '.join(['TTM', 'AMZN'])
tickers = 'AAPL AMZN GLD'
print('...Downloading Data...\n')
market_data = download_data(tickers, time_frame=time_frame)
print('...Download Completed...\n')

fig1=plotcolumns(market_data)
plt.show()

eff_port = EfficientFrontier(market_data, 10000)
df_portfolio = eff_port.get_portfolio()

port_optim = Optimizer(df_portfolio)

max_sharpe_port = port_optim.max_return_portfolio()
min_vol_port = port_optim.minimum_risk_portfolio()

portfolio_table = pd.concat([min_vol_port, max_sharpe_port], ignore_index=True)

# CAPM
capm = Capm(market_data)
exp_ret = pd.DataFrame(capm.expected_return())
exp_ret['Return'] = exp_ret['Return'].apply(lambda x: x*100)
print('Expected return:\n',  tabulate(exp_ret, headers=['Company', 'Return'], tablefmt='pretty')) # fancy_grid

portfolio_table['Beta'] = [capm.get_beta(min_vol_port.iloc[:, 3:].values), capm.get_beta(max_sharpe_port.iloc[:, 3:].values)]
portfolio_table['Alpha'] = [capm.calculate_alpha(0.1, min_vol_port.iloc[:, 3:].values), capm.calculate_alpha(0.35, max_sharpe_port.iloc[:, 3:].values)]
portfolio_table['Returns'] = portfolio_table['Returns'].apply(lambda x: x*100)
portfolio_table['Volatility'] = portfolio_table['Volatility'].apply(lambda x: x*100)
portfolio_metrics_table = portfolio_table[['Returns', 'Volatility', 'Sharpe Ratio', 'Beta', 'Alpha']]
portfolio_weights_table = portfolio_table.drop(['Returns', 'Volatility', 'Sharpe Ratio', 'Beta', 'Alpha'], axis = 1)

fig2=efficientplot(df_portfolio)
plt.show()

fig3=frontierplot(df_portfolio,max_sharpe_port,min_vol_port)
plt.show()

#print(f'Min Risk :\n{min_vol_port}\nMax Ret :\n{max_sharpe_port}')
print('Metrics :\n')
print(tabulate(portfolio_metrics_table,  headers='keys', tablefmt='psql'))
print('Weights :\n')
print(tabulate(portfolio_weights_table,  headers='keys', tablefmt='psql'))

fig=weightbar(min_vol_port,max_sharpe_port)
plt.show()


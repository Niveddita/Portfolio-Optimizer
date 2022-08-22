import streamlit as st
from datetime import datetime
import plotly.express as px
from src.download import download_data
from src.capm import Capm
from src.calculatefrontier import EfficientFrontier
from src.optimizer import Optimizer
import matplotlib.pyplot as plt
from src.plots import plotcolumns, efficientplot, frontierplot, weightbar
import pandas as pd
from streamlit_option_menu import option_menu
import time
from pymongo import MongoClient

@st.experimental_singleton
def db_init():
    client = MongoClient('mongodb://mongo/')
    mydb = client.proj
    mycollection = mydb['Portfolio-Optimizer']
    mycollection.drop()
    mycollection.insert_one({'ticker': 'AMZN,TSLA', 'steps': 10000, 'start_date': '2013-01-01', 'end_date': str(datetime.today().strftime('%Y-%m-%d'))})
    #print('Done init')
    return client

#@st.experimental_memo(ttl=600)
def get_data(_client, find_string={}, disp_string={}):
    mydb = _client.proj
    mycollection = mydb['Portfolio-Optimizer']
    ticker_list = list(mycollection.find(find_string, disp_string))
    return ticker_list

def insert_data(client, value):
    mydb = client.proj
    mycollection = mydb['Portfolio-Optimizer']
    mycollection.insert_one(value)

mongo_client = db_init()

selected2 = option_menu( None, ["Home" ,"Results", "Help", "History"], 
    icons=['house', "bi bi-file-earmark-bar-graph-fill", 'info-lg', 'clock-history'], 
    menu_icon="cast",default_index=0, orientation="horizontal")
st.session_state['ticker_string'] = 'AMZN,TSLA'

if selected2 == 'Home':
    st.header("Finance Marvels Portfolio Optimizer")

    st.subheader("Welcome!!")
    st.image("https://cdnblog.etmoney.com/wp-content/uploads/2021/09/investing-at-market-high-1.jpg", use_column_width='auto')
    st.write("$\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ Compound\ interest\ is\ the\ eighth\ wonder\ of\ the\ world.$")
    st.write("$\ \ \ \ \ \ \  \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ He\ who\ understands\ it,\ earns\ it.$")
    st.write("$\ \ \ \ \ \ \ \  \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ He\ who\ doesn’t,\ pays\ it.$")

    col1, col2 = st.columns(2)

    done ,info = None, None

    ticker_data = get_data(mongo_client)[-1]
    
    with col1:
        st.session_state['start_date'] = st.date_input("Start Date",datetime.strptime(ticker_data['start_date'], '%Y-%m-%d').date())
        
    with col2:
        st.session_state['end_date'] = st.date_input("End Date", datetime.strptime(ticker_data['end_date'], '%Y-%m-%d').date()) # it defaults to current date

    form = st.form(key='my-form')
    
    tickers_string = form.text_input('Enter all stock tickers to be included in portfolio separated by commas \
                                    WITHOUT spaces, e.g. "MA,FB,V,AMZN,JPM,BA"', ticker_data['ticker']).upper()


    st.session_state['ticker_string'] = tickers_string
    
    #st.header("Where Family and Finance come first")
    if len(tickers_string)!=0:
        tickers = tickers_string.split(',')
        tickers = ' '.join(tickers)

    if (tickers_string != ''):
        st.session_state['ticker'] = tickers
    
    steps = form.selectbox('Enter the no. of steps to optimize?',('10000', '20000', '30000', '50000', '100000'))
    if (steps != ''):
        st.session_state['steps'] = steps

    t, s = tickers_string, steps
    submit = form.form_submit_button('Optimize')

    if submit:

        with st.spinner(text='In progress'):
            time.sleep(1)

            insert_data(mongo_client, {'ticker': tickers_string, 'steps': 10000, 'start_date': str(st.session_state['start_date']), 'end_date': str(st.session_state['end_date'])})
            done = st.success('Portfolio Optimised!', icon="✅")
            #print(*dir(a), sep = '\n')
            info = st.info('Click on Results tabs to view results', icon="ℹ️")
            #print(type(st.session_state['start_date']))
            b = st.balloons()
            
        time.sleep(2.5)
        done.empty()
        info.empty()
        b.empty()


market_data = download_data(st.session_state['ticker'], start=st.session_state.start_date, end=st.session_state.end_date)
fig1 = plotcolumns(market_data)


eff_port = EfficientFrontier(market_data, int(st.session_state['steps']))
df_portfolio = eff_port.get_portfolio()

port_optim = Optimizer(df_portfolio)


max_sharpe_port = port_optim.max_return_portfolio()
min_vol_port = port_optim.minimum_risk_portfolio()

portfolio_table = pd.concat([min_vol_port, max_sharpe_port], ignore_index=True)

# CAPM
capm = Capm(market_data)
exp_ret = pd.DataFrame(capm.expected_return())
exp_ret['Return'] = exp_ret['Return'].apply(lambda x: x*100)

portfolio_table['Beta'] = [capm.get_beta(min_vol_port.iloc[:, 3:].values), capm.get_beta(max_sharpe_port.iloc[:, 3:].values)]
portfolio_table['Alpha'] = [capm.calculate_alpha(0.1, min_vol_port.iloc[:, 3:].values), capm.calculate_alpha(0.35, max_sharpe_port.iloc[:, 3:].values)]
portfolio_table['Returns'] = portfolio_table['Returns'].apply(lambda x: x*100)
portfolio_table['Volatility'] = portfolio_table['Volatility'].apply(lambda x: x*100)
portfolio_table['Type'] = ['Minimum Risk Portfolio', 'Maximum Return Portfolio']
portfolio_metrics_table = portfolio_table[['Type', 'Returns', 'Volatility', 'Sharpe Ratio', 'Beta', 'Alpha']]
portfolio_weights_table = portfolio_table.drop(['Returns', 'Volatility', 'Sharpe Ratio', 'Beta', 'Alpha'], axis = 1)

portfolio_metrics_table.set_index(keys = 'Type', inplace=True)	
portfolio_weights_table.set_index(keys = 'Type', inplace=True)	
#st.dataframe(min_max_data)

#st.subheader('Frontier')
fig2=efficientplot(df_portfolio)
#st.pyplot(fig2)

#st.subheader('Efficient Frontier')
fig3 = frontierplot(df_portfolio,max_sharpe_port,min_vol_port)
#st.pyplot(fig3)

#st.subheader('Weight Bar')
fig4=weightbar(min_vol_port,max_sharpe_port)
#st.pyplot(fig4)
capm = Capm(market_data)
    
if selected2 == 'Results':

    selected3 = option_menu( None, ["Trend", "Analysis", "Frontier"], 
    icons=['bi bi-reception-4', "list-task", 'gear'],
    menu_icon="cast",default_index=0, orientation="horizontal")
    if selected3 == "Analysis":
        st.subheader('Optimized Portfolio')
        st.dataframe(portfolio_weights_table)
        st.subheader('Weight Bar')
        #fig4=weightbar(min_vol_port,max_sharpe_port)
        st.pyplot(fig4)

        st.subheader('Metrics')
        st.dataframe(portfolio_metrics_table)
        with st.expander("See explanation"):
            st.write("""
                The Sharpe ratio is the most common ratio for comparing reward (return on investment) to risk (standard deviation). This allows us to adjust the returns on an investment by the amount of risk that was taken in order to achieve it. The Sharpe ratio also provides a useful metric to compare investments. The calculations are as follows:
            """)
            st.latex(r'''
                    Sharpe Ratio = \left(\frac{\overline{R} - R_f}{σ}\right)
                    ''')
            st.write('''
                    The Sortino ratio is very similar to the Sharpe ratio, the only difference being that where the Sharpe ratio uses all the observations for calculating the standard deviation the Sortino ratio only considers the harmful variance. 
                    ''')
            st.latex(r'''
                    Sortino Ratio = \left(\frac{\overline{R} - R_f}{σ^-}\right)
                    ''')
            st.write('''
                    Alpha (α) is a term used in investing to describe an investment strategy's ability to beat the market, or its "edge". Alpha refers to excess returns earned on an investment above the benchmark return where beta (the Greek letter β) measures the broad market's overall volatility or risk, known as systematic market risk.
                    ''')
        
    elif selected3 =="Frontier":
        st.subheader('Frontier')
        st.pyplot(fig2)
        st.subheader('Efficient Frontier')
        #fig3 = frontierplot(df_portfolio,max_sharpe_port,min_vol_port)
        st.pyplot(fig3)
        st.subheader('Expected Return')
        st.dataframe(exp_ret)
        with st.expander("See explanation"):
            st.write('''
                    The efficient frontier comprises investment portfolios that offer the highest expected return for a specific level of risk. 
                    The blue marker represents the minimum risk portfolio for risk averse investors. The red marker represents the portfolio with maximum returns.
                    ''')
    
    elif selected3 == "Trend":
        st.subheader('Market Trend')
        st.pyplot(fig1)
        with st.expander("See explanation"):
            st.write("""
                The chart above shows the normalized stock prices for comparison
            """)

elif selected2== "Help":
    st.subheader("What we do ?")
    st.write("Construct portfolios to optimize or maximize expected return based on a given level of market risk, emphasizing that risk is an inherent part of higher reward")
    st.subheader("What is Portfolio Optimization?")
    st.write("Portfolio optimization is the process of selecting the best portfolio (asset distribution), out of the set of all portfolios being considered, according to some objective.")
    st.subheader("What is MPT?")
    st.write("The modern portfolio theory (MPT) is a practical method for selecting investments in order to maximize their overall returns within an acceptable level of risk.")
    st.subheader("What is efficient frontier?")
    st.write("The efficient frontier is a cornerstone of modern portfolio theory. It is the line that indicates the combination of investments that will provide the highest level of return for the lowest level of risk.")
    st.subheader("Guide")
    st.markdown(
        """
        - Select the start date and end date accordingly
        - Type in your stock tickers. Amazon and Tesla are used as default tickers. If you don't want Amazon and Tesla, no worries, you can delete and type your stock tickers.
        - Enter the number of portfolios for optimization. 10000 is used as default.
        - To view the results navigate to the Results tab.
        - To see the market trend click on trend
        - To see the efficient frontier and expected return, click Portfolio
        - To see your optimized portfolio for minimum risk and maximum return, click Analysis
        - Happy Investment !!!.
        """
    )

elif selected2 == "History":
    display_data = get_data(mongo_client,{}, {'_id':0, 'steps':0})[-5:]
    #print(display_data)
    st.subheader('Tickers')
    for i, dat in enumerate(display_data):
        st.write(f'{i+1} - {dat["ticker"]}')
    
#except:
    #st.write('Enter correct stock tickers to be included in portfolio separated\
    #by commas WITHOUT spaces, e.g. "MA,FB,V,AMZN,JPM,BA"and hit Enter.')

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

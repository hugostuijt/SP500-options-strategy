import pandas as pd
import math



def selectOption(options, spxVal, maturity):
    # filter options on our ideal maturity
    options = options[options['days'] > maturity]
    # Next, find the strike price which is closest to what we want
    strikes = options['strike']
    idx = strikes.sub(spxVal / 2).abs().idxmin()
    strike = strikes[idx]
    # filter for best strike and select the cheapest (thus shortest available maturity)
    bestOptions = options[options['strike'] == strike].sort_values('offer')
    return bestOptions.iloc[0]


tradingDates = pd.read_csv("tradingDates.csv", header=None)[0]
spx = pd.read_csv("SPX.csv")

# import data, change date format
data = pd.read_csv("cleaned_data.csv")
data = data.rename(columns={'exdate': 'maturity', 'strike_price': 'strike', 'best_bid': 'bid', 'best_offer': 'offer'})
data['date'] = pd.to_datetime(data['date'])
data['maturity'] = pd.to_datetime(data['maturity'])

# first clean the S&P500 data
spx = spx.set_index('Date', drop=True)
spx.index = pd.to_datetime(spx.index)
spx = (spx['Open'] + spx['Close']) / 2

tradingDates = pd.to_datetime(tradingDates)
# filter S&P500 data
spx = spx[spx.index.isin(tradingDates)]
spxRet = spx.pct_change()

# since the portfolio is not dollar neutral, we do need some kind of starting capital to check if we can afford the puts
startingCapital = 10000
preferredMaturity = 60  # 65 trading days, 3 months
putAllocation = .005
OTMratio = .5

# dataframe with the output
portfolioValue = pd.DataFrame(index=tradingDates, columns=['S&P500', 'puts', 'total'])
tradingBook = pd.DataFrame(
    columns=['trading date', 'buy/sell', 'maturity', 'days', 'strike', 'bid', 'offer', 'position', 'cashflow'])

# Start with the first options trade
date = tradingDates[0]
bestOption = selectOption(data[data['date'] == date], spx[date], preferredMaturity)
# Check how many we can buy
budget = startingCapital * putAllocation
position = math.floor(budget / bestOption['bid'])
cf = position * bestOption['bid']
# add new position to the trading book
tradingBook.loc[0] = [date, 'b', bestOption['maturity'], bestOption['days'], bestOption['strike'],
                      bestOption['bid'], bestOption['offer'], position, cf]
# Set the current option in the portfolio
currentOption = bestOption[['maturity', 'strike']]
currentOption['position'] = position
# set the initial portfolio value
portfolioValue.loc[date] = [startingCapital - cf, cf, startingCapital]

# loop over each trading date, skip first
for i in range(1, len(tradingDates)):
    # for date in tradingDates[1:]:
    date = tradingDates[i]
    ret = spxRet[date]

    # retrieve the new options and find the new best option
    allOptions = data[data['date'] == date]
    bestOption = selectOption(allOptions, spx[date], preferredMaturity)

    # retrieve the new prices of the puts in our portfolio
    updatedPrices = allOptions[(allOptions['strike'] == currentOption['strike']) & (
            allOptions['maturity'] == currentOption['maturity'])]
    updatedPrices = updatedPrices.iloc[0]  # updatedPrices cannot be more than 1 option
    prevPosition = currentOption['position']
    cash = prevPosition * updatedPrices['bid']  # this is the cash we receive from selling the position

    # Then update our current portfolioValue
    newValue = portfolioValue.loc[tradingDates[i - 1], 'S&P500'] * (1 + ret)
    portfolioValue.loc[date] = [newValue, cash, newValue + cash]

    # If the current option is not the same as the new best option, perform the trade
    if not currentOption[['maturity', 'strike']].equals(bestOption[['maturity', 'strike']]):
        # first sell the current option, thus we need the current prices
        tradingBook.loc[len(tradingBook)] = [date, 's', updatedPrices['maturity'], updatedPrices['days'],
                                             updatedPrices['strike'], updatedPrices['bid'],
                                             updatedPrices['offer'], prevPosition, cash]

        # now calculate the new portfolio value and the new option allocation
        value = portfolioValue.loc[date, 'S&P500'] + cash
        budget = value * putAllocation
        position = math.floor(budget / bestOption['offer'])
        cf = position * bestOption['offer']
        # cf is now the amount of cash needed for the new option position, so need to buy/sell some S&P500
        portfolioValue.loc[date, 'S&P500'] -= (cf - cash)
        # now buy the best new option
        tradingBook.loc[len(tradingBook)] = [date, 'b', bestOption['maturity'], bestOption['days'],
                                             bestOption['strike'], bestOption['bid'],
                                             bestOption['offer'], position, cf]
        # update the portfolio value, we need to buy/sell some S&P500 for the put trade
        portfolioValue.loc[date, 'S&P500'] -= (cf - cash)
        portfolioValue.loc[date, ['puts', 'total']] = [cf, portfolioValue.loc[date, 'S&P500'] + cf]

        currentOption = bestOption[['maturity', 'strike']]
        currentOption['position'] = position

# set buy cashflow negative
tradingBook.loc[tradingBook['buy/sell'] == 'b', 'cashflow'] *= -1
portfolioValue['return'] = portfolioValue['total'].pct_change()
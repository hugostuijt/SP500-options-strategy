import pandas as pd
import numpy as np

def selectOption(options, spxVal, maturity, OTMratio):
    # filter options on our ideal maturity
    options = options[options['days'] > maturity]
    # Next, find the strike price which is closest to what we want
    strikes = options['strike']
    idx = strikes.sub(spxVal * OTMratio).abs().idxmin()
    strike = strikes[idx]
    # filter for best strike and select the cheapest (thus shortest available maturity)
    bestOptions = options[options['strike'] == strike].sort_values('offer')
    return bestOptions.iloc[0]


def simulateStrategy(data, tradingDates, spx, spxRet, putAllocation, minMaturity, OTMratio):
    # dataframe with the output
    portfolioValue = pd.DataFrame(index=tradingDates, columns=['S&P500', 'puts', 'total'])
    tradingBook = pd.DataFrame(
        columns=['trading date', 'buy/sell', 'maturity', 'days', 'strike', 'bid', 'offer', 'position', 'option return'])

    # Start with the first options trade
    date = tradingDates[0]
    bestOption = selectOption(data[data['date'] == date], spx[date], minMaturity, OTMratio)
    position = putAllocation

    # add new position to the trading book
    tradingBook.loc[0] = [date, 'b', bestOption['maturity'], bestOption['days'], bestOption['strike'],
                          bestOption['bid'], bestOption['offer'], position, np.nan]
    # Set the current option in the portfolio
    currentOption = bestOption[['maturity', 'strike', 'offer']]
    currentOption['position'] = position
    # set the initial portfolio value
    portfolioValue.loc[date] = [1 - position, position, 1]

    # loop over each trading date, skip first
    for i in range(1, len(tradingDates)):
        # for date in tradingDates[1:]:
        date = tradingDates[i]
        ret = spxRet[date]

        # retrieve the new options and find the new best option
        allOptions = data[data['date'] == date]
        bestOption = selectOption(allOptions, spx[date], minMaturity, OTMratio)

        # retrieve the new prices of the puts in our portfolio
        updatedPrices = allOptions[(allOptions['strike'] == currentOption['strike']) & (
                allOptions['maturity'] == currentOption['maturity'])]
        updatedPrices = updatedPrices.iloc[0]  # updatedPrices cannot be more than 1 option
        prevPosition = currentOption['position']
        prevPrice = currentOption['offer']  # price for which option was bought
        newPrice = updatedPrices['bid']  # price received when selling the option
        optRet = (newPrice - prevPrice) / prevPrice

        # Then update our current portfolioValue
        newValue = portfolioValue.loc[tradingDates[i - 1], 'S&P500'] * (1 + ret)
        newOptValue = prevPosition * (1 + optRet)
        newTotal = newValue + newOptValue
        portfolioValue.loc[date] = [newValue, np.nan, np.nan]

        # If the current option is not the same as the new best option, perform the trade
        if not currentOption[['maturity', 'strike']].equals(bestOption[['maturity', 'strike']]):
            # first sell the current option, thus we need the current prices
            tradingBook.loc[len(tradingBook)] = [date, 's', updatedPrices['maturity'], updatedPrices['days'],
                                                 updatedPrices['strike'], updatedPrices['bid'],
                                                 updatedPrices['offer'], prevPosition, optRet]

            position = newTotal * putAllocation

            # now buy the best new option
            tradingBook.loc[len(tradingBook)] = [date, 'b', bestOption['maturity'], bestOption['days'],
                                                 bestOption['strike'], bestOption['bid'],
                                                 bestOption['offer'], position, np.nan]
            # update the portfolio value, we need to buy/sell some S&P500 for the put trade
            portfolioValue.loc[date, 'S&P500'] += (newOptValue - position)
            portfolioValue.loc[date, ['puts', 'total']] = [position, portfolioValue.loc[date, 'S&P500'] + position]

            currentOption = bestOption[['maturity', 'strike', 'offer']]
            currentOption['position'] = position

        # current option is already in the portfolio, update the position
        else:
            # the new position which is needed
            position = newTotal * putAllocation
            extra = position - newOptValue  # additional puts which need to be bought/sold
            # buy extra options
            if extra > 0:
                tradingBook.loc[len(tradingBook)] = [date, 'b', bestOption['maturity'], bestOption['days'],
                                                     bestOption['strike'], bestOption['bid'],
                                                     bestOption['offer'], extra, np.nan]
                # update portfolio value
                portfolioValue.loc[date, 'S&P500'] -= extra
                portfolioValue.loc[date, ['puts', 'total']] = [position, portfolioValue.loc[date, 'S&P500'] + position]
            # sell part of the option portfolio, proceeds go into S&P portfolio
            else:
                tradingBook.loc[len(tradingBook)] = [date, 's', bestOption['maturity'], bestOption['days'],
                                                     bestOption['strike'], bestOption['bid'],
                                                     bestOption['offer'], -extra, np.nan]
                # update portfolio value
                portfolioValue.loc[date, 'S&P500'] -= extra
                portfolioValue.loc[date, ['puts', 'total']] = [position, portfolioValue.loc[date, 'S&P500'] + position]
            # update current options (new position + average price)
            currentOption = bestOption[['maturity', 'strike']]
            # take the weighted average offer price (only for calculating the return after selling the whole position)
            currentOption['offer'] = prevPosition * prevPrice / position - extra * bestOption['offer'] / position
            currentOption['position'] = position

    portfolioValue['temp'] = portfolioValue['puts'] / (portfolioValue['S&P500'] + portfolioValue['puts'])
    portfolioValue = portfolioValue.astype(float)
    return [portfolioValue, tradingBook]




# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    data_fetcher.py                                    :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Time Money Code <->                        +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2025/06/05 18:42:32 by Time Money        #+#    #+#              #
#    Updated: 2025/06/05 18:42:32 by Time Money       ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


import requests


def _fetch_price_qq(symbol: str):
    """腾讯行情接口 —— A 股 .SS/.SZ 后缀自动映射，国内访问稳定不走 Yahoo 限流。

    返回昨收折算的现价（字段 4 为实时价），失败返回 None。
    """
    code = symbol.replace(".SS", "").replace(".SZ", "")
    prefix = "sh" if symbol.endswith(".SS") else "sz"
    try:
        r = requests.get(
            f"https://qt.gtimg.cn/q={prefix}{code}", timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        fields = r.text.split('"')[1].split("~")
        price = float(fields[3])
        return price if price > 0 else None
    except Exception:
        return None


def fetch_current_prices(assets):
    """Fetch current prices: 腾讯源优先（A 股），yfinance 兜底（美股/其他）。"""
    prices = {}
    for asset in assets:
        price = _fetch_price_qq(asset.ticker) if asset.ticker.endswith((".SS", ".SZ")) else None
        if price is None:
            try:
                import yfinance as yf
                ticker = yf.Ticker(asset.ticker)
                price = ticker.history(period="1d").iloc[-1]["Close"]
            except Exception as e:
                print(f"Error fetching price for {asset.ticker}: {e}")
                price = None
        prices[asset.ticker] = price
    return prices


def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another using exchangerate.host API."""
    if from_currency == to_currency:
        return amount
    pair = f"{from_currency}_{to_currency}"
    if pair in CURRENCY_CACHE:
        rate = CURRENCY_CACHE[pair]
    else:
        try:
            url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}"
            response = requests.get(url)
            data = response.json()
            rate = data["result"]
            CURRENCY_CACHE[pair] = rate
        except Exception as e:
            print(f"Error converting currency {from_currency} to {to_currency}: {e}")
            return None
    return amount * rate

# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    portfolio.py                                       :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Time Money Code <->                        +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2025/06/05 18:41:20 by Time Money        #+#    #+#              #
#    Updated: 2025/06/05 18:41:20 by Time Money       ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import csv


class Asset:
    """Represents a single asset in the portfolio."""

    def __init__(self, ticker, shares, currency, target_allocation):
        self.ticker = ticker
        self.shares = shares
        self.currency = currency
        self.target_allocation = target_allocation


class Portfolio:
    """Represents the entire portfolio."""

    def __init__(self):
        self.assets = []

    def add_asset(self, asset):
        self.assets.append(asset)

    def get_assets(self):
        return self.assets

    def remove_asset(self, ticker):
        """Remove an asset from the portfolio by ticker symbol."""
        self.assets = [asset for asset in self.assets if asset.ticker != ticker]

    def get_asset(self, ticker):
        """Retrieve an asset by ticker symbol."""
        for asset in self.assets:
            if asset.ticker == ticker:
                return asset
        return None

    def total_value(self, prices):
        """Return total portfolio value given a price dict."""
        return sum(prices.get(a.ticker, 0) * a.shares for a in self.assets)

    def by_group(self):
        """Return a dict of group -> list of assets."""
        from collections import defaultdict

        groups = defaultdict(list)
        for asset in self.assets:
            group = getattr(asset, "group", asset.ticker) or asset.ticker
            groups[group].append(asset)
        return groups


def load_portfolio_from_csv(filepath):
    """
    Load assets from a CSV file with columns:
    Symbol:WKN:Shares:Group:Adjust:Target[:Currency]
    支持 # 注释行；自动识别 :, ;, , 分隔符；列名大小写不敏感。
    Returns a Portfolio object.
    """
    import io

    portfolio = Portfolio()
    with open(filepath, newline="", encoding="utf-8") as csvfile:
        sample = "".join(
            ln for ln in csvfile if not ln.lstrip().startswith("#")
        )
    if sample.count(":") > max(sample.count(";"), sample.count(",")):
        delimiter = ":"
    elif sample.count(";") > sample.count(","):
        delimiter = ";"
    else:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(sample), delimiter=delimiter)
    normalized_cols = {col.lower().strip(): col for col in reader.fieldnames}
    required = ["symbol", "shares", "target"]
    for req in required:
        if req not in normalized_cols:
            raise KeyError(
                f"Missing required column '{req}' in CSV. Found columns: {list(reader.fieldnames)}"
            )
    for i, row in enumerate(reader, start=2):
        try:
            ticker = row[normalized_cols["symbol"]].strip()
            shares = float(row[normalized_cols["shares"]])
            currency = (
                row.get(normalized_cols.get("currency", ""), "USD").strip().upper()
                if normalized_cols.get("currency")
                else "USD"
            )
            target_allocation = (
                float(row[normalized_cols["target"]])
                if row[normalized_cols["target"]]
                else 0.0
            )
            asset = Asset(ticker, shares, currency, target_allocation)
            asset.group = (
                row.get(normalized_cols.get("group", ""), "").strip()
                if normalized_cols.get("group")
                else ""
            )
            asset.adjust = (
                int(row.get(normalized_cols.get("adjust", ""), 1))
                if normalized_cols.get("adjust")
                and row.get(normalized_cols.get("adjust", ""))
                else 1
            )
            asset.wkn = (
                row.get(normalized_cols.get("wkn", ""), "").strip()
                if normalized_cols.get("wkn")
                else ""
            )
            portfolio.add_asset(asset)
        except Exception as e:
            print(f"[Warning] Skipping row {i}: {e}")
    return portfolio

from sec_edgar_downloader import Downloader

# Company + email form the User-Agent header the
# SEC requires for programmatic access.
dl = Downloader("NEU-DAMG7245-Team1",
                "cherla.p@northeastern.edu",
                "data/raw")

# Two fiscal periods for one company
dl.get("10-K", "AAPL", limit=2, download_details=True)
dl.get("10-Q", "AAPL", limit=2, download_details=True,
       after="2024-01-01")
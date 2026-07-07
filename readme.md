# Live Sports Arbitrage Bet Finder

A tool that scans live tennis odds across two Italian betting websites (SNAI and Eurobet) to detect and act on arbitrage opportunities — situations where the combined odds on both outcomes of a match guarantee a profit regardless of the result.

## Logic

The core loop, run repeatedly while the app is active, follows these steps:

1. **Find all matches and wagers on both websites**
   Each site is scraped independently to build a list of currently live matches along with the odds offered for each outcome (player 1 / player 2).

2. **Find common matches**
   The two lists are compared to identify matches that appear on both sites, so that odds can be compared head-to-head for the same event.

3. **Scan for arbitrage opportunities**
   For each common match, the implied probabilities from both sites' odds are combined. If the sum of implied probabilities is less than 1, an arbitrage opportunity exists — meaning a profit is guaranteed no matter which player wins, provided stakes are split correctly between the two sites.

4. **If an arbitrage opportunity is found:**
   - **Select wager and add it to schedina** — the relevant outcome is selected on each site's interface, adding it to the bet slip ("schedina").
   - **Compute and enter stake** — the stake for each side is calculated so that the payout is balanced regardless of outcome, then entered into the site's stake input field.
   - **Submit bid and clear schedina** _(not yet implemented)_ — this step would confirm/place the bet on both sites and reset the bet slip so the next opportunity can be evaluated. Currently a placeholder in the code.

## Notes

- The final step (submitting the bid and clearing the schedina) is intentionally left unimplemented for now.

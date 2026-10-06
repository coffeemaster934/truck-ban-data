name: Auto Update Truck Bans

on:
  schedule:
    - cron: '0 6 * * 1' # Spustí se každé pondělí v 6:00 ráno
  workflow_dispatch: # Možnost spustit ručně tlačítkem v rozhraní GitHubu

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Run update script
        run: python update_bans.py

      - name: Commit and push if changed
        run: |
          git config --global user.name 'GitHub Actions Bot'
          git config --global user.email 'actions@github.com'
          git add bans.json
          git diff --quiet && git diff --staged --quiet || (git commit -m "Automatická aktualizace dat zákazů [skip ci]" && git push)

# 💬 Talk Time Cards

A pass-and-play conversation card game for up to six players. Draw a card, answer it out loud, and dig deeper with the follow-up question. There is no right or wrong answer, just good talking.

**Play it:** open `index.html` in any browser (phone, tablet or computer), or use GitHub Pages once it is enabled for this repo. It works offline and can be added to a home screen.

## How to play
1. Choose 2 to 6 players, give each an animal and (optionally) a name.
2. Pick the deck(s) and topics you want:
   - 🧸 **Little Kids** (ages 4 to 8) and 🌟 **Big Kids & Grown-ups** (ages 9 and up), 70 cards each
   - 🏫 School & Learning, 🏠 Home & Family, 💛 Feelings, 🚀 Dreams & Future, 🎉 Fun & Silly
3. Tap the deck (or a topic) to draw a card. The card is read aloud if "Read cards aloud" is on.
4. The player whose turn it is answers. Tap **Dig deeper** for a follow-up question, or **Different card** to swap.
5. Tap **Done** to pass the turn.

Options:
- **Everyone answers**: each card goes around the whole table, starting with the current player.
- **Talking stars**: speakers earn ⭐ for sharing, and listeners can award a ⭐ for a great follow-up question. No winner, just fun.

## Files
- `index.html`: the whole game (HTML, CSS, JS). All card wording is original.
- `manifest.webmanifest`, `sw.js`, `icon-*.png`: install and offline support. Bump `CACHE` in `sw.js` after changes.
- `tests/run.py`: headless-browser tests (card content, setup, full games for 2 to 6 players, layout on phone / tablet / desktop). Run with `python3 tests/run.py`.
- `tests/shots.py`: screenshots for a visual check.

## Adding cards
Edit the `T` object in `index.html`. Each card is `"Question? | Follow-up question?"`, in a deck (`little` or `big`) and a topic. The tests check punctuation, length and duplicates.

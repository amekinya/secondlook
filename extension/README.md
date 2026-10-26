# SecondLook browser extension

Stamps warning labels on second-hand baby gear listings as you browse: banned products, recalls, and expired car seats.

## Install (Chrome, Edge, Brave)

1. Download this repository (Code → Download ZIP) and unzip it.
2. Open `chrome://extensions` and turn on **Developer mode** (top right).
3. Click **Load unpacked** and choose the `extension` folder.
4. Click the SecondLook icon, enter your SecondLook server address (for example `https://secondlook-xllm.onrender.com`), and press **Scan this page** on any listing page.

## How it works

- `adapters.js` finds listing cards: site-specific selectors for common marketplaces, plus a generic finder (an image next to a price) for everything else.
- `sl-overlay.js` (same file the web app uses) sends each listing's photo and text to the SecondLook server, which runs Nemotron 3.5 Super VL on Nebius Token Factory in parallel and streams back one result per listing.
- Nothing is stored. The extension only runs when you press **Scan this page**.

The extension doesn't read pages in the background and has no access to your marketplace account.

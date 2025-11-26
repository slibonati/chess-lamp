# Chess-Themed Color Suggestions

The default red/green colors feel like traffic lights. Use **themes** to easily switch between chess-themed color schemes!

## Quick Start: Use Themes

Simply set the `theme` in your `config.json`:

```json
{
  "theme": "classic"
}
```

## Available Themes

### `classic` (Recommended)
**Warm White & Midnight Blue** - Like classic chess pieces
- Your turn: Warm white/cream (#FFF8DC) at 30% brightness
- Opponent's turn: Midnight blue (#191970) at 20% brightness

### `pure`
**Pure White & Dark Gray** - Clean and modern
- Your turn: Pure white (#FFFFFF) at 70% brightness
- Opponent's turn: Dark gray (#2F2F2F) at 30% brightness

### `ivory`
**Ivory & Charcoal** - Elegant and soft
- Your turn: Cream/beige (#F5E6D3) at 65% brightness
- Opponent's turn: Charcoal (#36454F) at 35% brightness

### `royal`
**Royal Gold & Deep Purple** - Luxurious and regal
- Your turn: Gold (#FFD700) at 60% brightness
- Opponent's turn: Indigo/deep purple (#4B0082) at 40% brightness

### `ocean`
**Ocean Blue** - Calm and serene
- Your turn: Sky blue (#87CEEB) at 65% brightness
- Opponent's turn: Navy blue (#000080) at 35% brightness

### `amber`
**Amber & Teal** - Warm and cool contrast
- Your turn: Amber/gold (#FFBF00) at 60% brightness
- Opponent's turn: Teal (#008080) at 40% brightness

### `subtle`
**Subtle White & Slate** - Professional and understated
- Your turn: Ghost white (#F8F8FF) at 70% brightness
- Opponent's turn: Slate gray (#708090) at 30% brightness

### `warm`
**Warm Yellow & Deep Blue** - Cozy and inviting
- Your turn: Moccasin/warm yellow (#FFE4B5) at 60% brightness
- Opponent's turn: Dark blue (#00008B) at 40% brightness

### `traffic`
**Traffic Light** - Classic red/green (original behavior)
- Your turn: Green (#00FF00) at 40% brightness
- Opponent's turn: Red (#FF0000) at 40% brightness

## How to Apply a Theme

1. Edit your `config.json` file in the chess-lamp directory
2. Set the `theme` field:
   ```json
   {
     "theme": "classic"
   }
   ```
3. Rebuild and restart the container:
   ```bash
   cd /home/slibonat/github/chess-lamp
   docker compose down
   docker compose up -d --build
   ```

## Customizing a Theme

You can use a theme as a base and override specific colors:

```json
{
  "theme": "classic",
  "my_turn_brightness": 25,
  "opponent_turn_brightness": 15
}
```

## Advanced: Custom Colors (No Theme)

If you want completely custom colors without using a theme:

```json
{
  "my_turn_color": "#FFFFFF",
  "opponent_turn_color": "#000000",
  "my_turn_brightness": 50,
  "opponent_turn_brightness": 30
}
```

## Gradual Dimming

Themes now support gradual dimming! When the color changes, it starts bright and slowly dims to the target brightness:

```json
{
  "theme": "classic",
  "gradual_dim_enabled": true,
  "gradual_dim_duration": 1.5
}
```

- `gradual_dim_enabled`: Enable/disable gradual dimming (default: true)
- `gradual_dim_duration`: How long the dim takes in seconds (default: 1.5)

## See Also

For more details on themes, see `THEMES.md`.


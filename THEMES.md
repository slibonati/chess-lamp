# Color Themes

Choose a theme to apply a complete color scheme with one setting! Themes provide coordinated colors for your turn, opponent's turn, and brightness levels.

## Available Themes

### `classic` (Default)
**Warm White & Midnight Blue** - Like classic chess pieces
- Your turn: Warm white/cream (#FFF8DC) at 60% brightness
- Opponent's turn: Midnight blue (#191970) at 40% brightness

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

## Usage

### Simple: Just set the theme
```json
{
  "theme": "classic"
}
```

### Advanced: Override theme colors
You can use a theme as a base and override specific colors:
```json
{
  "theme": "royal",
  "my_turn_brightness": 80
}
```

### Custom: No theme, set colors individually
```json
{
  "my_turn_color": "#FFFFFF",
  "opponent_turn_color": "#000000",
  "my_turn_brightness": 70,
  "opponent_turn_brightness": 30
}
```

## Changing Themes

1. Edit `config.json` and set the `theme` field
2. Restart the container:
   ```bash
   cd /home/slibonat/github/chess-lamp
   docker compose restart
   ```

## Priority

1. **Individual color settings** (highest priority) - if set, these override theme
2. **Theme settings** - provides defaults if individual settings not specified
3. **Hardcoded defaults** - fallback if neither theme nor individual settings provided


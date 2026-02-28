import re
import random
import requests
import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import pytz

load_dotenv()  # Load .env into environment variables

API_KEY = os.getenv("RANDORG_API_KEY")
API_URL = ""#"https://api.random.org/json-rpc/4/invoke"
DISCORD_TOKEN = os.getenv("DISCORD_API_KEY")
PST = pytz.timezone('America/Los_Angeles')

def true_rand():
    payload = {
        "jsonrpc": "2.0",
        "method": "generateDecimalFractions",
        "params": {
            "apiKey": API_KEY,
            "n": 1,
            "decimalPlaces": 14,
            "replacement": True
        },
        "id": 1
    }

    response = requests.post(API_URL, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"RANDOM.ORG API error: {data['error']}")

    return data["result"]["random"]["data"][0]


class DylanGPT(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = DylanGPT()

def parse_dice_string(dice_str: str):
    """
    Parses A(d/D)B[kX][tY][+N|-N...]!C

    Examples:
      3d6
      3d6!attack roll
      5d10k8
      8d6t5!fireball
      10d10k7t8+3-1!big hit
      1d4+10-2!roll with disadvantage
    """
    # A = number of dice
    # B = sides
    # kX = keep dice >= X (others are crossed out)
    # tY = target number for successes (>= Y)
    # +N / -N = integer modifiers applied to the final total
    # !C = optional description

    pattern = r"""
        ^\s*
        (\d+)[dD](\d+)          # 1: num_dice, 2: sides
        (?:[kK](\d+))?          # 3: optional keep_threshold
        (?:[tT](\d+))?          # 4: optional target_threshold
        (                       # 5: modifier blob, e.g. +10-2+3
            (?:\s*[+-]\s*\d+)*
        )
        \s*
        (?:!(.{0,256}))?        # 6: optional description
        \s*$
    """

    match = re.match(pattern, dice_str, re.VERBOSE)

    if not match:
        return None

    num_dice = int(match.group(1))
    sides = int(match.group(2))

    keep_threshold = int(match.group(3)) if match.group(3) is not None else None
    target_threshold = int(match.group(4)) if match.group(4) is not None else None

    modifiers_raw = match.group(5) or ""
    description = match.group(6) or ""

    # Parse modifiers like "+10 -2 +3" into signed ints [10, -2, 3]
    modifiers: list[int] = []
    if modifiers_raw.strip():
        for m in re.finditer(r"([+-])\s*(\d+)", modifiers_raw):
            sign, num = m.groups()
            value = int(num)
            modifiers.append(value if sign == "+" else -value)

    return num_dice, sides, keep_threshold, target_threshold, modifiers, description

@bot.tree.command(name="roll", description="Roll dice in AdB[kX][tY][+N|-N]!C format")
@app_commands.describe(dice="Format: A(d/D)B[kX][tY][+N|-N]!C (example: 3d6k3t5+2-1!attack)")
async def roll(interaction: discord.Interaction, dice: str):
    print(f"[{interaction.created_at.astimezone(PST).strftime("%Y-%m-%d %H:%M:%S")}] {interaction.user}: /roll {dice}")
    if len(dice) > 256:
        await interaction.response.send_message(
            "Input too long (max 256 chars).",
            ephemeral=True
        )
        return

    parsed = parse_dice_string(dice)

    if not parsed:
        await interaction.response.send_message(
            "Invalid format. Use A(d/D)B[kX][tY][+N|-N]!C (example: 2d20k10t15+3!initiative)",
            ephemeral=True
        )
        return

    num_dice, sides, keep_threshold, target_threshold, modifiers, description = parsed

    if num_dice <= 0 or sides <= 0:
        await interaction.response.send_message(
            "Dice count and sides must be positive integers.",
            ephemeral=True
        )
        return
    num_dice = 100 if num_dice > 100 else num_dice
    sides = 2**31-1 if sides > 2**31-1 else sides

    rolls: list[int] = []

    for i in range(num_dice):
        if i == 0:
            # First roll uses true randomness
            try:
                r = true_rand()
            except Exception as e:
                print(f"\t[{interaction.user}:/roll] RANDOM.ORG failed: {e}, defaulting to normal rolls...")
                r = random.random()
        else:
            r = random.random()

        roll_value = int(r * sides) + 1
        rolls.append(roll_value)

    # Apply keep (kX): drop any value < keep_threshold from the sum
    if keep_threshold is not None:
        kept_rolls = [v for v in rolls if v >= keep_threshold]
        formatted_rolls = [
            f"~~{v}~~" if v < keep_threshold else str(v)
            for v in rolls
        ]
    else:
        kept_rolls = rolls[:]
        formatted_rolls = [str(v) for v in rolls]

    base_total = sum(kept_rolls)

    # Apply target (tY): count successes among kept dice
    successes = None
    if target_threshold is not None:
        successes = sum(1 for v in kept_rolls if v >= target_threshold)

    # Modifiers
    modifier_total = sum(modifiers) if modifiers else 0
    final_total = base_total + modifier_total

    # Build header text with notation (including modifiers)
    notation_parts = [f"{num_dice}d{sides}"]
    if keep_threshold is not None:
        notation_parts.append(f"k{keep_threshold}")
    if target_threshold is not None:
        notation_parts.append(f"t{target_threshold}")
    if modifiers:
        for m in modifiers:
            notation_parts.append(f"{'+' if m >= 0 else ''}{m}")

    notation = "".join(notation_parts)

    desc_text = f"*{description}*" if description else ""

    # Build response lines
    lines: list[str] = []
    lines.append(f"`{notation}`: {desc_text} 🎲")
    lines.append(f"**[{', '.join(formatted_rolls)}]**")

    # Modifiers, if any
    if modifiers:
        lines.append(f"= {base_total}{modifier_total:+d}")

    # Final total (always shown)
    lines.append(f"= **{final_total}**")

    # Successes
    if successes is not None:
        lines.append(f"({successes} successes)")

    await interaction.response.send_message(" ".join(lines))

bot.run(DISCORD_TOKEN)
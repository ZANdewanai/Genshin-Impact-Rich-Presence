# Collated Game Data

This folder contains `.csv` (comma-seperated value) files. Each line of text is a single record of a game element (e.g. location/domain/character/...), and their individual attributes are separated by columns.

All the `.csv` files are hot-reloaded. That is, you don't need to stop and restart the program to see effected changes. You can modify these while the program is running.

### Search phrase

⚠️ **SUPER IMPORTANT**: Refer to [the image capture coordinate configuration documentation](../configure%20coordinates.md) to know the exact in-game text this program searches to detect each type of game element.

The first attribute of all the records is the most important: the **search phrase**. This tells the program what in-game text to look for when detecting a particular character/location/boss/domain/etc...

**Only use lowercase alphabets for the search phrase**. To increase the chances of successful detection, if a location/name/text has punctuation in it, you have to provide multiple entries where the search phrases have its...
- ...punctuation removed --- **Bayt Al-muazzam** becomes `bayt almuazzam`
- ...punctuation replaced with a space --- **Bayt Al-muazzam** becomes `bayt al muazzam`

🟠 To reduce OCR (image-to-text) errors, keep the `ALLOWLIST` as small as possible (e.g. quotes `"` are not needed. `"They" Too Were Once Flawless` can be searched using the phrase `too were once flawless`).

The search phrases do not need to match the entire text, it just has to be unique enough to identify the location/character/domain.

### Image assets

Image asset names are based on the filenames of the images in [Image Assets](../Image%20Assets/), but have the following modifications:

- All lowercase
- No file extension (e.g. `.png`/`.jpg`)
- spaces are replaced with underscores.

🟢 **E.g.** [Image Assets/Char Kirara.png](../Image%20Assets/Characters/Char%20Kirara.png) has the image asset key `char_kirara`. 

These image assets and asset names have to be manually updated by the discord app owner: Currently, [@euwbah](https://github.com/euwbah).

-----

Here are the formats for each `.csv` file:

## [Characters](characters.csv)

```csv
lowercase search phrase, character image asset, character display name
kaveh,                   char_kaveh,            Kaveh
```

- Contains playable characters.
- The `search phrase` should match character names in the character selection display (on the right), not the full name.
- Character image assets are located in [Image Assets/Characters](../Image%20Assets/Characters/).

## [Domains/Trounce weekly bosses](domains.csv)

```csv
lowercase search phrase, domain name,                        domain type, location image asset
obsession,               Tower of Abject Pride | Obsession,  forgery,     domain_forgery_sumeru
```

- Contains names of Trounce, Blessing, Mastery, Forgery and One-Time domains.
  - Format for `domain name` should be `<domain location name> | <domain challenge name>`. Note that each domain has a location name, but within each domain there are individual challenges with different names.
  - **The `search phrase` should only contain the domain challenge name**, not the domain location name.
- If the domain challenge name is very long (i.e., appearing over multiple lines in the right info panel in the domain start/selection screen), the `search phrase` should be the front part of the domain name.
- `domain type` should be exactly written as either one of:
  - `mastery` --- Domain of Mastery
  - `forgery` --- Domain of Forgery
  - `blessing` --- Domain of Blessing
  - `trounce` --- Trounce Domain
  - `one-time` --- One-Time Domains (exploration domains or story quest domains)
  - `limited` --- Limited time event domains
- Domain image assets are located in [Image Assets/Domains](../Image%20Assets/Domains/).

> ⚠️ This list is incomplete. One-time and limited-time event domains are missing.
>
> 🟠 The `domain type` values must match the strings in the function `DomainType.from_str()`
> 
> 🟠 Weekly bosses in Trounce Domains are listed here as well.

## [Locations/Points of interest](locations.csv)

```csv
lowercase search phrase, location name, subarea name, country name, location emblem image asset
wuwang hill,             Wuwang Hill,   Bishui Plain, Liyue,        emblem_liyue
```

- Contains the following locations/`search phrase`:
  - names of locations/points of interests that pop up in both the **large location pop-up text while travelling between places**
    - e.g. instead of `starfell valley, mondstadt`, just use `starfell valley` as the search phrase
  - text that shows up in active gameplay which uniquely signify being at a particular location
    - e.g. `prince` and `cats tail` signify being in **The Cat's Tail**
    - e.g. `tubby` and `chubby` signify being in the **Serenitea Pot**
- Location emblem image assets are in [Image Assets/Location Emblem](../Image%20Assets/Location%20Emblem/).

This list includes locations, subareas, points of interest, and search text pertaining to specific areas like `chubby` or `tubby` for detecting teapot, `prince` and `cat's tail` for detecting cat's tail, etc...

> ⚠️ This list is incomplete. (Missing certain points of interest that are not considered subareas (e.g. Treasures Street)).
>
> 🟢 The [Genshin wiki locations page](https://genshin-impact.fandom.com/wiki/Locations) is a good reference for location/point-of-interest names sorted in alphabetical order, but may not be exhaustive nor precise.
> 
> 🟠 Some location emblems/entries are for limited-time events, which can be deleted once no longer used.
>
> 🟠 To improve detection ability, the location search phrase should be as shortest unique search phrase possible.
> For long location names, use the middle part of the location name as the search phrase.

## [World bosses](bosses.csv)

```csv
lowercase search phrase, boss name,        boss image asset
aeonblight drake,        Aeonblight Drake, boss_aeonblight_drake
```

- `search phrase` should match the upper boss name
  - E.g. for the [**Anemo Hypostasis**](https://genshin-impact.fandom.com/wiki/Anemo_Hypostasis), don't match `beth`, use `anemo hypostasis` instead.

> 🟠 NOTE: This list does not include boss names of bosses in Trounce Domains, those go under domains.
>    Only add world bosses into this list.
>
> 🟠 [**Andrius**](https://genshin-impact.fandom.com/wiki/Wolf_of_the_North_Challenge), along with other similar bosses, is considered a world boss, since there's no domain entrance to go through to fight the boss.
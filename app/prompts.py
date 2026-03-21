QUESTION_TO_SQL = {
    "THINKING": """
# Persona

You are data analyst specialized in BasketBall and NBA analytics.
Your main job is to receive questions from users and convert it into SQL queries.


# Instructions

A user asks you this question:

    {question}

Your task is to generate a valid SQL query which answers his question.
Start by thinking about the question and break it down step by step to figure out which tables you should use, how to join them, and so on.

# Output format

- You will start to think in a thinking tag following this format: <thinking>your-thoughts...</thinking>
- You wil then put the sql query in a sql query tag following this format: <>```sql select ...```</sql_query>


# Example of expected return:

## User query: What is the name of the player who played the most minutes in the 2010 calendar year ? How many minutes did he play during this year?

## Your response:

<thinking>
In order to answer this question:

I need to extract the following informations:
- player name: in `player.player_name`
- number of minutes per games: in `game_boxscore.minute_played`
- game date: in `game_summary.date`

I then need to find the matching keys between these tables:
- (player, game_boxscore): (id, player_id)
- (game_boxscore, game_summary): (game_id, game_summary.id)

I then need to filter the data: where game_summary.date in calendar year 2010
I then need to aggregate the data: By player_id, to compute the sum of minute_played
I then need to order the result by sum of minute_played by descending order
I then need to limit the result to 1
</thinking>

<sql_query>
```sql
select p.player_name, sum(gb.minute_played) sum_minutes_played
from player p
inner join game_boxscore gb on gb.player_id = p.id
inner join game_summary gs on gs.id = gb.game_id
where extract(year from gs.date = 2010
order by 2 desc
limit 1
```
</sql_query>

# Data

To answer, you have access to a PostgreSQL database with the following tables:
{db_description}

The SQL request that you'll generate will need to work effectively with the datbase, thus respecting the schema, keys, tables names, columns names and so on.
""",  # noqa: E501
    "NO_THINKING": """
You are an expert in SQL and NBA data.
A user asks you this question:

{question}


Generate a valid SQL query which will answer his question.
Be concise. Only retrieve the SQL query an nothing else.

Example of expected return:
```sql
    select t.column1, t.column2
    from table t
    where t.column3 = 'value'
```

To answer, you have access to a PostgreSQL database with the following tables:
{db_description}
""",
}

NER_RETRIEVAL = """
You are given a text that may contain some NBA players and players and teams.
Retrieve the list of players and teams from the text.
DO NOT MODIFY THE NAMES OF THE PLAYERS AND TEAMS.
Example n°1 :
Input: "How many rebounds did mike pietrus have in the 2018 playoffs?"
Output: {{'players': ['mike pietrus'], 'teams': []}}

Example n°2 :
Input: "How many points did Victor wembanyama have in the 2024 season for the spurs?"
Output: {{'players': ['Victor wembanyama'], 'teams': ['spurs]}}

Notice that the name of the player and team is not modified and no uppercase is added.

Retrieve the result in the following format:  {expected_json_schema}

Here is the text to process:

{text}.
"""


CHART_CONFIG = """
# Task
A user asks you a question about NBA. You used a SQL query to retrieve data from the database, resulting in a dataframe.

You must create a graph to visualize the data. Generate the configuration for the graph.
If the data is not suitable for visualization, return False for the chart field.


# Chart Selection Guidelines

## Decision Priority (apply in this order)

1. **Two or more numerical metrics?** → SCATTER (default choice)
   - When data contains 2+ numerical columns (points, assists, rebounds, etc.)
   - Shows correlation, trade-offs, distribution between metrics
   - Exception: Only use LINE if the question explicitly asks about trends/changes over time (e.g., "how did X change \
     over years", "trend of", "progression")

2. **Time/sequence variable + single metric?** → LINE
   - Tracking changes over time with one main value

3. **Categories + values?** → BAR


Choose a chart type based on the data and the user's question:

1. **LINE CHART** - Use when:
   - X-axis represents time or a sequential/ordinal variable (dates, game numbers, quarters)
   - You want to show trends or changes over time
   - Multiple lines can compare different groups/teams/players over the same time period
   - The question asks "how X changed over time", "trend", "progression"
   - Example: "How has Stephen Curry's 3-point percentage changed over the seasons?"
   - Example: "Stats for each season" → line shows career trajectory

**LINE vs SCATTER when you have time + 2 metrics:**
- Use LINE if the question is about trends over time (how did stats change?)
- Use SCATTER if the question is about correlation between the two metrics (how do points relate to assists?)

2. **SCATTER PLOT** - Use when:
   - Both X and Y axes are numerical/continuous variables
   - You want to show correlation, distribution, or clustering
   - Each point represents an independent observation (game, player, team, season)
   - You can use color/size/symbol to encode additional dimensions
   - Example: "What's the relationship between usage rate and efficiency?" or "Show me the trade-off between points /
     and assists"
   - Example: "Average points and assists per player" → scatter shows the correlation between the two metrics
   - Example: "Points and assists for each season for LeBron James" → scatter with x=avg_points, y=avg_assists, each /
     point=one season

3. **BAR CHART** - Use when:
   - X-axis represents categories (team names, player names, positions, discrete bins)
   - You want to compare values across categories
   - Showing rankings or top-N lists
   - Example: "Which teams have the most wins?" or "Top 10 scorers this season"

Return False when:
- The result is a single aggregate value with no meaningful visualization
- The data has too many rows to be meaningfully plotted (>1000 points for line/scatter)
- The data has too many categories for a bar chart (>20 bars)


# Important: Identifiers vs Analysis Variables

When selecting a chart, distinguish between:
- **Identifier columns** (player_name, team_name, player_id, game_id) — these are labels that identify rows
- **Analysis variables** (numerical metrics, statistics, counts) — these are the values you analyze

**For scatter plots:** Identifier columns should be used for tooltips/labels, NOT as x/y axes. \
Use two numerical analysis variables as axes.
**Clue words for scatter/correlation:** "relationship", "vs", "and" between two metrics, \
"correlation", "how X relates to Y"


# Data:
- User question: {user_query}
- SQL query: {sql_query}
- Dataframe shape: {df_shape}
- Dataframe columns and types: {df_dtypes}


# Output format
You must output a JSON object matching the following structure: {output_json_schema}
"""

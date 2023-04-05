import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)

# get unique dictionary of team to franchise IDs to merge into following dataframes
teams = pd.read_csv('LahmanData2023\core\Teams.csv')

franch_IDs = []
for team in teams['teamID'].unique():
    franch_IDs.append(teams[teams['teamID'] == team]['franchID'].iloc(0)[0])

franchises = pd.DataFrame(
    list(zip(teams['teamID'].unique(), franch_IDs)), columns=['teamID', 'franchID'])

# case sensitive fix for some differences in formatting :(
warbat = pd.read_csv('war_daily_bat.txt')
warbat = warbat[warbat['year_ID'] > 1984]
for a in warbat['team_ID'].unique():
    if not a in list(franchises['teamID']):
        if a in list(franchises['franchID']):
            franchises.loc[len(franchises.index)] = [a, a]
        else:
            franchises.loc[len(franchises.index)] = ['TBR', 'TBD']


salary = pd.read_csv('LahmanData2023\contrib\Salaries.csv').merge(
    franchises, on='teamID')
war_batting = pd.read_csv('war_daily_bat.txt').merge(
    franchises, left_on='team_ID', right_on='teamID')
war_pitching = pd.read_csv('war_daily_pitch.txt').merge(
    franchises, left_on='team_ID', right_on='teamID')


player_stats_full = war_batting.merge(war_pitching, how='left', on=[
                                      'player_ID', 'year_ID', 'franchID'])

# creating a column of what number season the player is in. 1 for their first season, and so on.
season = []
first_season = {}

for i in range(len(player_stats_full)):
    ID = player_stats_full['player_ID'][i]
    if ID in first_season.keys():
        s = player_stats_full['year_ID'][i] - first_season[ID] + 1
    else:
        first_year = min(
            player_stats_full[player_stats_full['player_ID'] == ID]['year_ID'])
        first_season[ID] = first_year
        s = player_stats_full['year_ID'][i] - first_year + 1
    season.append(s)

player_stats_full['season'] = season

player_stats_full = player_stats_full[player_stats_full['year_ID'] > 1984]
player_stats_full = player_stats_full[player_stats_full['year_ID'] != 1994]
player_stats_full = player_stats_full[player_stats_full['year_ID'] < 2020]
player_stats_full.reset_index(inplace=True)

# summing pitching and batting WAR to create WAR_total column
WAR_total = []
for i in range(len(player_stats_full)):
    x = player_stats_full['WAR_x'][i]
    y = player_stats_full['WAR_y'][i]

    x_true = pd.isna(player_stats_full['WAR_x'][i])
    y_true = pd.isna(player_stats_full['WAR_y'][i])

    if not(x_true or y_true):
        war = x + y
    elif x_true and not y_true:
        war = y
    elif y_true and not x_true:
        war = x
    else:
        war = np.NaN

    WAR_total.append(war)

player_stats_full['WAR_total'] = WAR_total


team_salary_bref_batting = war_batting.groupby(['year_ID', 'franchID']).agg(
    sum).reset_index().loc[:, ['year_ID', 'franchID', 'salary', 'WAR']]
team_stats_full = team_salary_bref_batting.merge(
    teams, left_on=['year_ID', 'franchID'], right_on=['yearID', 'franchID'])

playoffs = []
for i in range(len(team_stats_full)):
    if team_stats_full['WCWin'][i] == 'Y' or team_stats_full['DivWin'][i] == 'Y':
        playoffs.append('Y')
    else:
        playoffs.append('N')

team_stats_full['playoffs'] = playoffs

# removing years with incomplete salary statistics, and 1994 which was an incomplete season due to MLB strike
team_stats_full = team_stats_full[team_stats_full['yearID'] > 1984]
team_stats_full = team_stats_full[team_stats_full['yearID'] != 1994]
team_stats_full = team_stats_full[team_stats_full['yearID'] < 2020]
team_stats_full.reset_index(inplace=True)

# adding a column of salary/yearAverageSalary for each team
yearly_average = team_stats_full.groupby('yearID').agg(
    ['mean', np.std]).reset_index().loc[:, ['yearID', 'salary']]
pct_yearly_average = []
for i in range(len(team_stats_full)):
    pct_yearly_average.append(team_stats_full['salary'][i]/float(
        yearly_average[yearly_average['yearID'] == team_stats_full['yearID'][i]]['salary']['mean']))

team_stats_full['salary_plus'] = pct_yearly_average


player_stats_full['WAR_per_salary'] = player_stats_full['WAR_total'] / \
    player_stats_full['salary']


# intended global variables:
teams = team_stats_full
players = player_stats_full
teams_average = yearly_average

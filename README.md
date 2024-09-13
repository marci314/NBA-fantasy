# NBA-fantasy-app

## Description

The application is designed for playing NBA Fantasy Leagues. Upon the first use, the user registers and selects a team of players. These players earn points based on their real-life NBA performance. More points, assists, blocks, etc., mean a better score. If a player performs poorly, they can even receive negative points.

The goal of each user is to collect as many points as possible.

Statistical data on games and players are obtained from websites [basketball-reference.com](basketball-reference.com) and [NatStat.com](https://natstat.com/).

### ER diagram

Link to the [ER](https://github.com/marci314/NBA-fantasy-app/blob/main/Presentation/static/Images/opber3.png) diagrama.

### Database Structure

List of tables in our database:

- **user** (user_id, username, password, last_login)
- **fantasy_team** (f_team_id, points, owner, team_name)
- **player** (player_id, name, position, height, birthdate)
- **coach** (coach_id, name, birthdate)
- **fantasy_team_coach** (f_team_id, coach_id)
- **team** (team_id, team_name)
- **game** (game_id, home_team, away_team, home_team_points, away_team_points, date)
- **game_data** (player_id, game_id, shooting_percentage, steals, blocks, turnovers, rebounds, assists, minutes_played, points, result)
- **fantasy_team_players** (f_team_id, player_id)
- **player_points** (player_id, game_id, points)
- **team_players** (player_id, team_id)
- **team_coaches** (coach_id, team_id)

## Application Usage Instructions

1. **Registration:** After launching the application, register with a username, password, and name your fantasy team.
2. **Login:** Log in with your username and password.
3. **Read the rules:** Go to the "Rules" tab and read the basic rules and how the game works.
4. **Select players and a coach:** Each user can select up to 5 players and one coach for their team. You can preview other users' teams and the game schedule to help make your decision.
5. **Select a time window:** In the "Simulate Games" tab, set the time window in which you want to simulate the games.
6. **Review results:** After the games are played, check the "View Standings" tab to see your fantasy team's ranking.

#### Web Access

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/marci314/NBA-fantasy-app.git/main?urlpath=proxy/8081/)




















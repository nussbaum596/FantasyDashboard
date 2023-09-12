import pandas as pd
import espnfantasyfootball as espn
import requests
import numpy as np
import plotly.express as px
import streamlit as st


st.title('For Monetary Reward 2023 Stats Dashboard')

espn_s2 = 'AEBQhAI6VxLL4wP%2F7EO8xbAAvbjfTnboXPJeAIbboYWV5m1Ks0aulxJ3%2BWryhwIn6u2wvYsKOI0A6vTmuvnuxLYOqtIIteThgzHvg3MybuCnrr%2FavTzsHbWGNp%2FizmP%2Fu3%2BpWEsZQnlFMnzx0LFljQZdCsh5Fe5mrcnU1HBB7tbjG%2FxT9w8NoO0IanXGx49%2FM7dzTcL9rHGGtN0Km67vBjQogfBpC9GgZuNrw2dy817BiWEx6nIq7I7RZMrPURz%2BuyjsK12Kark7dqqmCXLuIPePyh6iuSWnlLqEPdQFl1%2FT8wrLGQ9kjYM6vsOlCQ2xgGOMQG0hxqzleu4%2B%2FnUapO%2BE'
swid = '{E447B594-6872-47C9-87B5-946872B7C9F9}'

@st.cache_data
def get_data():
    league = espn.FantasyLeague(league_id = 657778, 
                                year = 2023, 
                                espn_s2 = espn_s2, 
                                swid= swid)
     
    #%%Data by team roster
    data = league.get_league_data()
    data['FullName'] = data['FullName'].fillna('Brandon Nussbaum')
    
    #%%Data by Matchup
    data2 = league.get_matchup_data()
    data2 = data2.drop_duplicates()
    data2 = data2[data2['Score1'] > 0]
    
    #%%Data by Player
    custom_headers = {
    'Connection': 'keep-alive',
     'Accept': 'application/json, text/plain, */*',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
      'x-fantasy-filter': '{"filterActive":null}',
      'x-fantasy-platform': 'kona-PROD-1dc40132dc2070ef47881dc95b633e62cebc9913',
      'x-fantasy-source': 'kona'
     }
     
    url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2023/players?scoringPeriodId=0&view=players_wl"
    r = requests.get(url, 
                      cookies = {"swid": swid, "espn_s2": espn_s2}, 
                      headers=custom_headers)
    player_data = r.json()
    data3 = pd.DataFrame(player_data)
    data3 = data3[data3['defaultPositionId'].isin([1,2,3,4,5,16])][['fullName', 'defaultPositionId']]
    data3.columns = ['PlayerName', 'ActualPosition']
    data3['ActualPosition'] = data3['ActualPosition'].map({1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5:'K', 16:'D/ST'})
     
    data4 = data.merge(data3, how='left', on='PlayerName')
    data4 = data4.drop_duplicates()
    data4 = data4[data4['Week'] <=14]
    data4['FullName'] = data4['FullName'].str.title().replace(r'\s+', ' ', regex=True)
    data4 = data4.rename(columns = {'FullName': 'Name'})
    
    #Replacing Team names with Actual names for matchup data
    team_names = data4[['Name', 'TeamName']].drop_duplicates()
    data2 = data2.merge(team_names, how='left', left_on = 'Name1', right_on = 'TeamName')
    data2 = data2.drop(['Name1', 'TeamName'], axis=1)
    data2 = data2.rename(columns = {'Name': 'Name1'})
    data2 = data2.merge(team_names, how='left', left_on = 'Name2', right_on = 'TeamName')
    data2 = data2.drop(['Name2', 'TeamName'], axis=1)
    data2 = data2.rename(columns = {'Name': 'Name2'})

    ##Creating New Dataset with PF/PA
    pf1 = data2[['Week', 'Name1', 'Score1']]
    pf1.columns = ['Week', 'Name', 'PF']
    pf2 = data2[['Week', 'Name2', 'Score2']]
    pf2.columns = ['Week', 'Name', 'PF']
    pf = pd.concat([pf1, pf2])

    pa1 = data2[['Week', 'Name1', 'Score2']]
    pa1.columns = ['Week', 'Name', 'PA']
    pa2 = data2[['Week', 'Name2', 'Score1']]
    pa2.columns = ['Week', 'Name', 'PA']
    pa = pd.concat([pa1, pa2])

    #Merging Everything Together in One Giant Dataset
    data_all = data4.merge(pf, how='left', on = ['Week', 'Name'])
    data_all = data_all.merge(pa, how='left', on = ['Week', 'Name'])
    data_all = data_all.merge(pf, how='left', left_on = ['Week', 'PA'], right_on = ['Week', 'PF'])
    data_all = data_all.drop(['PF_y'], axis=1)
    data_all = data_all.rename(columns = {'Name_x': 'Name', 'PF_x': 'PF', 'Name_y': 'Opponent'})
    data_all = data_all[data_all['PF'] > 0]
    return data_all
 
data_all = get_data()

st.write("""
         This dashboard is for keeping track of interesting stats throughout the fantasy season including PF leaders (overall and by position),
         coach ratings, and power rankings. You can filter the stats by week ranges and teams, and these stats will be updated weekly. Have fun!
         """)

#%%Adding Options and Filters

#Options
options = st.sidebar.radio('Pages', options = ['PF Summary', 'Power Rankings'])

#Week
#week_slider = st.sidebar.slider("Select Weeks",
                        #1, data_all[data_all['PF'] > 0]['Week'].max(), (1, data_all[data_all['PF'] > 0]['Week'].max()))
                                               
if options == 'PF Summary':

    
    ##Team Name
    name_filter = st.sidebar.multiselect(
        "Select Teams:",
        options = data_all['Name'].unique(),
        default = list(data_all['Name'].unique()))
    
    data_all = data_all.loc[(data_all['Name'].isin(name_filter))]
    #data_all = data_all.loc[(data_all['Name'].isin(name_filter)) & (data_all['Week'].between(week_slider[0], week_slider[1]))]
    
    #%%Coach Rankings
    
    ##Total PF (All Positions) By Team
    total_pf = data_all[data_all['PlayerRosterSlot'] != 'Bench'].groupby('Name')['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
    total_pf.columns = ['Name', 'PF']
    ##Total PF (By Position) By Team
    
    def pos_pf(pos):
        df = data_all[data_all['PlayerRosterSlot'] == pos].groupby('Name')['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
        df.columns = ['Name', pos + ' Actual']
        return df
    
    qb_pf = pos_pf('QB')
    rb_pf = pos_pf('RB')
    wr_pf = pos_pf('WR')
    flex_pf = pos_pf('FLEX')
    te_pf = pos_pf('TE')
    k_pf = pos_pf('K')
    dst_pf = pos_pf('D/ST')
    
    ##Total Possible PF (By Position) By Team
    def pos_maxpf(pos):
        df = data_all[data_all['ActualPosition'] == pos].groupby(['Week', 'Name'])['PlayerScoreActual'].max().reset_index().groupby('Name')['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
        df.columns = ['Name', pos + ' Max']
        return df
    
    qb_maxpf = pos_maxpf('QB')
    te_maxpf = pos_maxpf('TE')
    k_maxpf = pos_maxpf('K')
    dst_maxpf = pos_maxpf('D/ST')
    
    ##Have to calculate Best RB and best WR based on the Top 2 of each on the roster.
    ##To find best FLEX, need to remove top 2 RBs, and Top 2 WRs, and find highest RB/WR/TE
    flex_max = data_all[data_all['ActualPosition'].isin(['RB','WR', 'TE'])]
    flex_max = flex_max.sort_values(['Week', 'Name', 'ActualPosition', 'PlayerScoreActual'], ascending = [True, True, True, False])
    flex_max['Rank'] = flex_max.groupby(['Week', 'Name', 'ActualPosition']).cumcount() + 1
    flex_max['VirtSlot'] = np.where(((flex_max['ActualPosition'] == 'RB') & (flex_max['Rank'] <= 2)), 'RB', np.where(
                                    ((flex_max['ActualPosition'] == 'WR') & (flex_max['Rank'] <= 2)), 'WR', np.where(   
                                    ((flex_max['ActualPosition'] == 'TE') & (flex_max['Rank'] == 1)), 'TE', np.nan)))
    #flex_max = flex_max.drop('Rank', axis=1)
    
    flex_max2 = flex_max[((flex_max['ActualPosition'] == 'RB') & (flex_max['Rank'] > 2)) |
                        ((flex_max['ActualPosition'] == 'WR') & (flex_max['Rank'] > 2)) |
                        ((flex_max['ActualPosition'] == 'TE') & (flex_max['Rank'] > 1))]
    flex_max2 = flex_max2.sort_values(['Week', 'Name', 'PlayerScoreActual'], ascending = [True, True, False])
    flex_max2['FlexRank'] = flex_max2.groupby(['Week', 'Name']).cumcount() + 1
    flex_max2['VirtSlot'] = np.where(flex_max2['FlexRank'] == 1, 'FLEX', 'Bench')
    flex_max2 = flex_max2.drop(['Rank', 'FlexRank'], axis=1)
    
    flex_max3 = pd.concat([flex_max, flex_max2])
    flex_max3 = flex_max3[flex_max3['VirtSlot'].isin(['RB', 'WR', 'TE', 'FLEX', 'Bench'])]
    
    def pos_maxpf2(pos):
        df = flex_max3[flex_max3['VirtSlot'] == pos].groupby(['Name'])['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
        df.columns = ['Name', pos + ' Max']
        return df
    
    rb_maxpf = pos_maxpf2('RB')
    wr_maxpf = pos_maxpf2('WR')
    flex_maxpf = pos_maxpf2('FLEX')
    
    ##Coach Ranking: Combining Everything into 1 Dataframe
    dfs = [df.set_index(['Name']) for df in [qb_pf, qb_maxpf, rb_pf, rb_maxpf, wr_pf, wr_maxpf,
                                                 te_pf, te_maxpf, flex_pf, flex_maxpf, dst_pf, dst_maxpf, k_pf, k_maxpf]]
    coach = pd.concat(dfs, axis=1).reset_index()
    coach['Total Actual PF'] = coach.filter(regex = 'Actual').sum(axis=1)
    coach['Total Possible PF'] = coach.filter(regex = 'Max').sum(axis=1)
    coach['Coach Rating'] = round(100*(coach['Total Actual PF'] / coach['Total Possible PF']),2)
    coach['CR Rank'] = coach['Coach Rating'].rank(ascending=False)
    
    #%%PF/PA Bar Chart
    st.header('Total PF/PA')
    

    pf_chart = data_all[['Name', 'PF', 'PA']]
    pf_chart = pf_chart.drop_duplicates()
    pf_chart = pd.melt(pf_chart, id_vars = ['Name'], var_name='Points Category', value_name = 'Points') 
    pf_chart = pf_chart.groupby(['Name', 'Points Category'])['Points'].agg('sum').reset_index()
    pf_chart['Points Category'] = pd.Categorical(pf_chart['Points Category'], categories = ['PF', 'PA'], ordered=True)
    pf_chart = pf_chart.sort_values(['Name', 'Points Category'])
    pf_chart['Sort'] = pf_chart[pf_chart['Points Category'] == 'PF']['Points']
    pf_chart = pf_chart.sort_values('Sort', ascending=False)
    pf_chart = pf_chart.drop(['Sort'], axis=1)
    fig = px.bar(pf_chart, x = 'Name', y = 'Points', color = 'Points Category', barmode='group', color_discrete_sequence=px.colors.qualitative.G10)
    st.plotly_chart(fig, use_container_width = True)

    #%%Actual vs Expected Wins
    st.header('Actual vs Expected Wins')
    
    st.write("""
             Expected Wins are calculated based on Weekly PF compared to all other weekly scores. Teams above the line 
             are considered "lucky" while teams below the line are considered "unlucky".
             """)
    
    records = data_all[['Week', 'Name', 'PF', 'Opponent', 'PA']]
    records = records.drop_duplicates()
    records['Winner'] = np.where(records['PF'] > records['PA'], records['Name'], np.where(
                                 records['PA'] > records['PF'], records['Opponent'], np.nan))
    wins = records['Winner'].value_counts().reset_index()
    wins.columns = ['Name', 'Actual Wins']
    for team in data_all['Name'].unique():
            if team not in wins['Name'].unique():
                wins = pd.concat([wins, pd.DataFrame({'Name': [team], 'Actual Wins': [0]})])
    wins['Actual Wins'] = wins['Actual Wins']/2
    
    scores = data_all[['Week', 'Name', 'PF', 'PA']]
    scores = scores.drop_duplicates()
    
    scores['PF Rank'] = scores.groupby('Week')['PF'].rank(ascending=False)
    pf_exp = round((((scores['Week'].max() - scores['Week'].min() + 1)*data_all['Name'].nunique()) - scores.groupby('Name')['PF Rank'].sum())/(data_all['Name'].nunique()-1),2).reset_index()
    pf_exp.columns = ['Name', 'Expected Wins']
    
    wins_actexp = wins.merge(pf_exp, how='left', on='Name')
    customdata = np.stack((wins_actexp['Name'], wins_actexp['Actual Wins'], wins_actexp['Expected Wins']), axis=-1)
    
    fig = px.scatter(wins_actexp, x='Expected Wins', y='Actual Wins', hover_name = 'Name')
    fig.update_traces(customdata=customdata, hovertemplate="Name: %{customdata[0]}<br>Actual Wins: %{customdata[1]}<br>Expected Wins: %{customdata[2]}")
    fig.add_shape(type='line',
            x0=0,
            y0=0,
            x1=scores['Week'].max() - scores['Week'].min() + 1,
            y1=scores['Week'].max() - scores['Week'].min() + 1,
            line=dict(color='Black'),
            xref='x',
            yref='y'
)
    st.plotly_chart(fig, use_container_width = True)
    

    #%%Positional Leaders
    st.header('Positional Leaders')


    def pos_lead(pos):
        df = data_all[data_all['PlayerRosterSlot'] == pos][['Name', 'PlayerScoreActual']]
        df = df.groupby('Name')['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
        df['Rank'] = np.arange(df.shape[0]) + 1
        df.columns = ['Name', 'PF', 'Rank']
        df = df[['Rank', 'Name', 'PF']]
        st.markdown("<h4 style='text-align: center;'>" + pos + "</h4>", unsafe_allow_html=True)
        st.dataframe(df, hide_index=True, use_container_width = True)

    c1, c2, c3 = st.columns(3)
    
    with c1:
        qb_table = pos_lead('QB')
        te_table = pos_lead('TE')
        
    with c2:
        rb_table = pos_lead('RB')
        flex_table = pos_lead('FLEX')
        k_table = pos_lead('K')
    with c3:
        wr_table = pos_lead('WR')
        dst_table = pos_lead('D/ST')
        
    #%%Coach Rating
    st.header('Coach Rating')
    st.write("""
             This rating compares your actual lineup to your best possible lineup. For example, if your coach rating is a 95,
             then your lineup scored 95 points when 100 points were possible from your best lineup. The best possible lineup includes your best QB,
             2 best RBs, 2 best WRs, best TE, next best RB/WR/TE as your FLEX, your best D/ST, and your best K.
             """)
    coach_table = coach[['Name', 'Coach Rating']]
    coach_table = coach_table.sort_values('Coach Rating', ascending=False)
    st.dataframe(coach_table, hide_index=True, use_container_width = True)


elif options == 'Power Rankings':
    
    data_all2 = data_all.copy()
    #data_all2 = data_all.loc[data_all['Week'].between(week_slider[0], week_slider[1])]
#%%Power Rankings

##Wins/Losses

##Expected Wins/Losses
    def power_rk(df, wk):
        df = df.copy()
        records = df[df['Week'] <= wk]
        records = records[['Week', 'Name', 'PF', 'Opponent', 'PA']]
        records = records.drop_duplicates()
        records['Winner'] = np.where(records['PF'] > records['PA'], records['Name'], np.where(
                                     records['PA'] > records['PF'], records['Opponent'], np.nan))
        records['Loser'] = np.where(records['PA'] > records['PF'], records['Name'], np.where(
                                     records['PF'] > records['PA'], records['Opponent'], np.nan))
        wins = records['Winner'].value_counts().reset_index()
        losses = records['Loser'].value_counts().reset_index()
        for team in df['Name'].unique():
            if team not in wins['Winner'].unique():
                wins = pd.concat([wins, pd.DataFrame({'Winner': [team], 'count': [0]})])
            if team not in losses['Loser'].unique():
                losses = pd.concat([losses, pd.DataFrame({'Loser': [team], 'count': [0]})])
        wins.columns = ['index', 'Winner']
        losses.columns = ['index', 'Loser']
        wins_losses = wins.merge(losses, how='left', on='index')
        wins_losses.columns = ['Name', 'Wins', 'Losses']
        wins_losses['Wins'] = wins_losses['Wins']/2
        wins_losses['Losses'] = wins_losses['Losses']/2
        
        scores = df[df['Week'] <= wk]
        scores = scores[['Week', 'Name', 'PF', 'PA']]
        scores = scores.drop_duplicates()
        
        scores['PF Rank'] = scores.groupby('Week')['PF'].rank(ascending=False)
        scores['PA Rank'] = scores.groupby('Week')['PA'].rank(ascending=False)
        pf_exp = round(((wk*data_all['Name'].nunique()) - scores.groupby('Name')['PF Rank'].sum())/(data_all['Name'].nunique() - 1),2).reset_index()
        pf_exp.columns = ['Name', 'PF Exp Wins']
        pa_exp = round(wk - ((wk*data_all['Name'].nunique()) - scores.groupby('Name')['PA Rank'].sum())/(data_all['Name'].nunique() - 1),2).reset_index()
        pa_exp.columns = ['Name', 'PA Exp Wins']
        
        total_pf2 = df[(df['PlayerRosterSlot'] != 'Bench') & (df['Week'] <= wk)].groupby('Name')['PlayerScoreActual'].agg('sum').reset_index().sort_values('PlayerScoreActual', ascending=False)
        total_pf2.columns = ['Name', 'PF']
        
        dfs = [df.set_index(['Name']) for df in [wins_losses, total_pf2, pf_exp, pa_exp]]
        power = pd.concat(dfs, axis=1).reset_index()
        power['Avg Exp Wins'] = power[['PF Exp Wins', 'PA Exp Wins']].mean(axis=1)
        power['AEW Rank'] = power['Avg Exp Wins'].rank(ascending=False)
        power['Avg Win Diff'] = power['Wins'] - power['Avg Exp Wins']
        power['Wins Above PF'] = power['Wins'] - power['PF Exp Wins']
        power['Wins Above PA'] = power['Wins'] - power['PA Exp Wins']
        power['SoS'] = power['PA Exp Wins'].rank(ascending=False)
        power['SoR'] = power['Avg Win Diff'].rank(ascending=False)
        power['Power PF'] = round(-(power['PF'] - power['PF'].min()) / (power['PF'].max() - power['PF'].min())*(data_all['Name'].nunique()-1) + data_all['Name'].nunique(),2)
        power['Power Exp Wins'] = round(-(power['PF Exp Wins'] - power['PF Exp Wins'].min()) / (power['PF Exp Wins'].max() - power['PF Exp Wins'].min())*(data_all['Name'].nunique()-1) + data_all['Name'].nunique(),2)
        power['Power Wins Above PA'] = round(-(power['Wins Above PA'] - power['Wins Above PA'].min()) / (power['Wins Above PA'].max() - power['Wins Above PA'].min())*(data_all['Name'].nunique()-1) + data_all['Name'].nunique(),2)
        power['Power Index'] = 0.3*power['Power PF'] + 0.4*power['Power Exp Wins'] + 0.3*power['Power Wins Above PA']
        power['Power Rank'] = power['Power Index'].rank()
        return power
    
    power = power_rk(data_all, data_all['Week'].max())
    #%%Power Indices

    power_indices = pd.DataFrame()
    for i in range (1, data_all2['Week'].max() + 1):
        if i <= 3:
            df = data_all2[data_all2['Week'] <= i]
            df2 = power_rk(df, i)
            df2['Week'] = i
            df2 = df2[['Week', 'Name', 'Power Index']]
        elif i > 3:
            df = data_all2[data_all2['Week'].between(i-2, i)]
            df2 = power_rk(df, i)
            df2['Week'] = i
            df2 = df2[['Week', 'Name', 'Power Index']]
        power_indices = pd.concat([power_indices, df2])
        
    #%%Power Index Table
    st.header('Power Indices')
    st.write("""
             The power index is the weighted average of various metrics and is intended to show true ranking of team performance. It takes
             into consideration your total PF, expected wins based on weekly PF compared to all other weekly scores, and expected wins based on weekly
             Opponent PF compared to all other weekly scores. A lower index indicates better team performance.
             
             For Weeks 1-3, the indices are calculated based on data from the start of the season to each respective week. For Weeks 4-onward, the indices are calculated 
             only using data from the 3 weeks prior (i.e Week 9 uses Weeks 7-9 data and Week 13 uses Weeks 11-13 data etc). This was done to represent how our teams have performed 
             over the course of the season. 
             
             Double click on a name to see that person's individual line. From there you can click on other names to compare lines. 
             """)
    fig = px.line(power_indices, x='Week', y='Power Index', color='Name', range_y = [data_all['Name'].nunique(), 1], markers=True, color_discrete_sequence=px.colors.qualitative.Dark24)
    fig.update_layout(xaxis={"dtick":1})
    fig.update_layout(yaxis={"dtick":1})
    st.plotly_chart(fig, use_container_width = True)
    
    #%%Power Ranking
    st.header('Power Rankings')
    st.write("""
             The power rankings are simply a ranking of the power indices from lowest to highest calculated based on the given week range.
             """)
    power_table = power[['Power Rank', 'Name']]
    power_table = power_table.sort_values('Power Rank')
    st.dataframe(power_table, hide_index=True, use_container_width = True)